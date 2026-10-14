import numpy as np

from nonoha_core.node import BaseNode, BaseNodeFlow, BaseNodeGraph
from nonoha_core.node_registry import NodeRegistry
from nonoha_core.nodes import register_nodes
from nonoha_core.nodes.graph_nodes import (
    GraphLoadedNode,
    GraphPropertiesChangedNode,
    GraphProxyNode,
)
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.data_type import DataType, PortValueType


class DoubleNode(BaseNode):
    """Test node that doubles its input."""

    def __init__(self, name: str):
        super().__init__(name, "Double")
        value_types = [PortValueType(DataType.Float64)]
        input_port = StaticTypeInputPort("value", value_types)
        input_port.subscribe(id(self), self._on_value)
        self.inputs["value"] = input_port
        self._output = StaticTypeOutputPort("result", value_types)
        self.outputs["result"] = self._output

    def _on_value(self, values):
        self._output.dispatch([values[0] * 2.0])


class FlushingGraph(BaseNodeGraph):
    """Engine-like graph whose flush_outputs fires the flush subscribers."""

    def flush_outputs(self):
        for callback in list(self._flush_outputs_callbacks.values()):
            callback()


def make_target_graph(name: str, graph_cls=BaseNodeGraph) -> BaseNodeGraph:
    """Graph with input "in" -> DoubleNode -> output "out"."""
    graph = graph_cls(name, {})
    graph.add_node(DoubleNode("Double_1"))
    value_types = [PortValueType(DataType.Float64)]
    graph.add_input_port(StaticTypeInputPort("in", value_types))
    graph.add_output_port(StaticTypeOutputPort("out", value_types))
    graph.connect_input_to_node("in", "Double_1", "value")
    graph.connect_node_to_output("Double_1", "result", "out")
    return graph


def make_proxy_setup(graph_cls=BaseNodeGraph):
    """Flow with a target graph and a main graph holding a bound proxy.

    Emulates loader order: parent_flow is set on the main graph before it
    is added to the flow, and the proxy binds via set_properties.
    """
    flow = BaseNodeFlow()
    target = make_target_graph("target", graph_cls)
    flow.add_graph(target)

    main = graph_cls("main", {})
    main.set_parent_flow(flow)
    proxy = GraphProxyNode("proxy_1")
    main.add_node(proxy)
    proxy.set_properties({"graph_name": "target"})
    flow.add_graph(main)
    return flow, target, main, proxy


def test_registry_registration_without_flow():
    registry = NodeRegistry()
    registry.register_node("GraphProxy", GraphProxyNode)

    node = registry.create_node("GraphProxy", "proxy_1")

    assert node.properties["graph_name"] == ""
    assert node.inputs == {}
    assert node.outputs == {}


def test_register_nodes_has_no_duplicates():
    registry = NodeRegistry()
    register_nodes(registry)  # raises on duplicate registration

    for type_name in ["GraphProxy", "GraphPropertiesChanged", "GraphLoaded"]:
        assert registry.create_node(type_name, f"{type_name}_1") is not None


def test_proxy_mirrors_target_ports():
    _, target, _, proxy = make_proxy_setup()

    assert set(proxy.inputs.keys()) == {"in"}
    assert set(proxy.outputs.keys()) == {"out"}
    assert proxy.inputs["in"].value_type_list == target.inputs["in"].value_type_list
    assert proxy.outputs["out"].value_type_list == target.outputs["out"].value_type_list


def test_proxy_forwards_input_to_target_and_back():
    _, _, _, proxy = make_proxy_setup()
    received: list[list] = []
    proxy.outputs["out"].subscribe(1, lambda values: received.append(values))

    proxy.inputs["in"].dispatch([np.array([2.0], dtype=np.float64)])

    assert len(received) == 1
    np.testing.assert_array_equal(received[0][0], np.array([4.0]))


