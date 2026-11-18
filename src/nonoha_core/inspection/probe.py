"""Probes: shared, reference-counted subscribers on graph and node ports.

A dispatched value is valid during the dispatch only (the sender may write
into the same buffer afterwards), so the inspector never keeps a reference
to it: what it shows is taken during a dispatch. To keep that off the hot
path, a probe takes nothing unless asked: the hub puts the watches and
activity entries that need a sample in ``pending``, and the next dispatch
fills and dates them (a reduced copy for a watch, statistics for activity).
Every other dispatch costs a counter increment and a truth test.

Nodes dispatch on the event loop's thread (other threads hand values over
with ``call_soon_threadsafe``), the thread the hub's timer runs on: a probe
and the hub never run at the same time.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

from ..node import BaseNodeGraph
from ..port import PortValue, StaticTypePort
from .reduce import reduce_values, summarize, type_name_of


@dataclass(frozen=True)
class PortRef:
    """A port addressed by node name ("" for the graph's own ports)."""

    node: str
    direction: str  # "in" or "out"
    port: str

    @classmethod
    def from_op(cls, op: dict) -> "PortRef":
        direction = op.get("dir", "out")
        if direction not in ("in", "out"):
            raise ValueError("dir must be 'in' or 'out'")
        port = op.get("port")
        if not isinstance(port, str) or not port:
            raise ValueError("port is required")
        return cls(str(op.get("node", "")), direction, port)

    def resolve(self, graph: BaseNodeGraph) -> StaticTypePort | None:
        if not self.node:
            ports = graph.inputs if self.direction == "in" else graph.outputs
        else:
            node = graph.get_node(self.node)
            if node is None:
                return None
            ports = node.inputs if self.direction == "in" else node.outputs
        return ports.get(self.port)


def describe_values(values: list[PortValue] | None, max_elements: int) -> tuple[Any, Any, Any, Any]:
    """(type name, shape, stats, last) of a dispatch's first slot, for activity
    rows. The type name is the one ports use ("f32", "str"), as in watch_ack."""
    if not values:
        return None, None, None, None
    first = np.asarray(values[0])
    stats, last = summarize(first, max_elements)
    return type_name_of(first), list(first.shape), stats, last


class Accumulator:
    """The items of every dispatch since the last sample, up to a byte cap.

    Each slot has one ring, allocated when the first dispatch (or a new shape
    or dtype) arrives. A dispatch is copied into it, sliced first when the
    watch slices (the ring holds what will be sent, so the cap counts that);
    nothing is allocated, and the oldest items are overwritten. ``take``
    returns the items in order; a ring that has not wrapped is returned as a
    view (the hub encodes it before the next dispatch). ``gap`` is set when
    items were lost (overwritten, or dropped by a reset).
    """

    __slots__ = ("cap", "slices", "indexes", "rings", "starts", "lengths", "gap")

    def __init__(self, cap: int, slices: list | None = None):
        self.cap = cap
        self.slices = slices or None
        self.indexes: list[tuple] | None = None  # per slot, when the watch slices
        self.rings: list[np.ndarray] | None = None
        self.starts: list[int] = []
        self.lengths: list[int] = []
        self.gap = False

    def _reset(self, values: list[PortValue]) -> None:
        # Cold path: first dispatch, or a slot changed shape or dtype. Every
        # slot holds the same number of items; together they fit the cap (a
        # single dispatch larger than that still fits: the ring grows).
        if any(self.lengths):
            self.gap = True
        slices = self.slices
        indexes = None
        held = []
        if slices:
            indexes = []
            for v in values:
                index: list[slice] = [slice(None)]
                for dim in range(1, v.ndim):
                    s = slices[dim - 1] if dim - 1 < len(slices) else None
                    index.append(slice(*s) if s else slice(None))
                indexes.append(tuple(index))
                held.append(v[tuple(index)] if v.ndim else v.reshape(1))
        else:
            held = [v if v.ndim else v.reshape(1) for v in values]
        self.indexes = indexes
        row_bytes = sum(int(np.prod(v.shape[1:], dtype=np.int64)) * v.dtype.itemsize for v in held) or 1
        rows = max(1, self.cap // row_bytes, max((v.shape[0] for v in held), default=1))
        self.rings = [np.empty((rows, *v.shape[1:]), dtype=v.dtype) for v in held]
        self.starts = [0] * len(held)
        self.lengths = [0] * len(held)

    def push(self, values: list[PortValue]) -> None:
        rings = self.rings
        if rings is None or len(rings) != len(values):
            self._reset(values)
            rings = self.rings
        indexes = self.indexes
        starts, lengths = self.starts, self.lengths
        for i in range(len(values)):
            value = values[i]
            if not value.ndim:
                value = value.reshape(1)  # one item
            elif indexes is not None:
                value = value[indexes[i]]
            ring = rings[i]
            if value.dtype != ring.dtype or value.shape[1:] != ring.shape[1:]:
                self._reset(values)
                self.push(values)
                return
            rows = value.shape[0]
            size = ring.shape[0]
            if rows >= size:
                if rows > size:
                    self._reset(values)
                    self.push(values)
                    return
                np.copyto(ring, value)
                if lengths[i]:
                    self.gap = True
                starts[i] = 0
                lengths[i] = size
                continue
            pos = (starts[i] + lengths[i]) % size
            first = size - pos
            if rows <= first:
                np.copyto(ring[pos:pos + rows], value)
            else:
                np.copyto(ring[pos:], value[:first])
                np.copyto(ring[:rows - first], value[first:])
            length = lengths[i] + rows
            if length > size:
                starts[i] = (starts[i] + length - size) % size
                length = size
                self.gap = True
            lengths[i] = length

    def take(self) -> list[np.ndarray] | None:
        rings = self.rings
        if rings is None or not self.lengths or self.lengths[0] == 0:
            return None
        out = []
        for i in range(len(rings)):
            ring, start, length = rings[i], self.starts[i], self.lengths[i]
            end = start + length
            if end <= ring.shape[0]:
                out.append(ring[start:end])
            else:
                out.append(np.concatenate((ring[start:], ring[:end - ring.shape[0]])))
            self.starts[i] = 0
            self.lengths[i] = 0
        return out

    def clear(self) -> None:
        """Forget the items held (a paused session); the next ones are a gap."""
        for i in range(len(self.lengths)):
            self.starts[i] = 0
            self.lengths[i] = 0
        self.gap = True


class Probe:
    """Subscribes to one port; shared by every watch and activity entry on it.

    A probe is an ordinary subscriber (callback order is not part of the
    port contract; graphs that need an order use a Sequence node). Its
    callback never raises: a failure is recorded on the entry it was taken
    for and reported by the hub.
    """

    __slots__ = ("ref", "port", "count", "last_t", "seen_count", "refs", "accumulators", "pending", "cpu", "clock", "_key")

    def __init__(self, ref: PortRef, clock: Callable[[], float] = time.monotonic):
        self.ref = ref
        self.port: StaticTypePort | None = None
        self.count = 0
        # Time of the last dispatch, stamped by the hub's tick (not per
        # dispatch: the callback stays cheap).
        self.last_t: float | None = None
        self.seen_count = 0
        self.refs = 0
        self.accumulators: list[Accumulator] = []
        # Watches and activity entries waiting for the next dispatch
        self.pending: list[Any] = []
        # Seconds spent taking samples since the hub last collected it
        self.cpu = 0.0
        # The hub's clock: when a sample was taken
        self.clock = clock
        self._key = id(self)

    def _on_values(self, values: list[PortValue]):
        self.count += 1
        if self.pending:
            t0 = time.perf_counter()
            count = self.count
            taken = self.clock()
            for entry in self.pending:
                try:
                    spec = entry.spec
                    if spec is not None:  # a watch: its reduced, owned copy
                        entry.captured = reduce_values(values, spec)
                    else:  # an activity entry: statistics only
                        entry.captured = describe_values(values, entry.max_elements)
                    entry.captured_error = None
                except Exception as e:
                    entry.captured = None
                    entry.captured_error = str(e)
                entry.captured_count = count
                entry.captured_t = taken
                entry.armed = False
            self.pending.clear()
            self.cpu += time.perf_counter() - t0
        if self.accumulators:
            try:
                for acc in self.accumulators:
                    acc.push(values)
            except Exception:
                # A value an accumulator cannot hold: start over rather than
                # raise into the sender's dispatch
                for acc in self.accumulators:
                    acc.rings = None

    def arm(self, entry: Any) -> None:
        """Take a sample for ``entry`` at the next dispatch (cold paths; the
        tick does the same inline)."""
        if not entry.armed:
            entry.armed = True
            self.pending.append(entry)

    def disarm(self, entry: Any) -> None:
        if entry.armed:
            entry.armed = False
            self.pending = [e for e in self.pending if e is not entry]

    def attach(self, port: StaticTypePort) -> bool:
        """Subscribe to ``port``; True when it is a different port than before."""
        if self.port is port:
            return False
        self.detach()
        self.port = port
        port.subscribe(self._key, self._on_values)
        return True

    def detach(self):
        if self.port is not None:
            self.port.unsubscribe(self._key)
            self.port = None

    @property
    def key(self) -> int:
        return self._key

    @property
    def attached(self) -> bool:
        return self.port is not None
