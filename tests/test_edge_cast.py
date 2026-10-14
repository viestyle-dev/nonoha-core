"""Edge value conversion tests.

The cast table gates which connections are allowed; the actual conversion
is materialized on the edge at connect time (make_edge_converter /
make_index_converter in port.py). These tests verify:

- mismatched edges deliver arrays cast to the target dtype
- matched edges keep the exact same code path as before (raw dispatch,
  same array reference — no copy)
- the conversion also applies on the connect-time replay of
  current_values and survives port replacement
- newly forbidden pairs are rejected at connect
"""

import numpy as np
import pytest

from nonoha_core.data_type import DataType, PortValueType
from nonoha_core.node import (
    BaseNode,
    BaseNodeGraph,
    replace_node_input_port,
)
from nonoha_core.nodes.flow_control_nodes import ValuesBranchNode
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort

BOOL = PortValueType(DataType.Bool)
I8 = PortValueType(DataType.Int8)
I16 = PortValueType(DataType.Int16)
I64 = PortValueType(DataType.Int64)
U64 = PortValueType(DataType.Uint64)
F32 = PortValueType(DataType.Float32)
F64 = PortValueType(DataType.Float64)


class SourceNode(BaseNode):
    """Node with a single output port."""

    def __init__(self, name: str, value_type: PortValueType):
        super().__init__(name, "Source")
        self._output = StaticTypeOutputPort("out", [value_type])
        self.outputs[self._output.name] = self._output

    def send(self, data: np.ndarray):
        self._output.dispatch([data])


class SinkNode(BaseNode):
    """Node with a single input port that records received data."""

    def __init__(self, name: str, value_type_list: list[PortValueType]):
        super().__init__(name, "Sink")
        self._input = StaticTypeInputPort("in", value_type_list)
        self._input.subscribe(id(self), self._on_input)
        self.inputs[self._input.name] = self._input
        self.received: list = []

    def _on_input(self, values):
        self.received.append(values)


def _make_graph_with_edge(
    source_type: PortValueType,
    sink_type_list: list[PortValueType],
    target_port_value_name: str = "in",
) -> tuple[BaseNodeGraph, SourceNode, SinkNode]:
    graph = BaseNodeGraph("g", {})
    src = SourceNode("src", source_type)
    snk = SinkNode("snk", sink_type_list)
    graph.add_node(src)
    graph.add_node(snk)
    graph.connect_nodes("src", "out", "snk", target_port_value_name)
    return graph, src, snk


# --- mismatched edges are cast ---


def test_bool_to_i8_edge_casts():
    _, src, snk = _make_graph_with_edge(BOOL, [I8])

    src.send(np.array([True, False]))

    assert len(snk.received) == 1
    got = snk.received[0][0]
    assert got.dtype == np.int8
    assert got.tolist() == [1, 0]


def test_i8_to_i16_edge_casts():
    _, src, snk = _make_graph_with_edge(I8, [I16])

    src.send(np.array([-5, 100], dtype=np.int8))

    got = snk.received[0][0]
    assert got.dtype == np.int16
    assert got.tolist() == [-5, 100]


def test_indexed_edge_casts():
    _, src, snk = _make_graph_with_edge(BOOL, [I8, I8], target_port_value_name="in.0")

    src.send(np.array([True]))

    stored = snk._input.values_store[0]
    assert stored is not None
    assert stored.dtype == np.int8
    assert stored.tolist() == [1]


def test_multi_slot_edge_casts_only_mismatched_slots():
    """Tuple edge where only one slot differs: that slot is cast, the
    matched slots pass through as the same reference (generic path)."""
    u8 = PortValueType(DataType.Uint8)
    graph = BaseNodeGraph("g", {})
    src = SourceNode("src", u8)  # placeholder, replaced below
    # Build 3-slot ports directly: (u8, i64, u8) -> (u8, f64, u8)
    src._output = StaticTypeOutputPort("out", [u8, I64, u8])
    src.outputs = {"out": src._output}
    snk = SinkNode("snk", [u8, F64, u8])
    graph.add_node(src)
    graph.add_node(snk)
    graph.connect_nodes("src", "out", "snk", "in")

    a = np.zeros(4, dtype=np.uint8)
    b = np.zeros(4, dtype=np.int64)
    c = np.zeros(4, dtype=np.uint8)
    src._output.dispatch([a, b, c])

    got = snk.received[0]
    assert got[0] is a          # matched slot: same reference
    assert got[1].dtype == np.float64  # mismatched slot: cast
    assert got[2] is c
    assert len(got) == 3


def test_wider_source_surplus_slots_pass_through():
    """Source wider than target: surplus slots are delivered unchanged."""
    u8 = PortValueType(DataType.Uint8)
    graph = BaseNodeGraph("g", {})
    src = SourceNode("src", u8)
    src._output = StaticTypeOutputPort("out", [BOOL, u8, u8])
    src.outputs = {"out": src._output}
    snk = SinkNode("snk", [I8])  # declares only 1 slot
    graph.add_node(src)
    graph.add_node(snk)
    graph.connect_nodes("src", "out", "snk", "in")

    a = np.array([True])
    b = np.zeros(4, dtype=np.uint8)
    c = np.zeros(4, dtype=np.uint8)
    src._output.dispatch([a, b, c])

    got = snk.received[0]
    assert got[0].dtype == np.int8  # declared slot: cast
    assert got[1] is b              # surplus: same reference
    assert got[2] is c
    assert len(got) == 3