def test_proxy_replays_current_values_on_bind():
    flow = BaseNodeFlow()
    target = make_target_graph("target")
    flow.add_graph(target)
    # Produce a value before the proxy binds
    target.inputs["in"].dispatch([np.array([3.0], dtype=np.float64)])

    main = BaseNodeGraph("main", {})
    main.set_parent_flow(flow)
    proxy = GraphProxyNode("proxy_1")
    main.add_node(proxy)
    proxy.set_properties({"graph_name": "target"})

    assert proxy.outputs["out"].current_values is not None
    np.testing.assert_array_equal(
        proxy.outputs["out"].current_values[0], np.array([6.0])
    )


def test_proxy_rebinds_to_other_graph():
    flow, target, main, proxy = make_proxy_setup()

    other = BaseNodeGraph("other", {})
    value_types = [PortValueType(DataType.Float64)]
    other.add_input_port(StaticTypeInputPort("x", value_types))
    other.add_output_port(StaticTypeOutputPort("y", value_types))
    flow.add_graph(other)

    proxy.set_properties({"graph_name": "other"})

    assert set(proxy.inputs.keys()) == {"x"}
    assert set(proxy.outputs.keys()) == {"y"}
    # Old target dispatches no longer reach the proxy
    received: list[list] = []
    proxy.outputs["y"].subscribe(1, lambda values: received.append(values))
    target.inputs["in"].dispatch([np.array([1.0], dtype=np.float64)])
    assert received == []


def test_proxy_missing_graph_clears_ports_without_raise():
    _, _, _, proxy = make_proxy_setup()

    proxy.set_properties({"graph_name": "no_such_graph"})

    assert proxy.inputs == {}
    assert proxy.outputs == {}


def test_proxy_without_flow_stays_unbound():
    graph = BaseNodeGraph("main", {})
    proxy = GraphProxyNode("proxy_1")
    graph.add_node(proxy)

    proxy.set_properties({"graph_name": "target"})

    assert proxy.inputs == {}
    assert proxy.outputs == {}


def test_proxy_flush_chain_with_flushing_host():
    _, _, main, proxy = make_proxy_setup(graph_cls=FlushingGraph)
    flush_count = 0

    def on_flush():
        nonlocal flush_count
        flush_count += 1

    main.subscribe_flush_outputs(1, on_flush)

    proxy.inputs["in"].dispatch([np.array([2.0], dtype=np.float64)])

    assert flush_count >= 1


def test_proxy_data_flows_even_without_flush_firing():
    # Plain BaseNodeGraph: flush_outputs is a no-op hook, data still flows
    _, _, main, proxy = make_proxy_setup()
    flush_count = 0

    def on_flush():
        nonlocal flush_count
        flush_count += 1

    main.subscribe_flush_outputs(1, on_flush)
    received: list[list] = []
    proxy.outputs["out"].subscribe(1, lambda values: received.append(values))

    proxy.inputs["in"].dispatch([np.array([5.0], dtype=np.float64)])

    assert flush_count == 0
    np.testing.assert_array_equal(received[0][0], np.array([10.0]))


def test_proxy_finalize_unsubscribes_from_target():
    _, target, _, proxy = make_proxy_setup(graph_cls=FlushingGraph)

    proxy._do_finalize()

    received: list[list] = []
    proxy.outputs["out"].subscribe(1, lambda values: received.append(values))
    target.inputs["in"].dispatch([np.array([1.0], dtype=np.float64)])
    assert received == []
    assert id(proxy) not in target._flush_outputs_callbacks


def test_graph_loaded_node_fires_on_notify():
    graph = BaseNodeGraph("g", {})
    node = GraphLoadedNode("loaded_1")
    graph.add_node(node)
    received: list[list] = []
    node.outputs["loaded"].subscribe(1, lambda values: received.append(values))

    graph.notify_graph_loaded()

    assert len(received) == 1
    assert bool(received[0][0][0]) is True


def test_graph_properties_changed_node_emits_selected():
    graph = BaseNodeGraph("g", {"foo": 1})
    node = GraphPropertiesChangedNode("props_1")
    graph.add_node(node)
    node.set_properties({"selector": "foo", "value_type_list": "i32"})
    received: list[list] = []
    node.outputs["properties"].subscribe(1, lambda values: received.append(values))

    graph.set_properties({"foo": 5})

    assert len(received) == 1
    np.testing.assert_array_equal(received[0][0], np.array([5], dtype=np.int32))


