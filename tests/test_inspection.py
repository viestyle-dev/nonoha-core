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
from nonoha_core.inspection.reduce import FLAG_GAP, FLAG_REDUCED, effective_type, summarize
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
    # Two items do not fit: the newest is kept, and strided since it alone is too large
    assert r.values[0].shape[0] == 1 and r.values[0].nbytes <= 8000
    assert np.array_equal(r.values[0][0, 0, 0], frame[1, 0, 0])
    assert r.steps[0][0] == r.steps[0][1] > 1 and r.steps[0][2] == 1 and r.flags & FLAG_REDUCED

    r = reduce_values([frame], ReduceSpec(slices=[[10, 20], None, [0, 1]], max_bytes=10**9))
    assert r.values[0].shape == (1, 10, 200, 1)

    floats = np.ones((1, 4), np.float64)
    r = reduce_values([floats], ReduceSpec(cast="f32", max_bytes=10**9))
    assert r.values[0].dtype == np.dtype(">f4") and r.types[0].data_type == DataType.Float32  # in wire order


def test_reduce_too_large_and_odd_types():
    big = np.zeros((1, 5000), np.float32)
    assert reduce_values([big], ReduceSpec(max_bytes=1024)).values is None

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


def lag_pause(inspector, clock):
    """Two ticks 0.6 s late (two spikes > 500 ms within 5 s): the engine-wide pause."""
    for _ in range(2):
        inspector._scheduled = clock.t + 0.05
        clock.t += 0.65
        inspector.tick(clock.t)
    inspector._scheduled = None
    assert inspector.paused


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
    step(inspector, clock, 0.05)  # nothing was taken while it could not be sent: asked now
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
    step(inspector, clock, 1.6)  # past the stop (two periods, at least a second) and one round
    rows = [row for m in messages(sent, "activity") for row in m["p"]]
    flowing = [row for row in rows if row[2] > 0][-1]
    assert flowing[0] == 7 and flowing[1] == 10 and flowing[4] == "f32" and flowing[5] == [1, 4]
    assert flowing[6] == [2.0, 2.0, 2.0] and 9.5 <= flowing[2] <= 10.5
    assert rows[-1][1] == 10 and rows[-1][2] == 0.0  # and then it stopped


# --- the activity rate: steady under jitter, stops once, no spike ------------------------

def run_dispatches(inspector, clock, source, times, until, dt=0.05):
    """Tick every dt until `until`; each dispatch in `times` lands just before
    the first tick at or after it. Returns [(ts, row)] of the activity rows."""
    times = sorted(times)
    i = 0
    while clock.t < until - 1e-9:
        clock.t = round(clock.t + dt, 6)
        while i < len(times) and times[i] <= clock.t + 1e-9:
            source.emit()
            i += 1
        inspector.tick(clock.t)


def activity_rows(sent, pid=7):
    return [(m["ts"], row) for m in messages(sent, "activity") for row in m["p"] if row[0] == pid]


def watch_activity(inspector, session, ids=(7,)):
    inspector.handle(session, {"op": "activity", "interval_ms": 500,
                               "ports": [{"id": i, "node": "Source_1", "port": "out"} for i in ids]})


def test_activity_rate_of_a_2hz_port_stays_steady_under_tick_jitter():
    """A 2 Hz port sees 0, 1 or 2 dispatches per 0.5 s round; its rate must not
    read 0 (the port would look stopped) nor jump between 0, 2 and 4."""
    rng = np.random.default_rng(1)
    graph, source, clock, inspector, session, sent = make()
    watch_activity(inspector, session)
    times = [0.5 * k + 0.05 * rng.integers(-1, 2) for k in range(1, 41)]
    run_dispatches(inspector, clock, source, times, 20.0)
    steady = [row[2] for ts, row in activity_rows(sent) if 2.0 <= ts <= 19.5]
    assert steady and all(1.8 <= hz <= 2.2 for hz in steady), steady


def test_activity_rate_of_a_15hz_port():
    graph, source, clock, inspector, session, sent = make()
    watch_activity(inspector, session)
    run_dispatches(inspector, clock, source, [k / 15 for k in range(1, 151)], 10.0)
    steady = [row[2] for ts, row in activity_rows(sent) if 2.0 <= ts <= 9.9]
    assert steady and all(14.0 <= hz <= 16.0 for hz in steady), steady


