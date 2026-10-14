from pathlib import Path

import numpy as np

from nonoha_core.node import (
    BaseNode,
    BaseNodeGraph,
    Edge,
    NodeGraphPersist,
    replace_node_input_port,
    replace_node_output_port,
)
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.data_type import DataType, PortValueType, PropertyDataType


def test_node_creation():
    class TestNode(BaseNode):
        def __init__(self, name: str):
            super().__init__(name, "Test")

    node = TestNode("test_node")
    assert node.name == "test_node"


class MockPersist(NodeGraphPersist):
    """Mock persist for testing."""

    def __init__(self):
        self.graph_properties_updates: list[dict[str, PropertyDataType]] = []
        self.node_updates: list[BaseNode] = []

    @property
    def data_dir_path(self) -> Path:
        return Path(".")

    def add_input_port(self, port: StaticTypeInputPort) -> None:
        pass

    def remove_input_port(self, port_name: str) -> None:
        pass

    def add_output_port(self, port: StaticTypeOutputPort) -> None:
        pass

    def remove_output_port(self, port_name: str) -> None:
        pass

    def add_node(self, node: BaseNode) -> None:
        pass

    def remove_node(self, node_name: str) -> None:
        pass

    def update_edges(self, edges: dict[tuple[str, str], Edge]) -> None:
        pass

    def update_node(self, node: BaseNode) -> None:
        self.node_updates.append(node)

    def update_properties(self, node: BaseNode) -> None:
        pass

    def update_graph_properties(self, properties: dict[str, PropertyDataType]) -> None:
        self.graph_properties_updates.append(properties.copy())


def test_nodegraph_set_properties_persists():
    """Test that BaseNodeGraph.set_properties() persists changes."""
    graph = BaseNodeGraph("test_graph", {"key1": "value1", "key2": 100})
    mock_persist = MockPersist()
    graph.set_persist(mock_persist)

    # Update properties
    graph.set_properties({"key1": "updated_value"})

    # Verify persist was called
    assert len(mock_persist.graph_properties_updates) == 1
    assert mock_persist.graph_properties_updates[0] == {
        "key1": "updated_value",
        "key2": 100,
    }

    # Verify graph properties are updated
    assert graph.properties["key1"] == "updated_value"
    assert graph.properties["key2"] == 100


def test_nodegraph_set_properties_without_persist():
    """Test that BaseNodeGraph.set_properties() works without persist."""
    graph = BaseNodeGraph("test_graph", {"key1": "value1"})

    # Should not raise even without persist
    graph.set_properties({"key1": "updated_value"})

    assert graph.properties["key1"] == "updated_value"


def test_nodegraph_set_properties_invalid_key():
    """Test that BaseNodeGraph.set_properties() rejects unknown keys."""
    graph = BaseNodeGraph("test_graph", {"key1": "value1"})
    mock_persist = MockPersist()
    graph.set_persist(mock_persist)

    # Try to set unknown key
    graph.set_properties({"unknown_key": "value"})

    # Persist should NOT be called for invalid key
    assert len(mock_persist.graph_properties_updates) == 0

    # Original properties should be unchanged
    assert graph.properties == {"key1": "value1"}


def test_nodegraph_set_properties_mixed_keys_applies_valid_and_skips_unknown(
    caplog,
):
    """Unknown keys are dropped per-key; valid keys still apply, and the
    notified change set equals the applied change set."""
    graph = BaseNodeGraph("test_graph", {"key1": "value1"})
    mock_persist = MockPersist()
    graph.set_persist(mock_persist)

    received: list[dict[str, PropertyDataType]] = []
    graph.subscribe_properties_changed(
        1, lambda properties: received.append(properties)
    )

    with caplog.at_level("WARNING"):
        graph.set_properties({"key1": "updated_value", "unknown_key": 1})

    assert graph.properties == {"key1": "updated_value"}
    assert received == [{"key1": "updated_value"}]
    assert len(mock_persist.graph_properties_updates) == 1
    assert mock_persist.graph_properties_updates[0] == {"key1": "updated_value"}
    assert any("unknown_key" in r.message for r in caplog.records)


# --- Helpers for port replacement tests ---


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
    """Create a graph with SourceNode→SinkNode connected."""
    graph = BaseNodeGraph("g", {})
    src = SourceNode("src", source_type)
    snk = SinkNode("snk", sink_type_list)
    graph.add_node(src)
    graph.add_node(snk)
    graph.connect_nodes("src", "out", "snk", target_port_value_name)
    return graph, src, snk