def test_graph_properties_changed_node_ignores_unrelated_change():
    graph = BaseNodeGraph("g", {"foo": 1, "bar": 2})
    node = GraphPropertiesChangedNode("props_1")
    graph.add_node(node)
    node.set_properties({"selector": "foo", "value_type_list": "i32"})
    received: list[list] = []
    node.outputs["properties"].subscribe(1, lambda values: received.append(values))

    graph.set_properties({"bar": 10})

    assert received == []


def test_graph_properties_changed_node_fallback_fills_unchanged_selected_key():
    graph = BaseNodeGraph("g", {"foo": 1, "bar": 2})
    node = GraphPropertiesChangedNode("props_1")
    graph.add_node(node)
    node.set_properties({"selector": "foo,bar", "value_type_list": "i32,i32"})
    received: list[list] = []
    node.outputs["properties"].subscribe(1, lambda values: received.append(values))

    graph.set_properties({"bar": 10})

    assert len(received) == 1
    np.testing.assert_array_equal(received[0][0], np.array([1], dtype=np.int32))
    np.testing.assert_array_equal(received[0][1], np.array([10], dtype=np.int32))


class _FlushCountingGraph(BaseNodeGraph):
    def __init__(self, name, properties):
        super().__init__(name, properties)
        self.flush_count = 0

    def flush_outputs(self):
        self.flush_count += 1


def test_graph_properties_changed_node_does_not_flush():
    # Configuration-path emissions are committed by the set_properties /
    # activate caller, never by the node (see BaseNodeGraph.flush_outputs).
    graph = _FlushCountingGraph("g", {"foo": 1})
    node = GraphPropertiesChangedNode("props_1")
    graph.add_node(node)
    node.set_properties({"selector": "foo", "value_type_list": "i32"})
    received: list[list] = []
    node.outputs["properties"].subscribe(1, lambda values: received.append(values))

    node._do_activate()
    graph.set_properties({"foo": 5})

    assert len(received) == 2
    assert graph.flush_count == 0


def test_graph_properties_changed_node_activate_emits_snapshot():
    graph = BaseNodeGraph("g", {"foo": 7})
    node = GraphPropertiesChangedNode("props_1")
    graph.add_node(node)
    node.set_properties({"selector": "foo", "value_type_list": "i32"})
    received: list[list] = []
    node.outputs["properties"].subscribe(1, lambda values: received.append(values))

    node._do_activate()

    assert len(received) == 1
    np.testing.assert_array_equal(received[0][0], np.array([7], dtype=np.int32))


def test_graph_properties_changed_node_activate_skips_when_already_emitted():
    graph = BaseNodeGraph("g", {"foo": 1})
    node = GraphPropertiesChangedNode("props_1")
    graph.add_node(node)
    node.set_properties({"selector": "foo", "value_type_list": "i32"})
    received: list[list] = []
    node.outputs["properties"].subscribe(1, lambda values: received.append(values))

    graph.set_properties({"foo": 5})
    node._do_activate()

    assert len(received) == 1
    np.testing.assert_array_equal(received[0][0], np.array([5], dtype=np.int32))


def test_graph_properties_changed_node_engine_load_order_single_emission():
    # Engine loader order: add nodes -> node.set_properties -> graph
    # set_properties with the full persisted dict -> activate.
    graph = BaseNodeGraph("g", {"foo": 3})
    node = GraphPropertiesChangedNode("props_1")
    graph.add_node(node)
    node.set_properties({"selector": "foo", "value_type_list": "i32"})
    received: list[list] = []
    node.outputs["properties"].subscribe(1, lambda values: received.append(values))

    graph.set_properties({"foo": 3})
    node._do_activate()

    assert len(received) == 1
    np.testing.assert_array_equal(received[0][0], np.array([3], dtype=np.int32))


