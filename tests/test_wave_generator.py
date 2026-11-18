"""WaveGenerator: waveforms, modulation (fm, pm), buffers and documentation."""

import logging
import math

import numpy as np
import pytest

from nonoha_core._testing import assert_all_ports_documented
from nonoha_core.data_type import DataType, PortValueType, port_value_type_can_cast
from nonoha_core.node_registry import NodeRegistry
from nonoha_core.nodes.wave_generator import WaveGeneratorNode

QUARTERS = np.array([0.0, 0.25, 0.5, 0.75])  # at 1 Hz: u = t


def make(**props):
    node = WaveGeneratorNode("wave")
    node.set_properties({"frequency": 1.0, **props})
    out: list[np.ndarray] = []
    node.outputs["series"].subscribe(1, lambda v: out.append(v[0].copy()))
    return node, out


def run(node, out, times, dtype: type[np.floating] = np.float64):
    node.inputs["times"].dispatch([np.asarray(times, dtype=dtype)])
    return out[-1]


@pytest.mark.parametrize(
    "waveform, expected",
    [
        ("sine", [0, 1, 0, -1]),
        ("square", [1, 1, -1, -1]),
        ("triangle", [0, 1, 0, -1]),
        ("saw", [0, 0.5, -1, -0.5]),
    ],
)
def test_waveforms_rise_through_zero_at_phase_zero(waveform, expected):
    node, out = make(waveform=waveform)
    np.testing.assert_allclose(run(node, out, QUARTERS), expected, atol=1e-6)


@pytest.mark.parametrize(
    "waveform, base",
    [("sine", [0, 1, 0, -1]), ("square", [1, 1, -1, -1]), ("triangle", [0, 1, 0, -1]), ("saw", [0, 0.5, -1, -0.5])],
)
def test_amplitude_and_offset_for_every_waveform(waveform, base):
    node, out = make(waveform=waveform, amplitude=2.0, offset=0.5)
    np.testing.assert_allclose(run(node, out, QUARTERS), 2.0 * np.array(base) + 0.5, atol=1e-6)


def test_amplitude_offset_and_phase():
    node, out = make(amplitude=2.0, offset=0.5, phase=math.pi / 2)
    np.testing.assert_allclose(run(node, out, QUARTERS), 2.0 * np.cos(2 * np.pi * QUARTERS) + 0.5, atol=1e-6)


def test_series_is_f32_in_one_buffer():
    node = WaveGeneratorNode("wave")
    seen: list[np.ndarray] = []
    node.outputs["series"].subscribe(1, lambda v: seen.append(v[0]))
    for k in range(3):
        node.inputs["times"].dispatch([np.arange(8, dtype=np.float64) / 600 + k])
    assert all(s.dtype == np.float32 for s in seen)
    # Dispatched values are valid during the dispatch: one buffer, no allocation per block.
    assert len({id(s) for s in seen}) == 1


def test_f32_and_f64_senders_connect():
    node = WaveGeneratorNode("wave")
    for port in ("times", "fm", "pm"):
        target = node.inputs[port].value_type_list[0]
        for data_type in (DataType.Float32, DataType.Float64):
            assert port_value_type_can_cast(PortValueType(data_type), target)
    node, out = make()
    np.testing.assert_allclose(run(node, out, QUARTERS, dtype=np.float32), [0, 1, 0, -1], atol=1e-6)


def test_a_year_in_the_period_is_still_exact():
    node, out = make(frequency=50.0)
    times = 365 * 86_400.0 + np.arange(4) / 200.0  # quarter periods of 50 Hz
    np.testing.assert_allclose(run(node, out, times), [0, 1, 0, -1], atol=1e-5)


def test_pm_per_sample_and_as_one_value():
    node, out = make()
    node.inputs["pm"].dispatch([np.full(4, math.pi / 2)])
    np.testing.assert_allclose(run(node, out, QUARTERS), np.cos(2 * np.pi * QUARTERS), atol=1e-6)
    node.inputs["pm"].dispatch([np.array([math.pi])])
    np.testing.assert_allclose(run(node, out, QUARTERS), -np.sin(2 * np.pi * QUARTERS), atol=1e-6)


def test_pm_of_another_length_is_ignored_with_one_warning(caplog):
    node, out = make()
    node.inputs["pm"].dispatch([np.ones(3)])
    with caplog.at_level(logging.WARNING):
        first = run(node, out, QUARTERS)
        run(node, out, QUARTERS)
    np.testing.assert_allclose(first, np.sin(2 * np.pi * QUARTERS), atol=1e-6)
    assert sum("pm has 3 values" in r.getMessage() for r in caplog.records) == 1


