"""Tests for nonoha_core.inspection (fake clock, fake transport)."""

import json

import numpy as np
import pytest

from nonoha_core.data_type import DataType, PortValueType
from nonoha_core.inspection import (
    FRAME_SAMPLE,
    Inspector,
    InspectorFull,
    Limits,
    ReduceSpec,
    decode_header,
    reduce_values,
)
from nonoha_core.inspection.reduce import FLAG_REDUCED, FLAG_TRUNCATED, effective_type, summarize
from nonoha_core.node import BaseNode, BaseNodeGraph, replace_node_output_port
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort


def subscribed(port) -> bool:
    """The test source has no edges, so any subscriber is a probe."""
    return bool(port._callback_keys)


# --- reduction ----------------------------------------------------------------------

def test_reduce_batch_slice_stride_cast():
    frame = np.arange(2 * 100 * 200 * 3, dtype=np.uint8).reshape(2, 100, 200, 3)
    r = reduce_values([frame], ReduceSpec(batch="last", max_bytes=10**9))
    assert r.values[0].shape == (1, 100, 200, 3) and r.types[0].name == "u8[100x200x3]"

    r = reduce_values([frame], ReduceSpec(batch="all", auto_stride=[0, 1], max_bytes=8000))
    assert r.values[0].shape[0] == 2 and r.values[0].nbytes <= 8000
    assert r.steps[0][0] == r.steps[0][1] > 1 and r.steps[0][2] == 1 and r.flags & FLAG_REDUCED

    r = reduce_values([frame], ReduceSpec(slices=[[10, 20], None, [0, 1]], max_bytes=10**9))
    assert r.values[0].shape == (1, 10, 200, 1)

    floats = np.ones((1, 4), np.float64)
    r = reduce_values([floats], ReduceSpec(cast="f32", max_bytes=10**9))
    assert r.values[0].dtype == np.float32 and r.types[0].data_type == DataType.Float32


def test_reduce_flags_truncation_and_odd_types():
    big = np.zeros((1, 5000), np.float32)
    assert reduce_values([big], ReduceSpec(max_bytes=1024)).flags & FLAG_TRUNCATED

    cplx = np.array([[1 + 1j, 3 + 4j]], np.complex64)
    r = reduce_values([cplx], ReduceSpec(max_bytes=10**6))
    np.testing.assert_allclose(r.values[0], [[np.sqrt(2), 5]], rtol=1e-6)

    text = np.array(["hello"])
    assert effective_type(text).data_type == DataType.String
    stats, last = summarize(np.array([[1.0, np.nan, 3.0]]))
    assert stats == [1.0, 3.0, 2.0] and last is None
    assert summarize(np.array([7.5], np.float32)) == ([7.5, 7.5, 7.5], 7.5)


# --- a small graph to inspect -----------------------------------------------------------

class Source(BaseNode):
    def __init__(self, name):
        super().__init__(name, "Source")
        self.out = StaticTypeOutputPort("out", [PortValueType(DataType.Float32, (-1,))])
        self.outputs["out"] = self.out

    def emit(self, n=4, value=1.0):
        self.out.dispatch([np.full((1, n), value, np.float32)])


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def make(limits=None):
    graph = BaseNodeGraph("g", {})
    source = Source("Source_1")
    graph.add_node(source)
    clock = Clock()
    sent = []
    inspector = Inspector(lambda ref: graph if ref == "g" else None, limits or Limits(), clock=clock)
    session = inspector.open_session("g", sent.append)
    return graph, source, clock, inspector, session, sent


def frames(sent):
    return [m for m in sent if isinstance(m, (bytes, bytearray))]


def messages(sent, kind):
    return [m for m in sent if isinstance(m, dict) and m.get("t") == kind]


def step(inspector, clock, seconds, dt=0.05):
    for _ in range(int(round(seconds / dt))):
        clock.t += dt
        inspector.tick(clock.t)


