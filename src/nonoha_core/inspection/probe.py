"""Probes: shared, reference-counted subscribers on graph and node ports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from ..node import BaseNodeGraph
from ..port import PortValue, StaticTypePort


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


class Accumulator:
    """Keeps copies of every dispatch since the last sample, up to a byte cap."""

    __slots__ = ("chunks", "nbytes", "cap", "dropped")

    def __init__(self, cap: int):
        self.chunks: list[list[np.ndarray]] = []
        self.nbytes = 0
        self.cap = cap
        self.dropped = 0

    def push(self, values: list[PortValue]):
        copies = [np.array(v, copy=True) for v in values]
        size = sum(int(c.nbytes) for c in copies)
        self.chunks.append(copies)
        self.nbytes += size
        while self.nbytes > self.cap and len(self.chunks) > 1:
            old = self.chunks.pop(0)
            self.nbytes -= sum(int(c.nbytes) for c in old)
            self.dropped += 1

    def take(self) -> list[np.ndarray] | None:
        if not self.chunks:
            return None
        chunks, self.chunks, self.nbytes = self.chunks, [], 0
        slots = len(chunks[0])
        try:
            return [np.concatenate([c[i] for c in chunks], axis=0) for i in range(slots)]
        except ValueError:  # shapes changed between dispatches
            return chunks[-1]


class Probe:
    """Subscribes to one port; shared by every watch and activity entry on it.

    A probe is an ordinary subscriber (callback order is not part of the
    port contract; graphs that need an order use a Sequence node). Its
    callback only records what it sees.
    """

    __slots__ = ("ref", "port", "values", "count", "last_t", "seen_count", "refs", "accumulators", "_key")

    def __init__(self, ref: PortRef, clock: Callable[[], float] | None = None):
        self.ref = ref
        self.port: StaticTypePort | None = None
        self.values: list[PortValue] | None = None
        self.count = 0
        # Time of the last dispatch, stamped by the hub's tick (not per
        # dispatch: the callback stays two attribute writes).
        self.last_t: float | None = None
        self.seen_count = 0
        self.refs = 0
        self.accumulators: list[Accumulator] = []
        self._key = id(self)

    def _on_values(self, values: list[PortValue]):
        self.values = values
        self.count += 1
        if self.accumulators:
            for acc in self.accumulators:
                acc.push(values)

    def stamp(self, now: float) -> None:
        """Called once per tick: date the newest dispatch at tick resolution."""
        if self.count != self.seen_count:
            self.seen_count = self.count
            self.last_t = now

    def attach(self, port: StaticTypePort):
        if self.port is port:
            return
        self.detach()
        self.port = port
        port.subscribe(self._key, self._on_values)
        if self.values is None and port.current_values is not None:
            self.values = port.current_values

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