def test_activity_stop_is_reported_once_two_periods_after_the_last_dispatch():
    graph, source, clock, inspector, session, sent = make()
    watch_activity(inspector, session)
    run_dispatches(inspector, clock, source, [0.5 * k for k in range(1, 7)], 8.0)  # last at 3.0 s
    rows = activity_rows(sent)
    flowing = [hz > 0 for ts, (_, _, hz, *rest) in rows]
    # flowing once established, then a single change to stopped (full rounds repeat it)
    changes = [ts for (ts, _), was, now in zip(rows[1:], flowing, flowing[1:]) if was != now]
    stopped_at = [ts for ts, row in rows if ts > 3.0 and row[2] == 0.0][0]
    assert 1.0 <= stopped_at - 3.0 <= 1.6
    assert changes[-1] == stopped_at and not any(f for (ts, _), f in zip(rows, flowing) if ts >= stopped_at)


def test_activity_after_a_stop_the_first_dispatch_has_no_rate_and_the_second_has():
    graph, source, clock, inspector, session, sent = make()
    watch_activity(inspector, session)
    run_dispatches(inspector, clock, source, [0.5 * k for k in range(1, 7)], 6.0)  # stopped at ~4.5 s
    count = activity_rows(sent)[-1][1][1]
    run_dispatches(inspector, clock, source, [6.2, 6.7], 7.5)
    after = [row for ts, row in activity_rows(sent) if ts > 6.0]
    first = [row for row in after if row[1] == count + 1]
    second = [row for row in after if row[1] == count + 2]
    assert first and all(row[2] == 0.0 for row in first)
    assert second and 1.8 <= second[0][2] <= 2.2


def test_activity_rate_does_not_spike_when_ports_are_added():
    """Adding a port (a new subscription, or another id on a watched port) starts
    a round at once; a short round must not make a rate out of one dispatch."""
    graph, source, clock, inspector, session, sent = make()
    times = [0.5 * k for k in range(1, 21)]
    run_dispatches(inspector, clock, source, [t for t in times if t <= 2.0], 2.02)
    watch_activity(inspector, session)  # subscribes while the port flows
    run_dispatches(inspector, clock, source, [t for t in times if 2.0 < t <= 5.0], 5.02)
    watch_activity(inspector, session, ids=(7, 8))  # another id on the same probe
    run_dispatches(inspector, clock, source, [t for t in times if t > 5.0], 10.0)
    rates = [row[2] for ts, row in activity_rows(sent, 7) + activity_rows(sent, 8)]
    assert rates and max(rates) <= 2.2, rates


def test_activity_single_dispatches_far_apart_are_not_a_flow():
    graph, source, clock, inspector, session, sent = make()
    watch_activity(inspector, session)
    run_dispatches(inspector, clock, source, [1.0, 13.0, 25.0], 27.0)
    assert all(row[2] == 0.0 for ts, row in activity_rows(sent))
    assert activity_rows(sent)[-1][1][1] == 3


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
    assert not subscribed(source.out) and not frames(sent)


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


def payload_floats(frame):
    """Every float32 of a one-slot sample frame (all its items)."""
    header = decode_header(frame)
    payload = bytes(frame[header["payload_offset"]:])
    ndim = payload[2]
    return np.frombuffer(payload, dtype=">f4", offset=3 + 2 * ndim + 4)


def test_items_held_back_by_the_budget_arrive_in_a_later_sample():
    limits = Limits(budget_bps=1_000, total_budget_bps=1_000, credit_frames=100, credit_bytes=10**9)
    graph, source, clock, inspector, session, sent = make(limits)
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out",
                               "interval_ms": 50, "batch": "since", "max_bytes": 100_000})
    source.emit(n=10_000)
    step(inspector, clock, 0.05)  # 40 KB sent on credit: the bucket is far below zero
    inspector.ack(session, 1)
    for i in range(5):
        source.emit(n=10, value=float(i + 1))
        step(inspector, clock, 0.05)
    assert len(frames(sent)) == 1  # held back
    for _ in range(45):  # the debt is paid back (a live client keeps its session)
        step(inspector, clock, 1.0)
        inspector.ack(session, len(frames(sent)))
    later = frames(sent)[1:]
    assert len(later) == 1 and not decode_header(later[0])["flags"] & FLAG_GAP
    assert payload_floats(later[0]).reshape(5, 10)[:, 0].tolist() == [1.0, 2.0, 3.0, 4.0, 5.0]