# --- matched edges keep the existing zero-overhead path ---


def test_same_dtype_edge_delivers_same_reference():
    _, src, snk = _make_graph_with_edge(F32, [F32])

    data = np.array([1.5], dtype=np.float32)
    src.send(data)

    assert snk.received[0][0] is data


def test_same_dtype_edge_subscribes_raw_dispatch():
    """Perf regression guard: a matched edge must subscribe the input
    port's dispatch itself, not a wrapper."""
    _, src, snk = _make_graph_with_edge(F32, [F32])

    assert any(cb == snk._input.dispatch for cb in src._output._callback_funcs)


def test_mismatched_edge_subscribes_wrapper():
    _, src, snk = _make_graph_with_edge(BOOL, [I8])

    assert all(cb != snk._input.dispatch for cb in src._output._callback_funcs)


# --- connect-time replay of current_values is cast too ---


def test_replay_casts_on_connect():
    graph = BaseNodeGraph("g", {})
    src = SourceNode("src", BOOL)
    snk = SinkNode("snk", [I8])
    graph.add_node(src)
    graph.add_node(snk)

    # Source fires BEFORE the edge exists; connect must replay converted.
    src.send(np.array([True]))
    graph.connect_nodes("src", "out", "snk", "in")

    assert len(snk.received) == 1
    got = snk.received[0][0]
    assert got.dtype == np.int8
    assert got.tolist() == [1]


def test_replay_casts_on_connect_indexed():
    graph = BaseNodeGraph("g", {})
    src = SourceNode("src", BOOL)
    snk = SinkNode("snk", [I8, I8])
    graph.add_node(src)
    graph.add_node(snk)

    src.send(np.array([True]))
    graph.connect_nodes("src", "out", "snk", "in.0")

    stored = snk._input.values_store[0]
    assert stored is not None
    assert stored.dtype == np.int8


# --- conversion survives port replacement ---


def test_replace_input_port_reapplies_converter():
    _, src, snk = _make_graph_with_edge(BOOL, [I8])

    # Replace the sink input with a different (still connectable) type.
    new_in = StaticTypeInputPort("in", [I16])
    replace_node_input_port(snk, snk._input, new_in, snk._on_input)
    snk._input = new_in

    src.send(np.array([True]))

    got = snk.received[0][0]
    assert got.dtype == np.int16
    assert got.tolist() == [1]


# --- graph boundary edges are cast ---


def test_graph_input_to_node_casts():
    graph = BaseNodeGraph("g", {})
    snk = SinkNode("snk", [I8])
    graph.add_node(snk)

    gin = StaticTypeInputPort("gin", [BOOL])
    graph.add_input_port(gin)
    graph.connect_input_to_node("gin", "snk", "in")

    gin.dispatch([np.array([True])])

    got = snk.received[0][0]
    assert got.dtype == np.int8


def test_node_to_graph_output_casts():
    graph = BaseNodeGraph("g", {})
    src = SourceNode("src", BOOL)
    graph.add_node(src)

    gout = StaticTypeOutputPort("gout", [I8])
    graph.add_output_port(gout)
    graph.connect_node_to_output("src", "out", "gout")

    src.send(np.array([True]))

    assert gout.current_values is not None
    assert gout.current_values[0].dtype == np.int8


# --- newly forbidden pairs are rejected at connect ---


@pytest.mark.parametrize(
    "source_type,sink_type",
    [
        (I64, U64),  # signed -> unsigned
        (F64, F32),  # narrowing float
        (I64, F32),  # precision-losing int -> float
        (F32, BOOL),  # truthiness
    ],
)
def test_forbidden_pairs_raise_on_connect(source_type, sink_type):
    graph = BaseNodeGraph("g", {})
    graph.add_node(SourceNode("src", source_type))
    graph.add_node(SinkNode("snk", [sink_type]))

    with pytest.raises(ValueError, match="not connectable"):
        graph.connect_nodes("src", "out", "snk", "in")


# --- graph-level regression: bool selector into ValuesBranch.index ---


def test_values_branch_bool_index_via_edge():
    """A bool source wired to ValuesBranch.index (i8) must route correctly:
    the edge casts bool -> int8, so no numpy.bool ever reaches the node
    (numpy >= 2.4 forbids numpy.bool as a list index)."""
    graph = BaseNodeGraph("g", {})
    idx_src = SourceNode("idx", BOOL)
    val_src = SourceNode("val", F32)
    vb = ValuesBranchNode("vb")
    graph.add_node(idx_src)
    graph.add_node(val_src)
    graph.add_node(vb)

    graph.connect_nodes("idx", "out", "vb", "index")
    graph.connect_nodes("val", "out", "vb", "values")

    routed: dict[str, list] = {"out_0": [], "out_1": []}
    vb.outputs["out_0"].subscribe(1, lambda v: routed["out_0"].append(v))
    vb.outputs["out_1"].subscribe(2, lambda v: routed["out_1"].append(v))

    idx_src.send(np.array([True]))
    val_src.send(np.array([1.5], dtype=np.float32))

    assert len(routed["out_1"]) == 1
    assert len(routed["out_0"]) == 0
    assert float(routed["out_1"][0][0][0]) == 1.5

    idx_src.send(np.array([False]))
    val_src.send(np.array([2.5], dtype=np.float32))

    assert len(routed["out_0"]) == 1
    assert float(routed["out_0"][0][0][0]) == 2.5
