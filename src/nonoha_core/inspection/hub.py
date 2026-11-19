"""Inspector hub: sessions, watches and activity on top of port subscriptions.

Transport-agnostic and asyncio-only. A host (a web server, an embedded
bridge, a test) opens a session per client with a ``send`` callable that
must not block and an ``on_close`` callable (told when the hub ends the
session, so the host ends the connection), feeds control operations (plain
dicts) and acknowledgements in, and runs the hub's timer on its event loop.
Nothing is observed until a client asks for it, and nothing runs when no
session is open. An engine has one Inspector: its lag pause and interval
scale concern the whole engine (the event loop and the CPU are shared), its
credits and budgets each session.

Two kinds of watches:

- ``LatestWatch``: a sample is taken during a dispatch. A watch is ``IDLE``,
  ``ASKED`` (in its probe's ``pending``: the next dispatch is taken) or
  ``HELD`` (a sample waits to be sent). The tick before a sample is due it is
  asked, when it can be sent (credit left, budget for a frame like the last);
  when due, what it holds is sent, or dropped when it was taken longer than
  an interval ago. A dispatched value is valid during the dispatch only (the
  sender may reuse its buffer), so a sample is always what was dispatched.
  A new watch (and a snapshot) holds the port's current value at once: a
  sender that writes into its buffer between dispatches can make that one
  sample a mix of two dispatches.
- ``SinceWatch`` (``batch: "since"``): an accumulator gathers every item;
  when due, they are reduced and sent.

Safety rules (so inspection never takes the process down):
- latest value wins; no per-dispatch queue (except bounded accumulators)
- nothing is copied on a dispatch unless a sample was asked for
- at most ``credit_frames`` / ``credit_bytes`` unacknowledged per session; a
  client that acknowledges nothing for ``ack_timeout_s`` is disconnected
  (its frames are never forgotten: the host's queue stays bounded)
- a token bucket per session and one across sessions cap bytes per second;
  a frame that does not fit waits and the smaller ones go on
- intervals widen when sampling takes too much CPU
- when the event loop lags, all probes detach until it recovers; only an
  explicit ``force_resume`` ends that early

Operations: ``hello``, ``ack``, ``watch``, ``unwatch``, ``snapshot``,
``activity``, ``pause`` / ``resume`` (this session's stream, e.g. a hidden
tab: nothing is taken or gathered for it meanwhile), ``force_resume`` (end
the engine-wide lag pause now), ``close``. Sending ``watch`` again for the
same id, port and reduction only changes its interval.

Errors are ``{"t": "error", "id", "code", "message"}``: ``bad_request``, and
for a watch that sends nothing ``too_large`` (a sample does not fit
``max_bytes`` even reduced) or ``encode``; a watch's problem is sent once,
until a frame goes out again.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from math import exp
from typing import Any, Callable, ClassVar

from ..error_log import ErrorLog
from ..node import BaseNodeGraph
from ..port import StaticTypePort
from .frames import encode_sample
from .probe import ASKED, HELD, IDLE, Accumulator, Probe, PortRef, describe_values
from .reduce import FLAG_GAP, Reduced, ReduceSpec, reduce_values

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = 1
_CLIENT_SLOW_S = 1.0  # no ack for this long while the credit window is full
_WATCH_ID_MAX = 0xFFFF  # frames carry the watch id as u16

# A port's rate: dispatches over the observed intervals, averaged over about a
# second. The average is weighted by time (ticks that see one dispatch and
# ticks that see several average to the true rate) and normalized by the weight
# so far (while it covers less than a second, it reads count / time). A port
# stops when no dispatch came for two of its periods, within [_STOP_MIN_S,
# _STOP_MAX_S]: the floor keeps a short stall of the engine from stopping a
# fast port. After a stop, the first dispatch has no rate yet and the second
# one gives it; a dispatch more than _STOP_MAX_S after the previous one counts
# as a first one again.
_RATE_TAU_S = 1.0
_STOP_PERIODS = 2.0
_STOP_MIN_S = 1.0
_STOP_MAX_S = 10.0


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


class _Bucket:
    """Bytes that may still be sent: refilled at ``rate`` per second, holding
    at most one second's worth. A frame larger than the bucket goes out when
    it is full (on credit); the next ones wait until that is paid back."""

    __slots__ = ("rate", "tokens")

    def __init__(self, rate: int):
        self.rate = float(rate)
        self.tokens = float(rate)

    def refill(self, dt: float) -> None:
        tokens = self.tokens + self.rate * dt
        self.tokens = tokens if tokens < self.rate else self.rate

    def allows(self, cost: float) -> bool:
        return self.tokens >= cost or self.tokens >= self.rate

    def spend(self, size: int) -> None:
        self.tokens -= size


@dataclass(eq=False)
class LatestWatch:
    """Samples taken during a dispatch: the latest value (or its last items)."""

    id: int
    ref: PortRef
    interval: float  # seconds
    spec: ReduceSpec
    probe: Probe  # kept while the watch exists (it holds a reference)
    next_due: float = 0.0
    sample_seq: int = 0
    last_size: int = 0  # bytes of the last frame: what the next one is expected to cost
    reported: str | None = None  # the problem last reported, until a frame goes out
    # Taking a sample (IDLE / ASKED / HELD); the probe fills these during a dispatch
    state: int = IDLE
    captured: Reduced | None = None
    captured_count: int = -1
    captured_t: float = 0.0
    captured_error: str | None = None


@dataclass(eq=False)
class SinceWatch:
    """Every item since the last sample, gathered by an accumulator."""

    id: int
    ref: PortRef
    interval: float  # seconds
    spec: ReduceSpec
    probe: Probe
    accumulator: Accumulator
    take_spec: ReduceSpec  # how the gathered items are reduced (the accumulator sliced them already)
    next_due: float = 0.0
    sample_seq: int = 0
    last_size: int = 0
    reported: str | None = None


@dataclass(eq=False)
class ActivityEntry:
    ref: PortRef
    max_elements: int
    probe: Probe
    sent_key: tuple | None = None
    # Taking statistics (IDLE / ASKED / HELD); the probe fills these during a dispatch
    state: int = IDLE
    captured: Any = None  # (type name, shape, stats, last)
    captured_count: int = -1
    captured_t: float = 0.0
    captured_error: str | None = None
    spec: ClassVar[None] = None  # tells the probe: statistics, not a reduced copy


@dataclass(eq=False)
class Session:
    graph_ref: Any
    send: Callable[[Any], None]
    on_close: Callable[[], None] | None
    bucket: _Bucket
    credit_frames: int
    credit_bytes: int
    watches: dict[int, LatestWatch | SinceWatch] = field(default_factory=dict)
    # The watches by kind, as tuples: iterated every tick without a copy
    latest: tuple[LatestWatch, ...] = ()
    since: tuple[SinceWatch, ...] = ()
    activity: dict[int, ActivityEntry] = field(default_factory=dict)
    activity_interval: float = 0.5
    activity_next: float = 0.0
    activity_rounds: int = 0
    activity_asked: bool = False  # the probes were asked for the next round
    frame_seq: int = 0
    inflight: deque[tuple[int, int]] = field(default_factory=deque)  # (frame_seq, bytes), oldest first
    inflight_bytes: int = 0
    last_ack: float = 0.0
    client_paused: bool = False
    closed: bool = False
    round_robin: int = 0

    def has_credit(self) -> bool:
        return len(self.inflight) < self.credit_frames and self.inflight_bytes < self.credit_bytes

    def index_watches(self) -> None:
        """Rebuild the per-kind tuples after the watches changed."""
        self.latest = tuple(w for w in self.watches.values() if type(w) is LatestWatch)
        self.since = tuple(w for w in self.watches.values() if type(w) is SinceWatch)

    def pause(self) -> None:
        """This session's stream stops (e.g. its tab is hidden): nothing is
        taken or gathered for it meanwhile."""
        if self.client_paused:
            return
        self.client_paused = True
        for watch in self.latest:
            watch.probe.forget(watch)
        for watch in self.since:
            if watch.accumulator in watch.probe.accumulators:
                watch.probe.accumulators.remove(watch.accumulator)
        for entry in self.activity.values():
            entry.probe.forget(entry)
        self.activity_asked = False

    def resume(self) -> None:
        if not self.client_paused:
            return
        self.client_paused = False
        for watch in self.since:
            watch.accumulator.clear()  # items from before the pause are not joined to new ones
            watch.probe.accumulators.append(watch.accumulator)
        for watch in self.watches.values():
            watch.next_due = 0.0


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
        # The same sessions as a tuple: iterated every tick without a copy,
        # and safe when a send closes a session meanwhile
        self._session_list: tuple[Session, ...] = ()
        self._probes: dict[tuple[Any, PortRef], Probe] = {}
        # The port each probe's watches were last told about (watch_ack/gone)
        self._announced: dict[tuple[Any, PortRef], StaticTypePort | None] = {}
        self._task: asyncio.Task | None = None
        self._errors = ErrorLog(logger)
        self._reasons: set[str] = set()
        self._reset_engine_state()

    def _reset_engine_state(self) -> None:
        """The engine-wide state as it is while no session is open (cold path)."""
        self._bucket = _Bucket(self.limits.total_budget_bps)
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
        self._reasons.clear()
        # Why sampling was limited in the last complete second: reported as
        # the status (per window, not per tick, so it does not flap)
        self._window_reasons: tuple[str, ...] = ()
        self._state_sent: tuple | None = None
        self._last_status_t = 0.0
        self._last_resolve = 0.0

    # ------------------------------------------------------------------ sessions

    @property
    def sessions(self) -> list[Session]:
        return list(self._sessions)

    def open_session(
        self, graph_ref: Any, send: Callable[[Any], None], on_close: Callable[[], None] | None = None
    ) -> Session:
        """A new session; already closed when the hello could not be sent.
        ``on_close`` is called whenever the session ends (also when the hub
        ends it: a client that stopped reading or acknowledging)."""
        limits = self.limits
        if len(self._sessions) >= limits.max_sessions:
            raise InspectorFull(f"at most {limits.max_sessions} inspector sessions")
        session = Session(
            graph_ref, send, on_close, _Bucket(limits.budget_bps), limits.credit_frames, limits.credit_bytes,
            last_ack=self._clock(),
        )
        self._sessions.append(session)
        self._session_list = tuple(self._sessions)
        self._send(session, {
            "t": "hello",
            "protocol": PROTOCOL_VERSION,
            "limits": limits.public(),
            "plugins": self._plugins,
        })
        if not session.closed:
            self._ensure_running()
        return session

    def close_session(self, session: Session) -> None:
        if session.closed:
            return
        session.closed = True
        for watch in session.watches.values():
            self._release(session.graph_ref, watch)
        for entry in session.activity.values():
            self._release(session.graph_ref, entry)
        session.watches.clear()
        session.index_watches()
        session.activity.clear()
        if session in self._sessions:
            self._sessions.remove(session)
            self._session_list = tuple(self._sessions)
        if not self._sessions:
            if self._task is not None:
                self._task.cancel()
                self._task = None
            self._reset_engine_state()  # a later session starts fresh (not paused, scale 1)
        if session.on_close is not None:
            try:
                session.on_close()
            except Exception:
                logger.exception("inspector session close callback failed")

    def close(self) -> None:
        for session in self._session_list:
            self.close_session(session)

    # ------------------------------------------------------------------ control

    def handle(self, session: Session, op: dict) -> None:
        """Apply one control operation; errors are reported to the client.
        Operations on a closed session are ignored."""
        if session.closed:
            return
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
                self._snapshot(session, int(op["id"]))
            elif kind == "pause":
                session.pause()
            elif kind == "resume":
                session.resume()  # the engine-wide lag pause ends by itself or by force_resume
            elif kind == "force_resume":
                if self.paused:
                    self._resume(self._clock(), forced=True)
            elif kind == "close":
                self.close_session(session)
            else:
                raise ValueError(f"unknown op {kind!r}")
        except (ValueError, KeyError, TypeError, OverflowError) as e:
            self._send(session, {"t": "error", "id": op.get("id"), "code": "bad_request", "message": str(e)})

    def reject(self, session: Session, code: str, message: str) -> None:
        """Answer a message the host could not read (e.g. not JSON)."""
        self._send(session, {"t": "error", "id": None, "code": code, "message": message})

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
        for pid, entry in list(session.activity.items()):
            if wanted.get(pid) != entry.ref:
                self._release(session.graph_ref, entry)
                del session.activity[pid]
        now = self._clock()
        max_elements = self.limits.stats_max_elements
        for pid, ref in wanted.items():
            if pid in session.activity:
                continue
            probe, port = self._acquire(session.graph_ref, ref)
            entry = ActivityEntry(ref, max_elements, probe)
            # The port's current value, so a row shows before the next dispatch
            current = port.current_values if port is not None else None
            if current is not None:
                try:
                    entry.captured = describe_values(current, max_elements)
                    entry.captured_count = probe.count
                    entry.captured_t = now
                except Exception as e:
                    entry.captured_error = str(e)
            if not session.client_paused:
                probe.ask(entry)
            session.activity[pid] = entry
        interval = float(op.get("interval_ms", self.limits.activity_interval_ms)) / 1000.0
        session.activity_interval = max(self.limits.min_interval_ms / 1000.0, interval)
        session.activity_next = 0.0
        session.activity_rounds = 0

    def _watch(self, session: Session, op: dict) -> None:
        wid = int(op["id"])
        if not 0 <= wid <= _WATCH_ID_MAX:
            raise ValueError(f"id must be 0..{_WATCH_ID_MAX} (frames carry it as u16)")
        ref = PortRef.from_op(op)
        if wid not in session.watches and len(session.watches) >= self.limits.max_watches:
            raise ValueError(f"at most {self.limits.max_watches} watches")
        max_bytes = int(op.get("max_bytes", self.limits.default_max_bytes))
        max_bytes = max(1024, min(self.limits.hard_max_bytes, max_bytes))
        interval = float(op.get("interval_ms", self.limits.default_interval_ms)) / 1000.0
        interval = max(self.limits.min_interval_ms / 1000.0, interval)
        since = op.get("batch") == "since"
        spec = ReduceSpec.from_op({**op, "batch": "all" if since else op.get("batch", "last")}, max_bytes)

        old = session.watches.get(wid)
        if old is not None:
            if old.ref == ref and old.spec == spec and (type(old) is SinceWatch) == since:
                # Only the interval changed (a subscriber came or went): the
                # watch keeps its schedule and its gathered items
                old.interval = interval
                return
            del session.watches[wid]
            self._release(session.graph_ref, old)
        probe, port = self._acquire(session.graph_ref, ref)
        if since:
            take_spec = ReduceSpec(batch="all", auto_stride=spec.auto_stride, cast=spec.cast, max_bytes=max_bytes)
            watch = SinceWatch(wid, ref, interval, spec, probe, Accumulator(max_bytes, spec.slices), take_spec)
            if not session.client_paused:
                probe.accumulators.append(watch.accumulator)
        else:
            watch = LatestWatch(wid, ref, interval, spec, probe)
        session.watches[wid] = watch
        session.index_watches()

        # Resolved even while paused (the probe is detached then), so a watch
        # made during a pause gets its types, not a false "gone"
        self._announced[(session.graph_ref, ref)] = port
        if port is None:
            self._send(session, {"t": "gone", "id": wid})
            return
        if not since and not session.client_paused:
            self._hold_current(watch, port)
        self._send(session, self._watch_ack(watch, port))

    def _unwatch(self, session: Session, wid: int) -> None:
        watch = session.watches.pop(wid, None)
        if watch is not None:
            session.index_watches()
            self._release(session.graph_ref, watch)

    def _snapshot(self, session: Session, wid: int) -> None:
        """Send a watch's sample at the next tick, even without a new dispatch."""
        watch = session.watches.get(wid)
        if watch is None:
            return
        watch.next_due = 0.0
        if type(watch) is LatestWatch and not session.client_paused:
            self._hold_current(watch)

    @staticmethod
    def _watch_ack(watch: LatestWatch | SinceWatch, port: StaticTypePort) -> dict:
        current = port.current_values
        return {
            "t": "watch_ack",
            "id": watch.id,
            "types": [vt.name for vt in port.value_type_list],
            "shape": [list(v.shape) for v in current] if current is not None else None,
        }

    def _hold_current(self, watch: LatestWatch, port: StaticTypePort | None = None) -> None:
        """The port's current value becomes the watch's sample now (a new
        watch, a snapshot); without one, the next dispatch is asked for."""
        probe = watch.probe
        port = port or probe.port
        current = port.current_values if port is not None else None
        if current is None:
            probe.ask(watch)
            return
        probe.forget(watch)  # this value is the sample, not the next dispatch
        try:
            watch.captured = reduce_values(current, watch.spec)
            watch.captured_error = None
        except Exception as e:
            watch.captured_error = str(e)
        watch.captured_count = probe.count
        watch.captured_t = self._clock()
        watch.state = HELD

    # ------------------------------------------------------------------ probes

    def _acquire(self, graph_ref: Any, ref: PortRef) -> tuple[Probe, StaticTypePort | None]:
        """The probe for ``ref`` (one more user) and the port it addresses,
        resolved even when the probe is detached (paused)."""
        key = (graph_ref, ref)
        probe = self._probes.get(key)
        if probe is None:
            probe = Probe(ref, self._clock)
            self._probes[key] = probe
            if not self.paused:
                self._attach(graph_ref, probe)
        probe.refs += 1
        port = probe.port
        if port is None:
            graph = self._resolve(graph_ref)
            port = ref.resolve(graph) if graph is not None else None
        return probe, port

    def _release(self, graph_ref: Any, entry: LatestWatch | SinceWatch | ActivityEntry) -> None:
        key = (graph_ref, entry.ref)
        probe = self._probes.get(key)
        if probe is None:
            return
        if type(entry) is SinceWatch:
            if entry.accumulator in probe.accumulators:
                probe.accumulators.remove(entry.accumulator)
        else:
            probe.forget(entry)
        probe.refs -= 1
        if probe.refs <= 0:
            probe.detach()
            del self._probes[key]
            self._announced.pop(key, None)

    def _attach(self, graph_ref: Any, probe: Probe) -> None:
        graph = self._resolve(graph_ref)
        port = probe.ref.resolve(graph) if graph is not None else None
        if port is None:
            probe.detach()
        else:
            probe.attach(port)

    def _announce(self, graph_ref: Any, probe: Probe) -> None:
        """Tell the watches of ``probe`` when its port is gone or is another
        port now (removed, replaced, re-created): a new watch_ack or "gone"."""
        key = (graph_ref, probe.ref)
        port = probe.port
        if self._announced.get(key) is port:
            return
        self._announced[key] = port
        ref = probe.ref
        for session in self._session_list:
            if session.closed or session.graph_ref != graph_ref:
                continue
            for watch in session.watches.values():
                if watch.ref == ref:
                    self._send(session, {"t": "gone", "id": watch.id} if port is None else self._watch_ack(watch, port))

    def _reresolve(self) -> None:
        """Follow replaced ports and report removed ones (ports change at runtime)."""
        for key, probe in list(self._probes.items()):
            if self._probes.get(key) is not probe:
                continue  # released meanwhile (a send closed its session)
            self._attach(key[0], probe)
            self._announce(key[0], probe)

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
                due = (self._scheduled or now) + period
                if due < now:
                    # Behind schedule (the loop stalled): start over from now
                    # instead of catching up with a burst of ticks. The stall
                    # was measured once, as the lag of the late tick.
                    due = now
                self._scheduled = due
                await asyncio.sleep(due - now)
                try:
                    self.tick(self._clock())
                except Exception:
                    self._errors.exception("inspector tick failed")
        except asyncio.CancelledError:
            pass

    def tick(self, now: float) -> None:
        """One scheduling round (also callable from tests with a fake clock)."""
        dt = 0.0 if self._last_tick is None else max(0.0, now - self._last_tick)
        self._last_tick = now
        lag = 0.0 if self._scheduled is None else max(0.0, now - self._scheduled)
        self._update_lag(now, lag)

        if not self.paused and now - self._last_resolve >= 0.5:
            self._last_resolve = now
            self._reresolve()
        cpu = 0.0
        for probe in self._probes.values():
            count = probe.count
            if count != probe.seen_count:  # date the newest dispatch, at tick resolution
                last_t = probe.last_t
                if last_t is None or now - last_t > probe.stop_after:
                    probe.rate = probe.rate_weight = 0.0  # the first dispatch after a stop: no rate yet
                    probe.stop_after = _STOP_MAX_S
                elif now > last_t:
                    gap = now - last_t
                    a = 1.0 - exp(-gap / _RATE_TAU_S)
                    weight = probe.rate_weight
                    new_weight = weight + a * (1.0 - weight)
                    rate = (probe.rate * weight * (1.0 - a) + a * (count - probe.seen_count) / gap) / new_weight
                    probe.rate = rate
                    probe.rate_weight = new_weight
                    probe.stop_after = min(max(_STOP_PERIODS / rate, _STOP_MIN_S), _STOP_MAX_S)
                probe.seen_count = count
                probe.last_t = now
            if probe.cpu:
                cpu += probe.cpu
                probe.cpu = 0.0
        self._cpu += cpu  # time spent taking samples during dispatches
        self._bucket.refill(dt)
        if self._cpu_window_start is None:
            self._cpu_window_start = now

        for session in self._session_list:
            if session.closed:
                continue
            session.bucket.refill(dt)
            if session.client_paused:
                continue
            if session.activity or self.paused:
                self._activity(session, now)
            if not self.paused:
                self._send_samples(session, now)
        if not self._sessions:
            return  # the last session ended during this tick: the state was reset

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
        for key, probe in list(self._probes.items()):
            if self._probes.get(key) is not probe:
                continue
            for accumulator in probe.accumulators:
                accumulator.gap = True  # nothing was gathered while detached
            self._attach(key[0], probe)
            self._announce(key[0], probe)
        logger.info("inspector resumed%s", " (forced by a client)" if forced else "")

    # ------------------------------------------------------------------ sending

    def _send(self, session: Session, message: Any) -> None:
        if session.closed:
            return
        try:
            session.send(message)
        except Exception:
            logger.exception("inspector send failed; closing session")
            self.close_session(session)

    def _activity(self, session: Session, now: float) -> None:
        """One session's activity: the probes are asked a tick before a round
        (a row shows a recent value at no cost between rounds), and the tick
        nearest to the round reports it (ticks jitter)."""
        period = self.limits.tick_ms / 1000.0
        round_at = session.activity_next - period * 0.5
        if not session.activity_asked and now >= round_at - period:
            session.activity_asked = True
            for entry in session.activity.values():
                if entry.state != ASKED:
                    entry.state = ASKED
                    entry.probe.pending.append(entry)
        if now < round_at:
            return
        interval = session.activity_interval * self.interval_scale * (2.0 if self.paused else 1.0)
        session.activity_next = now + max(interval, 1.0 if self.paused else 0.0)
        self._send_activity(session, now)

    def _send_activity(self, session: Session, now: float) -> None:
        rows = []
        full = session.activity_rounds % 5 == 0
        session.activity_rounds += 1
        session.activity_asked = False
        paused = self.paused
        for pid, entry in session.activity.items():
            probe = entry.probe
            count = probe.count
            last_t = probe.last_t
            age = None if last_t is None else now - last_t
            # 0: stopped, or no rate yet (see _RATE_TAU_S)
            hz = probe.rate if age is not None and age <= probe.stop_after else 0.0
            captured = entry.captured
            if captured is not None:
                dtype, shape, stats, last = captured
            else:
                dtype = shape = stats = last = None
            # A port that stops dispatching changes the key once (hz 0): the
            # row shows it at once, not at the next full round
            key = (count, dtype, tuple(shape or ()), probe.port is None, hz == 0.0)
            if not full and entry.sent_key == key:
                continue  # unchanged: no row
            entry.sent_key = key
            rows.append([pid, count, round(hz, 2), None if age is None else round(age, 3), dtype, shape, stats, last])
        self._send(session, {"t": "activity", "ts": now, "paused": paused, "p": rows})

    def _send_samples(self, session: Session, now: float) -> None:
        limits = self.limits
        if session.inflight and now - session.last_ack > limits.ack_timeout_s:
            # The client acknowledged nothing for a long time: it is gone or
            # stuck. Its frames are never forgotten (the host's queue would
            # grow without bound); the session ends, and a live client
            # reconnects and watches again.
            logger.warning("inspector: no acknowledgement for %.1f s; ending the session", now - session.last_ack)
            self.close_session(session)
            return
        if not session.has_credit():
            # Waiting for an ack is normal flow control; for long, the client is slow
            if now - session.last_ack > _CLIENT_SLOW_S:
                self._reasons.add("client_slow")
            return
        scale = self.interval_scale
        period = limits.tick_ms / 1000.0
        half = period * 0.5
        bucket = session.bucket
        total = self._bucket

        # Latest watches: send what is held when due, then ask for the next.
        # The tick nearest to the due time sends (ticks jitter); the one
        # before it asks the probe.
        latest = session.latest
        count = len(latest)
        start = session.round_robin % count if count else 0
        session.round_robin += 1
        for k in range(count):
            watch = latest[(start + k) % count]
            due = watch.next_due - half
            if now < due - period or watch.probe.port is None:
                continue  # not yet, or detached (paused, the port gone)
            if watch.state == HELD and now >= due:
                sample = watch.captured
                if watch.captured_error is not None:
                    self._report(session, watch, "encode", watch.captured_error)
                    watch.state, watch.next_due = IDLE, now + 1.0
                elif now - watch.captured_t > watch.interval * scale + period:
                    watch.state = IDLE  # taken too long ago to show now: take another
                elif sample.values is None:
                    self._report(session, watch, "too_large", sample.too_large)
                    watch.state, watch.next_due = IDLE, now + watch.interval * scale
                elif not session.has_credit():
                    return  # the frames sent this tick used it up
                elif bucket.allows(sample.nbytes) and total.allows(sample.nbytes):
                    self._emit(session, watch, sample, watch.captured_count, watch.captured_t, now)
                    watch.state = IDLE
                else:
                    self._reasons.add("budget")  # waits; smaller frames go on
            if session.closed:
                return  # a send closed it
            if watch.state == IDLE and now >= watch.next_due - half - period and session.has_credit():
                if bucket.allows(watch.last_size):
                    watch.state = ASKED
                    watch.probe.pending.append(watch)
                else:
                    self._reasons.add("budget")

        # Since watches: the items gathered, when due
        for watch in session.since:
            if now < watch.next_due - half or watch.probe.port is None:
                continue
            accumulator = watch.accumulator
            cost = min(accumulator.held_bytes(), watch.take_spec.max_bytes)
            if not cost:
                continue
            if not session.has_credit():
                return  # the frames sent this tick used it up
            if not (bucket.allows(cost) and total.allows(cost)):
                self._reasons.add("budget")  # the items stay gathered
                continue
            t0 = time.perf_counter()
            try:
                sample = reduce_values(accumulator.take(), watch.take_spec, owned=True)
            except Exception as e:
                accumulator.gap = True  # these items are lost
                self._report(session, watch, "encode", str(e))
                watch.next_due = now + 1.0
                continue
            finally:
                self._cpu += time.perf_counter() - t0
            if sample.values is None:
                accumulator.gap = True  # these items are lost
                self._report(session, watch, "too_large", sample.too_large)
                watch.next_due = now + watch.interval * scale
                continue
            if accumulator.gap:
                sample.flags |= FLAG_GAP
                accumulator.gap = False
            self._emit(session, watch, sample, watch.probe.count, watch.probe.last_t or now, now)
            if session.closed:
                return

    def _emit(
        self, session: Session, watch: LatestWatch | SinceWatch, sample: Reduced, dispatch_count: int, t: float,
        now: float,
    ) -> None:
        """Encode one sample and send it, counted against the session's
        credit and both buckets."""
        t0 = time.perf_counter()
        try:
            frame = encode_sample(watch.id, session.frame_seq + 1, watch.sample_seq + 1, dispatch_count, t, sample)
        except Exception as e:
            self._report(session, watch, "encode", str(e))
            watch.next_due = now + 1.0
            return
        finally:
            self._cpu += time.perf_counter() - t0
        size = len(frame)
        session.bucket.spend(size)
        self._bucket.spend(size)
        session.frame_seq += 1
        session.inflight.append((session.frame_seq, size))
        session.inflight_bytes += size
        if len(session.inflight) == 1:
            session.last_ack = now
        watch.sample_seq += 1
        watch.last_size = size
        watch.reported = None
        watch.next_due = now + watch.interval * self.interval_scale
        self._send(session, frame)

    def _report(self, session: Session, watch: LatestWatch | SinceWatch, code: str, message: str | None) -> None:
        """Tell the client why a watch sends nothing: once, until a frame goes out."""
        if watch.reported != code:
            watch.reported = code
            self._send(session, {"t": "error", "id": watch.id, "code": code, "message": message})

    def _adapt(self, now: float) -> None:
        window = now - (self._cpu_window_start or now)
        if window < 1.0:
            return
        ratio = self._cpu / window
        self._cpu, self._cpu_window_start = 0.0, now
        # Only the CPU widens intervals: budgets already pace each session
        if ratio > self.limits.cpu_target:
            self._reasons.add("cpu")
            self.interval_scale = min(16.0, self.interval_scale * 1.5)
            self._healthy_since = None
        else:
            self._healthy_since = self._healthy_since or now
            if now - self._healthy_since >= 2.0 and self.interval_scale > 1.0:
                self.interval_scale = max(1.0, self.interval_scale / 1.25)
        self._window_reasons = tuple(sorted(self._reasons))
        self._reasons.clear()

    def _report_status(self, now: float) -> None:
        if self.paused:
            state = "paused"
        elif self.interval_scale > 1.0 or self._window_reasons:
            state = "throttled"
        else:
            state = "ok"
        sent = self._state_sent
        if state == "ok" and sent is not None and sent[0] == "ok":
            return  # nothing to report (the common case: no allocation)
        if state == "paused":
            reasons: tuple[str, ...] = ("loop_lag",)
        elif state == "throttled":
            reasons = self._window_reasons or ("recovering",)
        else:
            reasons = ()
        key = (state, reasons)
        if key == sent and (state == "ok" or now - self._last_status_t < 1.0):
            return
        self._state_sent = key
        self._last_status_t = now
        message = {
            "t": "status",
            "state": state,
            "reasons": list(reasons),
            "lag_ms": {"ewma": round(self._lag_ewma, 1), "max": round(self._lag_max, 1)},
            "interval_scale": round(self.interval_scale, 2),
        }
        for session in self._session_list:
            self._send(session, message)