def test_a_client_that_never_acks_is_disconnected():
    graph, source, clock, inspector, _, _ = make()
    sent, closed = [], []
    session = inspector.open_session("g", sent.append, lambda: closed.append(True))
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out", "interval_ms": 50})
    for _ in range(6):
        source.emit()
        step(inspector, clock, 0.05)
    assert len(frames(sent)) == 2  # the credit window is full
    for _ in range(120):  # 6 s without an ack
        source.emit()
        step(inspector, clock, 0.05)
    # Its frames were never forgotten (no third frame); the session ended and told the host
    assert len(frames(sent)) == 2 and session.closed and closed == [True]
    assert not subscribed(source.out)


def test_a_watch_made_while_paused_gets_its_types_and_no_false_gone():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "activity", "ports": [{"id": 1, "node": "Source_1", "port": "out"}]})
    lag_pause(inspector, clock)
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
    lag_pause(inspector, clock)
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


# --- flow control and state (2026-11-18, second review) ------------------------------------

def watch(inspector, session, **op):
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out", **op})


def run(inspector, session, clock, sent, seconds, emit, ack=True):
    """Emit before every tick for ``seconds``, acknowledging every frame."""
    for _ in range(int(round(seconds / 0.05))):
        emit()
        step(inspector, clock, 0.05)
        if ack and frames(sent):
            inspector.ack(session, decode_header(frames(sent)[-1])["frame_seq"])


def test_a_watch_is_asked_a_tick_before_it_is_due():
    graph, source, clock, inspector, session, sent = make()
    watch(inspector, session, interval_ms=100)
    run(inspector, session, clock, sent, 2.0, source.emit)
    assert 19 <= len(frames(sent)) <= 21  # every 100 ms, not every 150 ms


def test_the_sample_time_is_when_the_dispatch_was_taken():
    graph, source, clock, inspector, session, sent = make()
    watch(inspector, session, interval_ms=100)
    clock.t = 0.0371
    source.emit()  # the first dispatch: taken now
    step(inspector, clock, 0.05)
    assert decode_header(frames(sent)[0])["t"] == pytest.approx(0.0371)


class TwoSources(BaseNodeGraph):
    pass


def test_a_small_watch_is_not_held_back_by_a_large_one():
    limits = Limits(budget_bps=100_000, total_budget_bps=10**9, credit_frames=100, credit_bytes=10**9)
    graph, source, clock, inspector, session, sent = make(limits)
    small = Source("Small")
    graph.add_node(small)
    watch(inspector, session, interval_ms=50, max_bytes=100_000)  # ~90 KB frames: the budget allows one a second
    inspector.handle(session, {"op": "watch", "id": 2, "node": "Small", "port": "out", "interval_ms": 100})

    def emit():
        source.emit(n=22_000)
        small.emit()

    run(inspector, session, clock, sent, 4.0, emit)
    by_watch = [decode_header(f)["watch_id"] for f in frames(sent)]
    assert by_watch.count(2) >= 36  # 10 Hz, as asked (it waited behind the large one before)
    assert 3 <= by_watch.count(1) <= 6  # the large one at the budget's pace


def test_the_status_does_not_flap_while_the_budget_paces_a_watch():
    graph, source, clock, inspector, session, sent = make(Limits(budget_bps=200_000, total_budget_bps=10**9))
    watch(inspector, session, interval_ms=66, max_bytes=200_000)
    run(inspector, session, clock, sent, 10.0, lambda: source.emit(n=45_000))
    states = [m["state"] for m in messages(sent, "status")]
    changes = sum(1 for a, b in zip(states, states[1:]) if a != b)
    assert "throttled" in states and changes <= 1  # it flapped ok/throttled 26 times in 10 s


def test_a_value_is_not_taken_while_it_could_not_be_sent():
    graph, source, clock, inspector, session, sent = make(Limits(credit_frames=1))
    watch(inspector, session, interval_ms=50)
    source.emit(value=1.0)
    step(inspector, clock, 0.05)
    for i in range(2, 11):  # no ack: the window is full, nothing is taken
        source.emit(value=float(i))
        step(inspector, clock, 0.05)
    inspector.ack(session, 1)
    step(inspector, clock, 0.05)  # asked again
    source.emit(value=11.0)
    step(inspector, clock, 0.05)
    assert [sample_floats(f)[0] for f in frames(sent)] == [1.0, 11.0]  # not the stale 2.0