def test_nothing_observed_until_watched_and_released_after():
    graph, source, clock, inspector, session, sent = make()
    assert messages(sent, "hello") and not subscribed(source.out)
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out", "interval_ms": 100})
    assert subscribed(source.out)
    ack = messages(sent, "watch_ack")[0]
    assert ack["types"] == ["f32[?]"]
    inspector.handle(session, {"op": "unwatch", "id": 1})
    assert not subscribed(source.out)

    inspector.handle(session, {"op": "watch", "id": 2, "node": "Source_1", "port": "out"})
    inspector.close_session(session)
    assert not subscribed(source.out) and inspector.sessions == []


def sample_floats(frame):
    """The float32 data of a one-slot sample frame."""
    header = decode_header(frame)
    payload = bytes(frame[header["payload_offset"]:])
    ndim = payload[2]
    start = 3 + 2 * ndim + 4
    return np.frombuffer(payload, dtype=">f4", offset=start)


def test_a_sample_is_the_first_dispatch_after_it_is_due_and_credit_window():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out", "interval_ms": 50})
    for i in range(100):
        source.emit(value=float(i))
    step(inspector, clock, 0.05)
    got = frames(sent)
    assert len(got) == 1  # 100 dispatches -> one sample
    header = decode_header(got[0])
    # A watch is due when it is made: the next dispatch is its sample
    assert header["kind"] == FRAME_SAMPLE and header["dispatch_count"] == 1
    assert sample_floats(got[0]).tolist() == [0.0] * 4

    # Without acks, at most credit_frames samples are in flight.
    for _ in range(5):
        source.emit()
        step(inspector, clock, 0.05)
    assert len(frames(sent)) == 2
    inspector.ack(session, decode_header(frames(sent)[-1])["frame_seq"])
    source.emit()
    step(inspector, clock, 0.05)
    assert len(frames(sent)) == 3


class ReusingSource(BaseNode):
    """Dispatches its one buffer, then starts writing the next value into it
    (like ValuesBuffer): legal, since a value is valid during the dispatch."""

    def __init__(self, name):
        super().__init__(name, "Source")
        self.out = StaticTypeOutputPort("out", [PortValueType(DataType.Float32, (-1,))])
        self.outputs["out"] = self.out
        self.buffer = np.zeros((1, 4), np.float32)

    def emit_then_scribble(self, value):
        self.buffer[:] = value
        self.out.dispatch([self.buffer])
        self.buffer[0, :2] = -1.0  # the head of the next value, never dispatched


def test_a_sample_is_what_was_dispatched_even_when_the_sender_reuses_its_buffer():
    graph = BaseNodeGraph("g", {})
    source = ReusingSource("Source_1")
    graph.add_node(source)
    clock = Clock()
    sent = []
    inspector = Inspector(lambda ref: graph if ref == "g" else None, Limits(), clock=clock)
    session = inspector.open_session("g", sent.append)
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out", "interval_ms": 50})
    inspector.handle(session, {"op": "activity", "interval_ms": 50,
                               "ports": [{"id": 7, "node": "Source_1", "port": "out"}]})
    source.emit_then_scribble(5.0)
    step(inspector, clock, 0.05)
    assert sample_floats(frames(sent)[0]).tolist() == [5.0] * 4  # not [-1, -1, 5, 5]
    rows = [row for m in messages(sent, "activity") for row in m["p"] if row[1] == 1]
    assert rows and rows[-1][6] == [5.0, 5.0, 5.0]


def test_no_dispatch_no_copy():
    """Between samples, a dispatch takes nothing: no allocation on the hot path."""
    import tracemalloc

    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out", "interval_ms": 1000})
    value = [np.ones((1, 4096), np.float32)]
    source.out.dispatch(value)  # taken: the watch was due
    step(inspector, clock, 0.05)  # sent; the next sample is due in a second
    tracemalloc.start()
    for _ in range(100):
        source.out.dispatch(value)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 4096  # far below one copy of the value (16 KiB)


