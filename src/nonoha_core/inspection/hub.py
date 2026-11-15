"""Inspector hub: sessions, watches and activity on top of port subscriptions.

Transport-agnostic and asyncio-only. A host (a web server, an embedded
bridge, a test) opens a session per client with a ``send`` callable that
must not block, feeds control operations (plain dicts) and acknowledgements
in, and runs the hub's timer on its event loop. Nothing is observed until a
client asks for it, and nothing runs when no session is open.

Safety rules (so inspection never takes the process down):
- latest value wins; no per-dispatch queue (except bounded accumulators)
- at most ``credit_frames`` / ``credit_bytes`` unacknowledged per session
- a token bucket per session and one across sessions cap bytes per second
- intervals widen when encoding takes too much CPU or the budget is hit
- when the event loop lags, all probes detach until it recovers
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable

from ..node import BaseNodeGraph
from .frames import encode_sample
from .probe import Accumulator, Probe, PortRef
from .reduce import ReduceSpec, reduce_values, summarize

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = 1
_CLIENT_SLOW_S = 1.0  # no ack for this long while the credit window is full


@dataclass
class Limits:
    tick_ms: float = 50.0
    activity_interval_ms: float = 500.0
    min_interval_ms: float = 50.0
    default_interval_ms: float = 200.0
    default_max_bytes: int = 256 * 1024
    hard_max_bytes: int = 4 * 1024 * 1024
    budget_bps: int = 2 * 1024 * 1024
    total_budget_bps: int = 8 * 1024 * 1024
    credit_frames: int = 2
    credit_bytes: int = 1024 * 1024
    ack_timeout_s: float = 5.0
    cpu_target: float = 0.03
    lag_pause_ms: float = 150.0
    lag_pause_hold_s: float = 1.0
    lag_spike_ms: float = 500.0
    lag_resume_ms: float = 40.0
    lag_resume_hold_s: float = 3.0
    max_sessions: int = 8
    max_watches: int = 32
    max_activity_ports: int = 1024
    stats_max_elements: int = 65536

    def public(self) -> dict:
        return {
            "min_interval_ms": self.min_interval_ms,
            "default_interval_ms": self.default_interval_ms,
            "default_max_bytes": self.default_max_bytes,
            "hard_max_bytes": self.hard_max_bytes,
            "budget_bps": self.budget_bps,
            "credit_frames": self.credit_frames,
            "max_watches": self.max_watches,
            "max_activity_ports": self.max_activity_ports,
        }


class InspectorFull(Exception):
    """Too many sessions."""


@dataclass
class Watch:
    id: int
    ref: PortRef
    interval: float  # seconds
    spec: ReduceSpec
    accumulate: bool = False
    next_due: float = 0.0
    last_count: int = -1
    snapshot: bool = False
    sample_seq: int = 0
    accumulator: Accumulator | None = None


@dataclass
class Session:
    graph_ref: Any
    send: Callable[[Any], None]
    watches: dict[int, Watch] = field(default_factory=dict)
    activity: dict[int, PortRef] = field(default_factory=dict)
    activity_interval: float = 0.5
    activity_next: float = 0.0
    activity_sent: dict[int, tuple] = field(default_factory=dict)
    activity_counts: dict[int, tuple[int, float]] = field(default_factory=dict)
    activity_rounds: int = 0
    tokens: float = 0.0
    frame_seq: int = 0
    inflight: deque[tuple[int, int]] = field(default_factory=deque)  # (frame_seq, bytes), oldest first
    inflight_bytes: int = 0
    last_ack: float = 0.0
    client_paused: bool = False
    closed: bool = False
    round_robin: int = 0


class Inspector:
    def __init__(
        self,
        resolve_graph: Callable[[Any], BaseNodeGraph | None],
        limits: Limits | None = None,
        plugins: list[dict] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._resolve = resolve_graph
        self.limits = limits or Limits()
        self._plugins = plugins or []
        self._clock = clock
        self._sessions: list[Session] = []
        self._probes: dict[tuple[Any, PortRef], Probe] = {}
        self._task: asyncio.Task | None = None

        self._total_tokens = float(self.limits.total_budget_bps)
        self._last_tick: float | None = None
        self._scheduled: float | None = None
        self._lag_ewma = 0.0
        self._lag_max = 0.0
        self._over_since: float | None = None
        self._under_since: float | None = None
        self._spikes: list[float] = []
        self.paused = False
        self.interval_scale = 1.0
        self._cpu = 0.0
        self._cpu_window_start: float | None = None
        self._healthy_since: float | None = None
        self._throttled = False
        self._reasons: set[str] = set()
        self._state_sent: tuple | None = None
        self._last_status_t = 0.0
        self._last_resolve = 0.0

    # ------------------------------------------------------------------ sessions

    @property
    def sessions(self) -> list[Session]:
        return list(self._sessions)

    def open_session(self, graph_ref: Any, send: Callable[[Any], None]) -> Session:
        if len(self._sessions) >= self.limits.max_sessions:
            raise InspectorFull(f"at most {self.limits.max_sessions} inspector sessions")
        now = self._clock()
        session = Session(graph_ref, send, tokens=float(self.limits.budget_bps), last_ack=now)
        self._sessions.append(session)
        self._send(session, {
            "t": "hello",
            "protocol": PROTOCOL_VERSION,
            "limits": self.limits.public(),
            "plugins": self._plugins,
        })
        self._ensure_running()
        return session

    def close_session(self, session: Session) -> None:
        if session.closed:
            return
        session.closed = True
        for watch in session.watches.values():
            self._release(session.graph_ref, watch.ref, watch.accumulator)
        for ref in session.activity.values():
            self._release(session.graph_ref, ref)
        session.watches.clear()
        session.activity.clear()
        if session in self._sessions:
            self._sessions.remove(session)
        if not self._sessions and self._task is not None:
            self._task.cancel()
            self._task = None

    def close(self) -> None:
        for session in list(self._sessions):
            self.close_session(session)

    # ------------------------------------------------------------------ control

    def handle(self, session: Session, op: dict) -> None:
        """Apply one control operation; errors are reported to the client."""
        try:
            kind = op.get("op")
            if kind == "hello":
                return
            if kind == "ack":
                self.ack(session, int(op.get("seq", 0)))
            elif kind == "activity":
                self._set_activity(session, op)
            elif kind == "watch":
                self._watch(session, op)
            elif kind == "unwatch":
                self._unwatch(session, int(op["id"]))
            elif kind == "snapshot":
                watch = session.watches.get(int(op["id"]))
                if watch is not None:
                    watch.snapshot = True
                    watch.next_due = 0.0
            elif kind == "pause":
                session.client_paused = True
            elif kind == "resume":
                session.client_paused = False
                if self.paused:
                    self._resume(self._clock(), forced=True)
            elif kind == "close":
                self.close_session(session)
            else:
                raise ValueError(f"unknown op {kind!r}")
        except (ValueError, KeyError, TypeError) as e:
            self._send(session, {"t": "error", "id": op.get("id"), "code": "bad_request", "message": str(e)})

    def ack(self, session: Session, seq: int) -> None:
        inflight = session.inflight  # acks are cumulative: drop every frame up to seq
        while inflight and inflight[0][0] <= seq:
            session.inflight_bytes -= inflight.popleft()[1]
        session.last_ack = self._clock()

    def _set_activity(self, session: Session, op: dict) -> None:
        ports = op.get("ports", [])
        if len(ports) > self.limits.max_activity_ports:
            raise ValueError(f"at most {self.limits.max_activity_ports} activity ports")
        wanted = {int(p["id"]): PortRef.from_op(p) for p in ports}
        for pid, ref in list(session.activity.items()):
            if wanted.get(pid) != ref:
                self._release(session.graph_ref, ref)
                del session.activity[pid]
                session.activity_sent.pop(pid, None)
                session.activity_counts.pop(pid, None)
        for pid, ref in wanted.items():
            if pid not in session.activity:
                self._acquire(session.graph_ref, ref)
                session.activity[pid] = ref
        interval = float(op.get("interval_ms", self.limits.activity_interval_ms)) / 1000.0
        session.activity_interval = max(self.limits.min_interval_ms / 1000.0, interval)
        session.activity_next = 0.0
        session.activity_rounds = 0

    def _watch(self, session: Session, op: dict) -> None:
        wid = int(op["id"])
        ref = PortRef.from_op(op)
        if wid not in session.watches and len(session.watches) >= self.limits.max_watches:
            raise ValueError(f"at most {self.limits.max_watches} watches")
        max_bytes = int(op.get("max_bytes", self.limits.default_max_bytes))
        max_bytes = max(1024, min(self.limits.hard_max_bytes, max_bytes))
        interval = float(op.get("interval_ms", self.limits.default_interval_ms)) / 1000.0
        interval = max(self.limits.min_interval_ms / 1000.0, interval)
        accumulate = op.get("batch") == "since"
        spec = ReduceSpec.from_op({**op, "batch": "all" if accumulate else op.get("batch", "last")}, max_bytes)

        old = session.watches.pop(wid, None)
        if old is not None:
            self._release(session.graph_ref, old.ref, old.accumulator)
        probe = self._acquire(session.graph_ref, ref)
        watch = Watch(wid, ref, interval, spec, accumulate=accumulate)
        if accumulate:
            watch.accumulator = Accumulator(max_bytes)
            probe.accumulators.append(watch.accumulator)
        session.watches[wid] = watch

        port = probe.port
        if port is None:
            self._send(session, {"t": "gone", "id": wid})
            return
        current = probe.values
        self._send(session, {
            "t": "watch_ack",
            "id": wid,
            "types": [vt.name for vt in port.value_type_list],
            "shape": [list(v.shape) for v in current] if current is not None else None,
        })

    def _unwatch(self, session: Session, wid: int) -> None:
        watch = session.watches.pop(wid, None)
        if watch is not None:
            self._release(session.graph_ref, watch.ref, watch.accumulator)

    # ------------------------------------------------------------------ probes

    def _acquire(self, graph_ref: Any, ref: PortRef) -> Probe:
        key = (graph_ref, ref)
        probe = self._probes.get(key)
        if probe is None:
            probe = Probe(ref)
            self._probes[key] = probe
            if not self.paused:
                self._attach(graph_ref, probe)
        probe.refs += 1
        return probe

    def _release(self, graph_ref: Any, ref: PortRef, accumulator: Accumulator | None = None) -> None:
        key = (graph_ref, ref)
        probe = self._probes.get(key)
        if probe is None:
            return
        if accumulator is not None and accumulator in probe.accumulators:
            probe.accumulators.remove(accumulator)
        probe.refs -= 1
        if probe.refs <= 0:
            probe.detach()
            del self._probes[key]

    def _attach(self, graph_ref: Any, probe: Probe) -> bool:
        graph = self._resolve(graph_ref)
        port = probe.ref.resolve(graph) if graph is not None else None
        if port is None:
            probe.detach()
            return False
        probe.attach(port)
        return True

    def _reresolve(self) -> None:
        """Follow replaced ports and report removed ones (ports change at runtime)."""
        for (graph_ref, ref), probe in list(self._probes.items()):
            was = probe.port
            ok = self._attach(graph_ref, probe)
            if ok or was is None:
                continue
            for session in self._sessions:
                if session.graph_ref != graph_ref:
                    continue
                for watch in session.watches.values():
                    if watch.ref == ref:
                        self._send(session, {"t": "gone", "id": watch.id})

    # ------------------------------------------------------------------ timer

    def _ensure_running(self) -> None:
        if self._task is not None and not self._task.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return  # tests drive tick() directly
        self._scheduled = None
        self._task = loop.create_task(self._run())

    async def _run(self) -> None:
        period = self.limits.tick_ms / 1000.0
        try:
            while self._sessions:
                now = self._clock()
                self._scheduled = (self._scheduled or now) + period
                await asyncio.sleep(max(0.0, self._scheduled - now))
                self.tick(self._clock())
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("inspector tick failed")

    def tick(self, now: float) -> None:
        """One scheduling round (also callable from tests with a fake clock)."""
        dt = 0.0 if self._last_tick is None else max(0.0, now - self._last_tick)
        self._last_tick = now
        lag = 0.0 if self._scheduled is None else max(0.0, now - self._scheduled)
        self._update_lag(now, lag)

        if not self.paused and now - self._last_resolve >= 0.5:
            self._last_resolve = now
            self._reresolve()
        for probe in self._probes.values():
            probe.stamp(now)

        self._total_tokens = min(
            float(self.limits.total_budget_bps), self._total_tokens + self.limits.total_budget_bps * dt
        )
        self._throttled = False
        self._reasons = set()
        if self._cpu_window_start is None:
            self._cpu_window_start = now

        for session in list(self._sessions):
            session.tokens = min(float(self.limits.budget_bps), session.tokens + self.limits.budget_bps * dt)
            if session.client_paused:
                continue
            if now >= session.activity_next and (session.activity or self.paused):
                interval = session.activity_interval * (2.0 if self.paused else 1.0)
                session.activity_next = now + max(interval, 1.0 if self.paused else 0.0)
                self._send_activity(session, now)
            if not self.paused:
                self._send_samples(session, now)

        self._adapt(now)
        self._report_status(now)

    def _update_lag(self, now: float, lag: float) -> None:
        lag_ms = lag * 1000.0
        self._lag_ewma = 0.8 * self._lag_ewma + 0.2 * lag_ms
        self._lag_max = max(lag_ms, self._lag_max * 0.95)
        if lag_ms > self.limits.lag_spike_ms:
            self._spikes = [t for t in self._spikes if now - t < 5.0] + [now]
        if not self.paused:
            if self._lag_ewma > self.limits.lag_pause_ms:
                self._over_since = self._over_since or now
            else:
                self._over_since = None
            sustained = self._over_since is not None and now - self._over_since >= self.limits.lag_pause_hold_s
            if sustained or len(self._spikes) >= 2:
                self._pause(now)
        else:
            if self._lag_ewma < self.limits.lag_resume_ms:
                self._under_since = self._under_since or now
                if now - self._under_since >= self.limits.lag_resume_hold_s:
                    self._resume(now)
            else:
                self._under_since = None

    def _pause(self, now: float) -> None:
        self.paused = True
        self._over_since = None
        self._under_since = None
        self._spikes = []
        for probe in self._probes.values():
            probe.detach()
        logger.warning("inspector paused: event loop lag %.0f ms", self._lag_ewma)

    def _resume(self, now: float, forced: bool = False) -> None:
        self.paused = False
        self._under_since = None
        self.interval_scale = min(16.0, self.interval_scale * 2.0)
        for (graph_ref, _ref), probe in self._probes.items():
            self._attach(graph_ref, probe)
        logger.info("inspector resumed%s", " (by client)" if forced else "")

    # ------------------------------------------------------------------ sending

    def _send(self, session: Session, message: Any) -> None:
        if session.closed:
            return
        try:
            session.send(message)
        except Exception:
            logger.exception("inspector send failed; closing session")
            self.close_session(session)

    def _send_activity(self, session: Session, now: float) -> None:
        rows = []
        full = session.activity_rounds % 5 == 0
        session.activity_rounds += 1
        for pid, ref in session.activity.items():
            probe = self._probes.get((session.graph_ref, ref))
            if probe is None:
                continue
            prev_n, prev_t = session.activity_counts.get(pid, (probe.count, now))
            elapsed = now - prev_t
            hz = (probe.count - prev_n) / elapsed if elapsed > 0 else 0.0
            session.activity_counts[pid] = (probe.count, now)
            dtype, shape, stats, last = None, None, None, None
            if probe.values:
                first = probe.values[0]
                dtype = getattr(first, "dtype", None)
                dtype = dtype.str.lstrip("<>|=") if dtype is not None else None
                shape = list(getattr(first, "shape", ()))
                stats, last = summarize(first, self.limits.stats_max_elements)
            age = None if probe.last_t is None else round(now - probe.last_t, 3)
            row = (pid, probe.count, round(hz, 2), age, dtype, shape, stats, last)
            key = (row[1], row[4], tuple(row[5] or ()), not probe.attached)
            if not full and session.activity_sent.get(pid) == key:
                continue
            session.activity_sent[pid] = key
            rows.append(list(row))
        self._send(session, {"t": "activity", "ts": now, "paused": self.paused, "p": rows})

    def _send_samples(self, session: Session, now: float) -> None:
        if session.inflight and now - session.last_ack > self.limits.ack_timeout_s:
            self._reasons.add("client_slow")
            return
        # A snapshot: sending can close the session, which clears the watches.
        watches = list(session.watches.values())
        count = len(watches)
        if not count:
            return
        start = session.round_robin % count
        session.round_robin += 1
        for k in range(count):
            watch = watches[(start + k) % count]
            if now < watch.next_due:
                continue
            if (
                len(session.inflight) >= self.limits.credit_frames
                or session.inflight_bytes >= self.limits.credit_bytes
            ):
                # Waiting for an ack is normal flow control; report it only
                # when the client has not acknowledged anything for a while.
                if now - session.last_ack > _CLIENT_SLOW_S:
                    self._reasons.add("client_slow")
                break
            probe = self._probes.get((session.graph_ref, watch.ref))
            if probe is None or not probe.attached:
                continue
            if watch.accumulate:
                values = watch.accumulator.take() if watch.accumulator else None
            else:
                values = probe.values if (probe.count != watch.last_count or watch.snapshot) else None
            if values is None:
                watch.next_due = now + watch.interval * self.interval_scale
                continue

            t0 = time.perf_counter()
            try:
                reduced = reduce_values(values, watch.spec)
                session.frame_seq += 1
                watch.sample_seq += 1
                frame = encode_sample(watch.id, session.frame_seq, watch.sample_seq, probe.count,
                                      probe.last_t or now, reduced)
            except Exception as e:
                self._send(session, {"t": "error", "id": watch.id, "code": "encode", "message": str(e)})
                watch.next_due = now + 1.0
                continue
            finally:
                self._cpu += time.perf_counter() - t0

            size = len(frame)
            if size > session.tokens or size > self._total_tokens:
                self._throttled = True
                self._reasons.add("budget")
                session.frame_seq -= 1
                watch.sample_seq -= 1
                break
            session.tokens -= size
            self._total_tokens -= size
            session.inflight.append((session.frame_seq, size))
            session.inflight_bytes += size
            if len(session.inflight) == 1:
                session.last_ack = now
            watch.last_count = probe.count
            watch.snapshot = False
            watch.next_due = now + watch.interval * self.interval_scale
            self._send(session, frame)

    def _adapt(self, now: float) -> None:
        window = now - (self._cpu_window_start or now)
        if window < 1.0:
            return
        ratio = self._cpu / window
        self._cpu, self._cpu_window_start = 0.0, now
        if ratio > self.limits.cpu_target:
            self._reasons.add("cpu")
        if ratio > self.limits.cpu_target or self._throttled:
            self.interval_scale = min(16.0, self.interval_scale * 1.5)
            self._healthy_since = None
        else:
            self._healthy_since = self._healthy_since or now
            if now - self._healthy_since >= 2.0 and self.interval_scale > 1.0:
                self.interval_scale = max(1.0, self.interval_scale / 1.25)

    def _report_status(self, now: float) -> None:
        if self.paused:
            state, reasons = "paused", ["loop_lag"]
        elif self.interval_scale > 1.0 or self._reasons:
            state, reasons = "throttled", sorted(self._reasons) or ["recovering"]
        else:
            state, reasons = "ok", []
        key = (state, tuple(reasons))
        if key == self._state_sent and (state == "ok" or now - self._last_status_t < 1.0):
            return
        self._state_sent = key
        self._last_status_t = now
        message = {
            "t": "status",
            "state": state,
            "reasons": reasons,
            "lag_ms": {"ewma": round(self._lag_ewma, 1), "max": round(self._lag_max, 1)},
            "interval_scale": round(self.interval_scale, 2),
        }
        for session in list(self._sessions):
            self._send(session, message)