def test_a_paused_session_takes_and_gathers_nothing():
    import tracemalloc

    graph, source, clock, inspector, session, sent = make()
    watch(inspector, session, interval_ms=50, batch="since")
    source.emit(value=1.0)
    step(inspector, clock, 0.05)
    inspector.handle(session, {"op": "pause"})
    value = [np.ones((1, 4096), np.float32)]
    tracemalloc.start()
    for _ in range(50):
        source.out.dispatch(value)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert peak < 4096  # not copied into the ring
    inspector.handle(session, {"op": "resume"})
    inspector.ack(session, 10)
    source.emit(value=7.0)
    step(inspector, clock, 0.05)
    last = frames(sent)[-1]
    assert decode_header(last)["flags"] & FLAG_GAP and payload_floats(last).tolist() == [7.0] * 4


def test_changing_only_the_interval_keeps_the_gathered_items():
    graph, source, clock, inspector, session, sent = make()
    watch(inspector, session, interval_ms=1000, batch="since")
    for i in range(3):
        source.emit(value=float(i))
    watch(inspector, session, interval_ms=50, batch="since")  # a faster subscriber joined
    step(inspector, clock, 0.05)
    assert payload_floats(frames(sent)[0]).reshape(3, 4)[:, 0].tolist() == [0.0, 1.0, 2.0]
    assert len(messages(sent, "watch_ack")) == 1  # the same watch


def test_lost_items_are_flagged():
    graph, source, clock, inspector, session, sent = make()
    watch(inspector, session, interval_ms=1000, batch="since", max_bytes=1024)  # a ring of 64 items of 4 floats
    for _ in range(3):
        source.out.dispatch([np.ones((40, 4), np.float32)])
    step(inspector, clock, 0.05)
    assert decode_header(frames(sent)[0])["flags"] & FLAG_GAP


def test_too_large_is_said_once_and_again_after_a_sample_fitted():
    graph, source, clock, inspector, session, sent = make()
    watch(inspector, session, interval_ms=50, max_bytes=1024)
    run(inspector, session, clock, sent, 0.5, lambda: source.emit(n=5000))
    run(inspector, session, clock, sent, 0.2, lambda: source.emit(n=4))
    run(inspector, session, clock, sent, 0.5, lambda: source.emit(n=5000))
    too_large = [m for m in messages(sent, "error") if m["code"] == "too_large"]
    assert len(too_large) == 2 and "max_bytes 1024" in too_large[0]["message"] and frames(sent)


def test_a_watch_id_a_frame_cannot_carry_is_refused():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "watch", "id": 70_000, "node": "Source_1", "port": "out"})
    assert messages(sent, "error")[-1]["code"] == "bad_request" and not subscribed(source.out)


def test_a_new_session_after_the_last_one_starts_fresh():
    graph, source, clock, inspector, session, sent = make()
    watch(inspector, session)
    lag_pause(inspector, clock)
    inspector.close_session(session)
    other = inspector.open_session("g", [].append)
    inspector.handle(other, {"op": "watch", "id": 1, "node": "Source_1", "port": "out"})
    assert not inspector.paused and inspector.interval_scale == 1.0 and subscribed(source.out)


def test_zero_dimensional_values_are_one_item():
    # A port's values carry a batch axis; a 0-d one (a contract violation the
    # test ports refuse) is still held as one item, not an error per dispatch
    from nonoha_core.inspection.probe import Accumulator

    acc = Accumulator(cap=64)
    for v in (1.0, 2.0):
        acc.push([np.array(v, np.float32)])
    assert acc.take()[0].tolist() == [1.0, 2.0]


def test_a_port_that_stops_shows_it_at_the_next_round():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "activity", "interval_ms": 500,
                               "ports": [{"id": 7, "node": "Source_1", "port": "out"}]})
    run(inspector, session, clock, sent, 3.0, source.emit)
    stopped_at = clock.t
    step(inspector, clock, 1.2)
    idle = [m["ts"] for m in messages(sent, "activity") for row in m["p"] if row[2] == 0.0 and m["ts"] > stopped_at]
    assert idle and idle[0] - stopped_at <= 1.05  # within two rounds, not at the fifth


def test_accumulator_slices_before_holding_and_flags_gaps():
    from nonoha_core.inspection.probe import Accumulator

    acc = Accumulator(cap=8 * 4, slices=[[0, 1]])  # 8 items of one float (of 64 channels)
    acc.push([np.arange(4 * 64, dtype=np.float32).reshape(4, 64)])
    held = acc.take()[0]
    assert held.shape == (4, 1) and held[:, 0].tolist() == [0.0, 64.0, 128.0, 192.0] and not acc.gap
    for _ in range(3):
        acc.push([np.zeros((4, 64), np.float32)])  # 12 items into 8
    assert acc.gap and acc.take()[0].shape == (8, 1)