def test_no_new_dispatch_no_new_sample_but_snapshot_forces_one():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out", "interval_ms": 50})
    source.emit()
    step(inspector, clock, 0.05)
    inspector.ack(session, 10)
    step(inspector, clock, 0.5)
    assert len(frames(sent)) == 1
    inspector.handle(session, {"op": "snapshot", "id": 1})
    step(inspector, clock, 0.05)
    assert len(frames(sent)) == 2


def test_budget_throttles_large_samples():
    limits = Limits(budget_bps=40_000, total_budget_bps=40_000, credit_frames=100, credit_bytes=10**9)
    graph, source, clock, inspector, session, sent = make(limits)
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out",
                               "interval_ms": 50, "max_bytes": 200_000})
    for _ in range(40):  # two seconds of 40 KB dispatches at 20 Hz
        source.emit(n=10_000)
        step(inspector, clock, 0.05)
    total = sum(len(f) for f in frames(sent))
    assert total <= 40_000 * 2 + 41_000  # never far above the budget
    assert any(m["state"] == "throttled" for m in messages(sent, "status"))


def test_accumulate_since_last_sample():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out",
                               "interval_ms": 100, "batch": "since"})
    for i in range(3):
        source.emit(n=2, value=float(i))
    step(inspector, clock, 0.1)
    header = decode_header(frames(sent)[0])
    assert header["flags"] & 0x02  # all rows of the accumulated dispatches
    # 3 dispatches x (1, 2) -> (3, 2) floats in the payload
    payload = frames(sent)[0][header["payload_offset"]:]
    assert payload[0] == 1 and int.from_bytes(payload[3 + 2 * 1:3 + 2 * 1 + 4], "big") == 3 * 2 * 4


def test_activity_reports_rate_shape_and_stats():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "activity", "interval_ms": 500,
                               "ports": [{"id": 7, "node": "Source_1", "port": "out"}]})
    step(inspector, clock, 0.05)
    for _ in range(10):
        source.emit(value=2.0)
        step(inspector, clock, 0.1)
    step(inspector, clock, 0.6)  # one more report after the last dispatch
    rows = [row for m in messages(sent, "activity") for row in m["p"]]
    last = rows[-1]
    assert last[0] == 7 and last[1] == 10 and last[4] == "f4" and last[5] == [1, 4]
    assert last[6] == [2.0, 2.0, 2.0] and 4.0 <= last[2] <= 12.0


def test_lag_pauses_detaches_and_resumes():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out"})
    # The tick runs 0.6 s late twice: two spikes > 500 ms within 5 s.
    for _ in range(2):
        inspector._scheduled = clock.t + 0.05
        clock.t += 0.65
        inspector.tick(clock.t)
    assert inspector.paused and not subscribed(source.out)
    assert messages(sent, "status")[-1]["state"] == "paused"

    inspector._scheduled = None
    step(inspector, clock, 4.0)  # healthy ticks for > lag_resume_hold_s
    assert not inspector.paused and subscribed(source.out)


def test_replaced_port_is_followed_and_removed_port_reported():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out", "interval_ms": 50})
    new = StaticTypeOutputPort("out", [PortValueType(DataType.Float32, (-1,))])
    replace_node_output_port(source, source.out, new)
    source.out = new
    step(inspector, clock, 0.6)
    assert subscribed(new)

    graph.remove_node("Source_1")
    step(inspector, clock, 0.6)
    assert messages(sent, "gone")


def test_limits_and_bad_requests():
    graph, source, clock, inspector, session, sent = make(Limits(max_sessions=1, max_watches=1))
    with pytest.raises(InspectorFull):
        inspector.open_session("g", lambda m: None)
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out"})
    inspector.handle(session, {"op": "watch", "id": 2, "node": "Source_1", "port": "out"})
    inspector.handle(session, {"op": "nope"})
    errors = messages(sent, "error")
    assert len(errors) == 2 and "at most 1 watches" in errors[0]["message"]
    json.dumps(sent[0])  # hello is JSON-serializable


