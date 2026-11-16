from nonoha_core.nodes.time_nodes import (
    ClockNode,
    SystemTimeNode,
    TickClockNode,
    TimeStringifyNode,
)

import numpy as np
import pytest
import time
from datetime import datetime


def test_system_time_node():
    node = SystemTimeNode("test")

    input_dispatch = node.inputs["dispatch"]
    output_time = node.outputs["time"]

    input_dispatch.dispatch([np.arange(5)])

    assert output_time.current_values is not None
    result = output_time.current_values[0]
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float64
    assert result.shape == (5,)


def test_time_stringify_node():
    node = TimeStringifyNode("test")

    input_time = node.inputs["time"]
    output_string = node.outputs["string"]

    node.set_properties({"format_str": "%Y-%m-%d %H:%M:%S.%f"})

    input_time.dispatch(
        [
            np.array(
                [
                    1752927027,
                    1752927028,
                    1752927029,
                ],
                dtype=np.float64,
            )
        ]
    )

    assert output_string.current_values is not None
    result = output_string.current_values[0]
    # print(result)

    assert isinstance(result, np.ndarray)
    assert result.shape == (3,)


# ───────────────────────────────────────────────────────────────
# ClockNode
# ───────────────────────────────────────────────────────────────


def _run_clock(fs: float, pack_size: int, seconds: float) -> list[tuple[np.ndarray, np.ndarray]]:
    """(dispatched array, copy taken when it arrived) per pack."""
    import asyncio

    packs: list[tuple[np.ndarray, np.ndarray]] = []

    async def run():
        node = ClockNode("clock")
        node.set_properties({"fs": fs, "pack_size": pack_size})
        node.outputs["times"].subscribe(1, lambda values: packs.append((values[0], values[0].copy())))
        node.inputs["enabled"].dispatch([np.array([True])])
        await asyncio.sleep(seconds)
        node.inputs["enabled"].dispatch([np.array([False])])
        node.finalize()

    asyncio.run(run())
    return packs


def test_clock_keeps_its_rate():
    # 50 packs/s: a clock that slept 20 ms after each emit lost the timer
    # rounding every period (about 32 packs/s with 15.6 ms timer ticks).
    packs = _run_clock(fs=50.0, pack_size=1, seconds=2.0)
    assert 92 <= len(packs) <= 102


def test_clock_times_come_from_a_counter_in_one_buffer():
    packs = _run_clock(fs=100.0, pack_size=4, seconds=0.5)
    assert len(packs) >= 5
    for k, (pack, at_arrival) in enumerate(packs):
        assert pack.dtype == np.float64
        np.testing.assert_array_equal(at_arrival, (np.arange(4) + 4 * k) / 100.0)
    # Values are valid during the dispatch (receivers copy what they keep):
    # every pack is written into the same buffer, nothing is allocated per pack.
    assert len({id(pack) for pack, _ in packs}) == 1


def test_clock_times_stay_finer_than_a_sample_after_a_day_at_192_khz():
    # float32 times stop telling neighbouring samples apart after about a
    # minute at 192 kHz; float64 keeps them about 1e-6 of a sample apart.
    import asyncio

    fs, pack_size = 192_000.0, 1920
    packs: list[np.ndarray] = []

    async def run():
        node = ClockNode("clock")
        node.set_properties({"fs": fs, "pack_size": pack_size})
        node._index = int(fs) * 86_400  # one day of samples
        node.outputs["times"].subscribe(1, lambda values: packs.append(values[0].copy()))
        node.inputs["enabled"].dispatch([np.array([True])])
        await asyncio.sleep(0.05)
        node.finalize()

    asyncio.run(run())
    times = packs[0]
    assert times[0] == pytest.approx(86_400.0)
    np.testing.assert_allclose(np.diff(times), 1.0 / fs, rtol=1e-5)


# ───────────────────────────────────────────────────────────────
# TickClockNode
# ───────────────────────────────────────────────────────────────