# --- replace_node_output_port tests ---


def test_replace_output_port_preserves_compatible_edge():
    """Compatible output port replacement keeps the edge alive."""
    f32 = PortValueType(DataType.Float32)
    graph, src, snk = _make_graph_with_edge(f32, [f32])

    # Replace output with same type
    new_out = StaticTypeOutputPort("out", [f32])
    replace_node_output_port(src, src._output, new_out)
    src._output = new_out

    # Edge should still work
    src.send(np.array([1.0], dtype=np.float32))
    assert len(snk.received) == 1

    # Edge should be valid
    edges = list(graph._edges.values())
    assert len(edges) == 1
    assert edges[0].valid is True


def test_replace_output_port_invalidates_incompatible_edge():
    """Incompatible output port replacement marks the edge invalid."""
    f32 = PortValueType(DataType.Float32)
    graph, src, snk = _make_graph_with_edge(f32, [f32])

    # Replace output with incompatible type (string)
    str_type = PortValueType(DataType.String)
    new_out = StaticTypeOutputPort("out", [str_type])
    replace_node_output_port(src, src._output, new_out)
    src._output = new_out

    # Edge should be invalid
    edges = list(graph._edges.values())
    assert len(edges) == 1
    assert edges[0].valid is False

    # No data should reach sink
    snk.received.clear()
    src._output.dispatch([np.array(["hello"])])
    assert len(snk.received) == 0


def test_replace_output_port_to_graph_output():
    """Output port replacement preserves edge to graph output port."""
    f32 = PortValueType(DataType.Float32)
    graph = BaseNodeGraph("g", {})
    src = SourceNode("src", f32)
    graph.add_node(src)

    graph_out = StaticTypeOutputPort("graph_out", [f32])
    graph.add_output_port(graph_out)
    graph.connect_node_to_output("src", "out", "graph_out")

    # Replace source output with same type
    new_out = StaticTypeOutputPort("out", [f32])
    replace_node_output_port(src, src._output, new_out)
    src._output = new_out

    edges = list(graph._edges.values())
    assert len(edges) == 1
    assert edges[0].valid is True


# --- replace_node_input_port tests ---


def test_replace_input_port_preserves_compatible_edge():
    """Compatible input port replacement keeps the edge alive."""
    f32 = PortValueType(DataType.Float32)
    graph, src, snk = _make_graph_with_edge(f32, [f32])

    # Replace input with same type
    new_in = StaticTypeInputPort("in", [f32])
    replace_node_input_port(snk, snk._input, new_in, snk._on_input)
    snk._input = new_in

    # Edge should still work
    src.send(np.array([2.0], dtype=np.float32))
    assert len(snk.received) == 1

    edges = list(graph._edges.values())
    assert len(edges) == 1
    assert edges[0].valid is True


def test_replace_input_port_invalidates_incompatible_edge():
    """Incompatible input port replacement marks the edge invalid."""
    f32 = PortValueType(DataType.Float32)
    graph, src, snk = _make_graph_with_edge(f32, [f32])

    # Replace input with incompatible type
    str_type = PortValueType(DataType.String)
    new_in = StaticTypeInputPort("in", [str_type])
    replace_node_input_port(snk, snk._input, new_in, snk._on_input)
    snk._input = new_in

    edges = list(graph._edges.values())
    assert len(edges) == 1
    assert edges[0].valid is False

    snk.received.clear()
    src.send(np.array([1.0], dtype=np.float32))
    assert len(snk.received) == 0


def test_replace_input_port_sub_value_edge():
    """Sub-value edge (out→in.0) is preserved after compatible input replace."""
    f32 = PortValueType(DataType.Float32)
    f32_2 = [f32, f32]

    graph, src, snk = _make_graph_with_edge(f32, f32_2, target_port_value_name="in.0")

    # Replace input with same types
    new_in = StaticTypeInputPort("in", f32_2)
    replace_node_input_port(snk, snk._input, new_in, snk._on_input)
    snk._input = new_in

    # Edge should be valid
    edges = list(graph._edges.values())
    assert len(edges) == 1
    assert edges[0].valid is True

    # Sub-value receive stores value at index 0
    src.send(np.array([3.0], dtype=np.float32))
    assert new_in.values_store[0] is not None
    assert float(new_in.values_store[0][0]) == 3.0