# --- review fixes (2026-11-18) --------------------------------------------------------

def test_operations_on_a_closed_session_are_ignored():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "close"})
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out"})
    inspector.handle(session, {"op": "activity", "ports": [{"id": 1, "node": "Source_1", "port": "out"}]})
    assert not subscribed(source.out) and not inspector._probes


def test_huge_numbers_are_a_bad_request_not_a_crash():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "unwatch", "id": float("inf")})
    assert messages(sent, "error")[-1]["code"] == "bad_request"


def test_a_failing_tick_does_not_stop_the_timer():
    import asyncio

    async def run():
        graph, source, clock, inspector, session, sent = make()
        inspector._clock = lambda: asyncio.get_running_loop().time()
        calls = []

        def failing_tick(now):
            calls.append(now)
            if len(calls) == 1:
                raise RuntimeError("boom")

        inspector.tick = failing_tick
        inspector._ensure_running()
        await asyncio.sleep(0.2)
        inspector.close()
        return calls

    assert len(asyncio.run(run())) >= 2


def test_a_stall_counts_once_and_is_not_caught_up():
    import asyncio
    import time as _time

    async def run():
        graph, source, clock, inspector, session, sent = make()
        loop = asyncio.get_running_loop()
        inspector._clock = loop.time
        ticks = []
        real_tick = inspector.tick

        def tick(now):
            ticks.append(now)
            real_tick(now)

        inspector.tick = tick
        inspector._ensure_running()
        await asyncio.sleep(0.12)
        _time.sleep(0.7)  # the loop stalls (> lag_spike_ms)
        before = len(ticks)
        await asyncio.sleep(0.12)
        after = len(ticks)
        inspector.close()
        return before, after, inspector

    before, after, inspector = asyncio.run(run())
    assert after - before <= 4  # no burst of 14 catch-up ticks
    assert not inspector.paused  # one spike is not two


def test_a_frame_larger_than_the_bucket_goes_out_on_credit():
    limits = Limits(budget_bps=100_000, total_budget_bps=100_000, credit_frames=100, credit_bytes=10**9,
                    hard_max_bytes=4_000_000)
    graph, source, clock, inspector, session, sent = make(limits)
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out",
                               "interval_ms": 50, "max_bytes": 1_000_000})
    source.emit(n=60_000)  # a 240 KB frame (u16 dimensions), 2.4x the bucket
    step(inspector, clock, 0.05)
    assert len(frames(sent)) == 1 and len(frames(sent)[0]) > 240_000


def test_an_exhausted_budget_encodes_nothing():
    from unittest import mock

    limits = Limits(budget_bps=1_000, total_budget_bps=1_000, credit_frames=100, credit_bytes=10**9)
    graph, source, clock, inspector, session, sent = make(limits)
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out",
                               "interval_ms": 50, "batch": "since", "max_bytes": 100_000})
    source.emit(n=10_000)
    step(inspector, clock, 0.05)  # 40 KB sent on credit: the bucket is far below zero
    from nonoha_core.inspection import hub as hub_module
    with mock.patch.object(hub_module, "encode_sample", wraps=hub_module.encode_sample) as encode:
        for _ in range(5):
            source.emit(n=10)
            step(inspector, clock, 0.05)
        assert encode.call_count == 0
    # The rows accumulated meanwhile are kept, not dropped
    assert inspector._probes[("g", next(iter(session.watches.values())).ref)].accumulators[0].lengths[0] == 5


def test_a_client_that_never_acks_is_given_a_new_window():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out", "interval_ms": 50})
    for _ in range(6):
        source.emit()
        step(inspector, clock, 0.05)
    assert len(frames(sent)) == 2  # the credit window is full
    for _ in range(120):  # 6 s without an ack
        source.emit()
        step(inspector, clock, 0.05)
    assert len(frames(sent)) > 2