def _dispatch_tick(node: TickClockNode, batch_size: int) -> np.ndarray:
    """Dispatch a single tick of given batch size and return the latest times output."""
    node.inputs["tick"].dispatch([np.ones(batch_size, dtype=np.bool_)])
    assert node.outputs["times"].current_values is not None
    return node.outputs["times"].current_values[0]


def test_tick_clock_single_tick_emits_zero_then_increments():
    node = TickClockNode("test")

    first = _dispatch_tick(node, 1)
    assert isinstance(first, np.ndarray)
    assert first.dtype == np.float64
    assert first.shape == (1,)
    assert first[0] == 0.0

    second = _dispatch_tick(node, 1)
    assert second[0] == 1.0 / 30.0


def test_tick_clock_batch_tick_emits_arange_then_advances():
    node = TickClockNode("test")

    out = _dispatch_tick(node, 3)
    assert out.shape == (3,)
    assert out[0] == 0.0 / 30.0
    assert out[1] == 1.0 / 30.0
    assert out[2] == 2.0 / 30.0

    # next tick should start at frame_index=3
    nxt = _dispatch_tick(node, 1)
    assert nxt[0] == 3.0 / 30.0


def test_tick_clock_exact_at_fs_boundary():
    """At fs=30, after exactly 30 ticks, the next tick must emit 1.0 exactly.

    A naive `time += 1/fs` accumulator would produce 0.9999999... here due to
    f64 representation of 1/30; frame_index-based computation must be bit-exact.
    """
    node = TickClockNode("test")
    for _ in range(30):
        _dispatch_tick(node, 1)
    out = _dispatch_tick(node, 1)
    assert out[0] == 1.0  # bit-exact equality, not approx


def test_tick_clock_reset_zeros_frame_index():
    node = TickClockNode("test")
    _dispatch_tick(node, 5)
    assert node._frame_index == 5

    node.inputs["reset"].dispatch([np.array([True])])
    reset_out = node.outputs["times"].current_values[0]
    assert reset_out.shape == (1,)
    assert reset_out[0] == 0.0
    assert node._frame_index == 0

    nxt = _dispatch_tick(node, 1)
    assert nxt[0] == 0.0


def test_tick_clock_set_properties_changes_fs():
    node = TickClockNode("test")

    node.set_properties({"fs": 60.0})
    assert node._fs == 60.0
    assert node.properties["fs"] == 60.0

    out = _dispatch_tick(node, 1)
    assert out[0] == 0.0
    nxt = _dispatch_tick(node, 1)
    assert nxt[0] == 1.0 / 60.0


def test_tick_clock_set_properties_rejects_nonpositive_fs():
    node = TickClockNode("test")
    with pytest.raises(ValueError):
        node.set_properties({"fs": 0.0})
    with pytest.raises(ValueError):
        node.set_properties({"fs": -1.0})
    # state unchanged
    assert node._fs == 30.0


def test_tick_clock_no_overflow_at_10_years():
    """At 30 fps, 10**10 frames is ~10.5 years. Output must be bit-exact."""
    node = TickClockNode("test")
    node._frame_index = 10**10
    out = _dispatch_tick(node, 1)
    assert out[0] == (10**10) / 30.0


def test_tick_clock_no_overflow_near_f64_precision_limit():
    """f64 integer precision is 2^53 ~ 9e15. 10**15 frames at 30 fps is ~1 million years.

    This is the spot check for the precision boundary: as long as frame_index
    stays under 2^53, division by fs is exact for representable quotients.
    """
    node = TickClockNode("test")
    node._frame_index = 10**15
    out = _dispatch_tick(node, 1)
    # The integer 10**15 is exactly representable in f64 (well under 2^53).
    assert out[0] == (10**15) / 30.0


def test_tick_clock_describe_category_is_time():
    doc = TickClockNode.describe()
    assert doc.category == "Time"
    assert "tick" in doc.inputs
    assert "reset" in doc.inputs
    assert "times" in doc.outputs