def test_graph_properties_changed_node_activate_with_no_matching_keys_emits_nothing_and_warns(
    caplog,
):
    graph = BaseNodeGraph("g", {})
    node = GraphPropertiesChangedNode("props_1")
    graph.add_node(node)
    with caplog.at_level("WARNING"):
        node.set_properties({"selector": "foo", "value_type_list": "i32"})
    received: list[list] = []
    node.outputs["properties"].subscribe(1, lambda values: received.append(values))

    node._do_activate()

    assert received == []
    assert any("foo" in record.message for record in caplog.records)


def test_graph_properties_changed_node_missing_selector_key_warns_once(caplog):
    graph = BaseNodeGraph("g", {"foo": 1})
    node = GraphPropertiesChangedNode("props_1")
    graph.add_node(node)
    with caplog.at_level("WARNING"):
        node.set_properties({"selector": "foo,missing", "value_type_list": "i32,i32"})
        received: list[list] = []
        node.outputs["properties"].subscribe(1, lambda values: received.append(values))

        graph.set_properties({"foo": 5})
        graph.set_properties({"foo": 6})

    assert len(received) == 2
    for values in received:
        np.testing.assert_array_equal(values[1], np.array([], dtype=np.int32))
    np.testing.assert_array_equal(received[0][0], np.array([5], dtype=np.int32))
    np.testing.assert_array_equal(received[1][0], np.array([6], dtype=np.int32))
    warnings = [r for r in caplog.records if "missing" in r.message]
    assert len(warnings) == 1


def test_graph_properties_changed_node_uncastable_value_emits_empty_and_warns(
    caplog,
):
    # Domain errors are handled inside the callback (graph set_properties
    # callbacks must not raise): a value that cannot be represented in the
    # selected type becomes an empty slot; other slots still deliver.
    graph = BaseNodeGraph("g", {"foo": "abc", "bar": 2})
    node = GraphPropertiesChangedNode("props_1")
    graph.add_node(node)
    node.set_properties({"selector": "foo,bar", "value_type_list": "i32,i32"})
    received: list[list] = []
    node.outputs["properties"].subscribe(1, lambda values: received.append(values))

    with caplog.at_level("WARNING"):
        graph.set_properties({"foo": "xyz"})
        graph.set_properties({"foo": "uvw"})

    assert len(received) == 2
    for values in received:
        np.testing.assert_array_equal(values[0], np.array([], dtype=np.int32))
        np.testing.assert_array_equal(values[1], np.array([2], dtype=np.int32))
    assert graph.properties["foo"] == "uvw"
    warnings = [r for r in caplog.records if "cannot represent" in r.message]
    assert len(warnings) == 1


def test_graph_properties_changed_node_emits_all_property_types():
    properties = {
        "p_i8": -1,
        "p_u8": 2,
        "p_i16": -3,
        "p_u16": 4,
        "p_i32": -5,
        "p_u32": 6,
        "p_i64": -7,
        "p_u64": 8,
        "p_f32": 1.5,
        "p_f64": 2.5,
        "p_bool": True,
        "p_str": "hello",
    }
    type_names = ["i8", "u8", "i16", "u16", "i32", "u32", "i64", "u64",
                  "f32", "f64", "bool", "str"]
    graph = BaseNodeGraph("g", dict(properties))
    node = GraphPropertiesChangedNode("props_1")
    graph.add_node(node)
    node.set_properties(
        {
            "selector": ",".join(properties),
            "value_type_list": ",".join(type_names),
        }
    )
    received: list[list] = []
    node.outputs["properties"].subscribe(1, lambda values: received.append(values))

    graph.set_properties(dict(properties))

    assert len(received) == 1
    expected_dtypes = [np.int8, np.uint8, np.int16, np.uint16, np.int32,
                       np.uint32, np.int64, np.uint64, np.float32, np.float64,
                       np.bool_]
    for value, dtype, prop_value in zip(
        received[0], expected_dtypes, list(properties.values())[:11]
    ):
        assert value.dtype == dtype
        assert value.shape == (1,)
        assert value[0] == prop_value
    assert str(received[0][11][0]) == "hello"