def test_a_watch_made_while_paused_gets_its_types_and_no_false_gone():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "activity", "ports": [{"id": 1, "node": "Source_1", "port": "out"}]})
    inspector._pause(clock.t)
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out"})
    assert not messages(sent, "gone")
    assert messages(sent, "watch_ack")[-1]["types"] == ["f32[?]"]
    acks = len(messages(sent, "watch_ack"))
    inspector.handle(session, {"op": "force_resume"})
    assert not inspector.paused and len(messages(sent, "watch_ack")) == acks  # same port: nothing to announce


def test_a_replaced_port_is_announced_again():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out", "interval_ms": 50})
    acks = len(messages(sent, "watch_ack"))
    new = StaticTypeOutputPort("out", [PortValueType(DataType.Float64, (-1,))])
    replace_node_output_port(source, source.out, new)
    step(inspector, clock, 0.6)
    assert len(messages(sent, "watch_ack")) == acks + 1
    assert messages(sent, "watch_ack")[-1]["types"] == ["f64[?]"]


def test_a_session_closed_while_reporting_does_not_hide_the_others():
    graph, source, clock, inspector, _, first = make()
    second = []
    other = inspector.open_session("g", second.append)
    for s in inspector.sessions:
        inspector.handle(s, {"op": "watch", "id": 1, "node": "Source_1", "port": "out"})

    def failing(message):
        raise RuntimeError("socket gone")

    inspector.sessions[0].send = failing
    graph.remove_node("Source_1")
    step(inspector, clock, 0.6)
    assert messages(second, "gone")


def test_resume_is_for_the_session_and_force_resume_for_the_engine():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out"})
    inspector._pause(clock.t)
    scale = inspector.interval_scale
    inspector.handle(session, {"op": "pause"})
    inspector.handle(session, {"op": "resume"})  # a tab shown again
    assert inspector.paused and not subscribed(source.out) and inspector.interval_scale == scale
    inspector.handle(session, {"op": "force_resume"})  # "Resume now"
    assert not inspector.paused and subscribed(source.out)


def test_summarize_scalars_nan_and_integers():
    assert summarize(np.float64(3.0)) == ([3.0, 3.0, 3.0], 3.0)
    assert summarize(np.array(2.0)) == ([2.0, 2.0, 2.0], 2.0)
    stats, last = summarize(np.array([[1.0, np.nan, 3.0]], np.float32))
    assert stats == [1.0, 3.0, 2.0] and last is None
    assert summarize(np.array([[1, 2], [3, 4]], np.int16)) == ([1.0, 4.0, 2.5], None)
    assert summarize(np.array([[np.inf]])) == (None, None)
    assert summarize(np.array([True, False])) == ([0.0, 1.0, 0.5], 0.0)


def test_accumulator_keeps_order_cap_and_shape_changes_without_allocating():
    import tracemalloc

    from nonoha_core.inspection.probe import Accumulator

    acc = Accumulator(cap=8 * 4 * 4)  # 8 rows of 4 float32
    for i in range(3):
        acc.push([np.full((2, 4), i, np.float32)])
    assert acc.take()[0][:, 0].tolist() == [0, 0, 1, 1, 2, 2]
    for i in range(6):  # 12 rows into 8: the oldest 4 are overwritten
        acc.push([np.full((2, 4), i, np.float32)])
    assert acc.take()[0][:, 0].tolist() == [2, 2, 3, 3, 4, 4, 5, 5]
    acc.push([np.zeros((1, 3), np.float32)])  # a new shape starts over
    assert acc.take()[0].shape == (1, 3)
    acc.push([np.zeros((20, 3), np.float32)])  # one dispatch larger than the cap: kept whole
    assert acc.take()[0].shape == (20, 3)
    value = [np.ones((1, 3), np.float32)]
    acc.push(value)
    tracemalloc.start()
    for _ in range(100):
        acc.push(value)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert peak < 2048  # views only, no copies of the data
