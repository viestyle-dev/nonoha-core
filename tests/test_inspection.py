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


def test_latest_wins_and_credit_window():
    graph, source, clock, inspector, session, sent = make()
    inspector.handle(session, {"op": "watch", "id": 1, "node": "Source_1", "port": "out", "interval_ms": 50})
    for i in range(100):
        source.emit(value=float(i))
    step(inspector, clock, 0.05)
    got = frames(sent)
    assert len(got) == 1  # 100 dispatches -> one sample of the newest value
    header = decode_header(got[0])
    assert header["kind"] == FRAME_SAMPLE and header["dispatch_count"] == 100

    # Without acks, at most credit_frames samples are in flight.
    for _ in range(5):
        source.emit()
        step(inspector, clock, 0.05)
    assert len(frames(sent)) == 2
    inspector.ack(session, decode_header(frames(sent)[-1])["frame_seq"])
    source.emit()
    step(inspector, clock, 0.05)
    assert len(frames(sent)) == 3


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
