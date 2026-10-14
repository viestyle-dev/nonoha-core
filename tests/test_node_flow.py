import pytest

from nonoha_core.node import BaseNode, BaseNodeFlow, BaseNodeGraph


class TrackingNode(BaseNode):
    """Node that records finalize calls."""

    def __init__(self, name: str):
        super().__init__(name, "Tracking")
        self.finalized = False

    def finalize(self):
        self.finalized = True


def make_graph(name: str) -> tuple[BaseNodeGraph, TrackingNode]:
    graph = BaseNodeGraph(name, {})
    node = TrackingNode(f"{name}_node")
    graph.add_node(node)
    return graph, node


def test_add_and_get_graph():
    flow = BaseNodeFlow()
    graph, _ = make_graph("g1")

    flow.add_graph(graph)

    assert flow.get_graph("g1") is graph
    assert flow.get_graph("unknown") is None
    assert list(flow.graph_names) == ["g1"]
    assert flow.graphs == {"g1": graph}


def test_add_graph_sets_parent_flow():
    flow = BaseNodeFlow()
    graph, _ = make_graph("g1")

    flow.add_graph(graph)

    assert graph.parent_flow is flow


def test_add_graph_duplicate_name_raises():
    flow = BaseNodeFlow()
    graph1, _ = make_graph("g1")
    graph2, _ = make_graph("g1")

    flow.add_graph(graph1)
    with pytest.raises(ValueError):
        flow.add_graph(graph2)


def test_graph_names_preserve_insertion_order():
    flow = BaseNodeFlow()
    for name in ["b", "a", "c"]:
        graph, _ = make_graph(name)
        flow.add_graph(graph)

    assert list(flow.graph_names) == ["b", "a", "c"]


def test_remove_graph_finalizes_and_clears_parent_flow():
    flow = BaseNodeFlow()
    graph, node = make_graph("g1")
    flow.add_graph(graph)

    removed = flow.remove_graph("g1")

    assert removed is graph
    assert node.finalized
    assert graph.parent_flow is None
    assert flow.get_graph("g1") is None


def test_remove_graph_unknown_returns_none():
    flow = BaseNodeFlow()
    assert flow.remove_graph("unknown") is None


def test_finalize_finalizes_all_graphs():
    flow = BaseNodeFlow()
    graph1, node1 = make_graph("g1")
    graph2, node2 = make_graph("g2")
    flow.add_graph(graph1)
    flow.add_graph(graph2)

    flow.finalize()

    assert node1.finalized
    assert node2.finalized