def test_modulation_is_copied_on_arrival():
    node, out = make()
    block = np.full(4, math.pi / 2)
    node.inputs["pm"].dispatch([block])
    block[:] = 0.0  # the sender reuses its buffer after the dispatch
    np.testing.assert_allclose(run(node, out, QUARTERS), np.cos(2 * np.pi * QUARTERS), atol=1e-6)


def test_fm_as_one_value_shifts_the_frequency():
    times = np.arange(2000) / 1000.0
    node, out = make(frequency=10.0)
    node.inputs["fm"].dispatch([np.array([2.0])])
    np.testing.assert_allclose(run(node, out, times), np.sin(2 * np.pi * 12.0 * times), atol=1e-4)


def test_sine_fm_equals_pm_of_deviation_over_rate():
    # fm = dev sin(2 pi rate t) integrates to a phase of beta (1 - cos(2 pi rate t)), beta = dev / rate.
    times = np.arange(8000) / 1000.0
    dev, rate = 2.0, 0.5
    fm_node, fm_out = make(frequency=10.0)
    fm_node.inputs["fm"].dispatch([dev * np.sin(2 * np.pi * rate * times)])
    pm_node, pm_out = make(frequency=10.0)
    pm_node.inputs["pm"].dispatch([dev / rate * (1.0 - np.cos(2 * np.pi * rate * times))])
    np.testing.assert_allclose(run(fm_node, fm_out, times), run(pm_node, pm_out, times), atol=1e-3)


def test_fm_integral_restarts_when_the_time_goes_back():
    times = np.arange(100) / 100.0
    node, out = make()
    node.inputs["fm"].dispatch([np.array([0.3])])
    first = run(node, out, times)
    run(node, out, times + 1.0)
    again = run(node, out, times)  # back to 0, e.g. a Clock reset
    np.testing.assert_allclose(again, first, atol=1e-6)


@pytest.mark.parametrize("bad", ["per sample", "one value"])
def test_one_nan_fm_block_does_not_poison_the_rest(bad):
    times = np.arange(100) / 100.0
    node, out = make()
    if bad == "per sample":
        fm = np.zeros(100)
        fm[50] = np.nan
        node.inputs["fm"].dispatch([fm])
    else:
        node.inputs["fm"].dispatch([np.array([np.inf])])
    with np.errstate(invalid="ignore"):
        run(node, out, times)  # this block is lost
    node.inputs["fm"].dispatch([np.array([0.0])])
    later = run(node, out, times + 1.0)
    assert np.isfinite(later).all()


@pytest.mark.parametrize("fm", [None, "per sample", "one value"])
def test_blocks_join_without_a_seam(fm):
    times = np.arange(600) / 600.0
    mod = 3.0 * np.sin(2 * np.pi * 0.7 * times)

    def generate(cuts):
        node, out = make(frequency=7.0, waveform="triangle")
        parts = []
        for a, b in zip(cuts[:-1], cuts[1:]):
            if fm == "per sample":
                node.inputs["fm"].dispatch([mod[a:b]])
            elif fm == "one value":
                node.inputs["fm"].dispatch([np.array([1.5])])
            parts.append(run(node, out, times[a:b]))
        return np.concatenate(parts)

    np.testing.assert_allclose(generate([0, 600]), generate([0, 20, 220, 221, 600]), atol=1e-5)


def test_property_ports_and_validation():
    node, _ = make()
    node.inputs["@waveform"].dispatch([np.array(["square"])])
    assert node.properties["waveform"] == "square"
    node.set_properties({"frequency": 10})  # ints in older graphs
    assert node.properties["frequency"] == 10.0
    with pytest.raises(ValueError):
        node.set_properties({"waveform": "noise"})
    with pytest.raises(ValueError):
        node.set_properties({"frequency": float("nan"), "amplitude": 3.0})
    assert node.properties["amplitude"] == 1.0  # nothing applied from a rejected update


def test_ports_and_properties_are_documented():
    registry = NodeRegistry()
    registry.register_node("WaveGenerator", WaveGeneratorNode)
    assert_all_ports_documented(registry)
    node = WaveGeneratorNode("wave")
    assert {"@frequency", "@amplitude", "@offset", "@phase", "@waveform"} <= set(node.inputs)
    assert "modulation" not in node.inputs
