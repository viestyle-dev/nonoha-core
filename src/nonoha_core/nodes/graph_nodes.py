from typing import Any, Callable
import numpy as np
import logging

from ..node import (
    BaseNodeGraph,
    BaseNode,
    NodeDoc,
    replace_node_input_port,
    replace_node_output_port,
)
from ..port import (
    StaticTypeOutputPort,
    StaticTypeInputPort,
    PortValue,
)
from ..data_type import (
    DataType,
    PortValueType,
    PropertyDataType,
    name_to_port_value_type,
)

logger = logging.getLogger(__name__)


class GraphProxyNode(BaseNode):
    """Proxy node that references and executes another graph in the same flow.

    The target graph is resolved by name through
    ``self.parent_graph.parent_flow`` (see BaseNodeFlow), so the resolution
    scope is the flow this node's graph belongs to.

    The target may come and go while the flow runs. While it is not there,
    the node keeps its ports and edges and passes nothing on; when a graph of
    that name is added, the node binds to it (ports the new graph does not
    have are removed with their edges) and passes on the last value each of
    its inputs received: ports carry the latest value, so the target gets it
    whatever the order the graphs were loaded or restarted in. A target that
    is not in the flow when ``graph_name`` is applied is bound when it is
    added; edges to ports that did not exist yet are then made.

    Note on flush propagation: this node subscribes to the target graph's
    ``flush_outputs`` and re-flushes its parent graph, but firing those
    callbacks is left to ``BaseNodeGraph`` subclasses
    (``flush_outputs`` is a no-op hook). Data transfer itself rides direct
    port subscriptions, so the proxy works even when flush callbacks never
    fire.
    """

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Proxy node that references and executes another graph",
            category="Graph",
            inputs={},
            outputs={},
        )

    PROPERTIES = {
        "graph_name": {
            "description": "Name of the graph to run",
            "data_type": "str",
            "default_value": "",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "GraphProxy")

        graph_name: str = str(self.properties["graph_name"])

        self._graph: BaseNodeGraph | None = None
        self._graph_name = graph_name
        self._flow = None  # the flow whose graph changes this node hears

    def set_properties(self, properties: dict[str, PropertyDataType]):
        if "graph_name" in properties:
            graph_name = properties["graph_name"]
            if not isinstance(graph_name, str):
                raise ValueError("graph_name must be a string")

            # Always rebind when graph_name is specified (allows refresh even with same name)
            flow = self.parent_graph.parent_flow if self.parent_graph else None
            graph = flow.get_graph(graph_name) if flow is not None else None
            renamed = graph_name != self._graph_name
            self._graph_name = graph_name
            self.properties["graph_name"] = graph_name
            self._watch(flow)
            if graph is not None:
                self._bind_graph(graph)
            elif renamed or not graph_name:
                # Another target (or none): the old target's ports mean nothing any more
                self._bind_graph(None)
            else:
                # The same target, not there now: keep the wiring for when it is back
                self._detach()
            if graph is None and graph_name:
                logger.warning(
                    f"{self.name}: Graph not found: {graph_name!r}"
                    f" (flow attached: {flow is not None}); it is bound when it is added"
                )

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _watch(self, flow):
        """Hear from ``flow`` when graphs are added or removed (once per flow)."""
        if flow is self._flow:
            return
        if self._flow is not None:
            self._flow.unsubscribe_graphs_changed(id(self))
        self._flow = flow
        if flow is not None:
            flow.subscribe_graphs_changed(id(self), self._on_graphs_changed)

    def _on_graphs_changed(self, name: str, graph: BaseNodeGraph | None):
        if name != self._graph_name:
            return
        if graph is None:
            self._detach()
            return
        self._bind_graph(graph)
        # The target was just added: its nodes start after this. Once they
        # have, it gets the latest value of each input
        graph.subscribe_graph_loaded(id(self), self._pass_latest)
        if self.parent_graph is not None:
            # Edges recorded before these ports existed
            self.parent_graph.connect_invalid_edges(self.name)
            self.parent_graph.notify_node_updated(self)

    def _pass_latest(self, graph: BaseNodeGraph):
        """Give the target the latest value of each input.

        Ports carry the latest value: the target gets it whatever the order
        the graphs were loaded or restarted in. An input that has received
        nothing (its edge was made only now) takes its source's latest value.
        Called while the target is loaded, whose loader commits the batch
        (no flush here).
        """
        if graph is not self._graph:
            return
        for name in self._proxied_input_names():
            target = graph.inputs.get(name)
            if target is None:
                continue
            values = self.inputs[name].current_values
            if values is None and self.parent_graph is not None:
                values = self.parent_graph.source_values(self.name, name)
            if values is not None:
                target.dispatch(values)

    def _detach(self):
        """Let go of the target but keep the ports and their edges."""
        graph = self._graph
        if graph is None:
            return
        graph.unsubscribe_flush_outputs(id(self))
        for name in self.outputs:
            if name in graph.outputs:
                graph.outputs[name].unsubscribe(id(self))
        self._graph = None

    def _bind_graph(self, graph: BaseNodeGraph | None):
        # Unsubscribe from previous graph
        if self._graph is not None:
            self._graph.unsubscribe_flush_outputs(id(self))

        if graph is None:
            # Clear all ports
            self._clear_all_ports()
            self._graph = None
            return

        # Differential sync for inputs
        self._sync_inputs(graph)

        # Differential sync for outputs (clone, not share)
        self._sync_outputs(graph)

        # Subscribe to new graph
        graph.subscribe_flush_outputs(id(self), self._on_graph_flush_outputs)

        # * When this node receives input, flush the target graph
        # * When the target graph flushes, flush this node's parent graph
        self._graph = graph

    def _proxied_input_names(self) -> list[str]:
        """The inputs that mirror the target graph's (the node's own property ports are not)."""
        return [name for name in self.inputs if not name.startswith(self.PROPERTY_PORT_PREFIX)]

    def _clear_all_ports(self):
        """Clear all dynamic ports with proper disconnection."""
        # Unsubscribe from graph outputs
        if self._graph is not None:
            for name in self.outputs.keys():
                if name in self._graph.outputs:
                    self._graph.outputs[name].unsubscribe(id(self))

        proxied = self._proxied_input_names()
        if self.parent_graph is not None:
            for name in proxied:
                self.parent_graph.disconnect_all_from_node_input(self.name, name)
            for port in self.outputs.values():
                self.parent_graph.disconnect_all_from_node_output(self.name, port.name)

        for name in proxied:
            self.inputs.pop(name).unsubscribe(id(self))

        self.outputs = {}

    def _sync_inputs(self, graph: BaseNodeGraph):
        """Sync input ports with differential update, preserving compatible edges.

        The mirrored ports end up in the target graph's order, after the
        node's own property ports. Every step goes through the ports in a
        list's order, never a set's (that order changes with every run), so
        what a client is shown and the order values are passed on in are the
        same on every run, whatever was bound before.
        """
        target_inputs = {n: p.value_type_list for n, p in graph.inputs.items()}
        current_names = self._proxied_input_names()
        kept = {name for name in current_names if name in target_inputs}

        # Remove ports that no longer exist
        for name in current_names:
            if name in kept:
                continue
            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_input(self.name, name)
            self.inputs[name].unsubscribe(id(self))
            del self.inputs[name]

        # Add new ports
        for name, types in target_inputs.items():
            if name in kept:
                continue
            port = StaticTypeInputPort(name, types)
            port.subscribe(
                id(self),
                lambda values, n=name: self._on_input(n, values),
            )
            self.inputs[name] = port

        # Update existing ports if types changed (replace_node_input_port preserves edges)
        for name, new_types in target_inputs.items():
            if name not in kept:
                continue
            old_port = self.inputs[name]
            if old_port.value_type_list != new_types:
                new_port = StaticTypeInputPort(name, new_types)
                replace_node_input_port(
                    self,
                    old_port,
                    new_port,
                    lambda values, n=name: self._on_input(n, values),
                )
                self.inputs[name] = new_port

        # The target's order: each port moves to the end, one after the other
        for name in target_inputs:
            self.inputs[name] = self.inputs.pop(name)

    def _sync_outputs(self, graph: BaseNodeGraph):
        """Sync output ports with differential update, cloning from graph.

        Like the inputs, the ports end up in the target graph's order and
        every step follows a list's order.
        """
        target_outputs = {n: p.value_type_list for n, p in graph.outputs.items()}
        current_names = list(self.outputs)
        kept = {name for name in current_names if name in target_outputs}
        old_graph = self._graph

        # Unsubscribe all from old graph first
        if old_graph is not None:
            for name in current_names:
                if name in old_graph.outputs:
                    old_graph.outputs[name].unsubscribe(id(self))

        # Remove ports that no longer exist
        for name in current_names:
            if name in kept:
                continue
            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_output(self.name, name)
            del self.outputs[name]

        # Add new ports (clone from graph)
        for name in target_outputs:
            if name in kept:
                continue
            original = graph.outputs[name]
            port = StaticTypeOutputPort(name, original.value_type_list)
            self.outputs[name] = port

            if original.current_values is not None:
                port.dispatch(original.current_values)

        # Update existing ports if types changed
        for name, new_types in target_outputs.items():
            if name not in kept:
                continue
            old_port = self.outputs[name]
            if old_port.value_type_list != new_types:
                new_port = StaticTypeOutputPort(name, new_types)
                replace_node_output_port(self, old_port, new_port)
                self.outputs[name] = new_port

                if old_port.current_values is not None:
                    new_port.dispatch(old_port.current_values)

        # The target's order: each port moves to the end, one after the other
        for name in target_outputs:
            self.outputs[name] = self.outputs.pop(name)

        # Subscribe to all outputs on new graph
        for name in target_outputs:
            graph.outputs[name].subscribe(
                id(self),
                lambda values, n=name: self._forward_output(n, values),
            )

    def _forward_output(self, port_name: str, values: list[PortValue]):
        """Forward output values from referenced graph to this node's output."""
        if port_name in self.outputs:
            self.outputs[port_name].dispatch(values)

    def _on_input(self, port_name: str, values: list[Any]):
        graph = self._graph
        if graph is None:
            return

        port = graph.inputs.get(port_name)
        if port is None:
            logger.warning(f"{self.name}: Port not found: {port_name}")
            return

        port.dispatch(values)

        graph.flush_outputs()

    def _on_graph_flush_outputs(self):
        if self.parent_graph is not None:
            self.parent_graph.flush_outputs()

    def finalize(self):
        """Clean up subscriptions when node is removed."""
        self._watch(None)
        if self._graph is not None:
            # Unsubscribe from graph's flush_outputs
            self._graph.unsubscribe_flush_outputs(id(self))

            # Unsubscribe from graph's output ports
            for name in self.outputs.keys():
                if name in self._graph.outputs:
                    self._graph.outputs[name].unsubscribe(id(self))


# Per-slot (python cast, numpy dtype) builders for the scalar types
# GraphPropertiesChangedNode.set_properties allows.
_VALUE_BUILDERS: dict[DataType, tuple[Callable[[Any], Any], Any]] = {
    DataType.Int8: (int, np.int8),
    DataType.Uint8: (int, np.uint8),
    DataType.Int16: (int, np.int16),
    DataType.Uint16: (int, np.uint16),
    DataType.Int32: (int, np.int32),
    DataType.Uint32: (int, np.uint32),
    DataType.Int64: (int, np.int64),
    DataType.Uint64: (int, np.uint64),
    DataType.Float32: (float, np.float32),
    DataType.Float64: (float, np.float64),
    DataType.Bool: (bool, np.bool_),
    DataType.String: (str, np.dtypes.StringDType()),  # type: ignore
}


class GraphPropertiesChangedNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Emit selected property values when graph properties change",
            category="Graph",
            inputs={},
            outputs={"properties": ""},
        )

    PROPERTIES = {
        "selector": {
            "description": "Comma-separated names of the graph properties to emit",
            "data_type": "str",
            "default_value": "property_name",
        },
        "value_type_list": {
            "description": "Comma-separated value types, one per selected property",
            "data_type": "str",
            "default_value": "i32",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "GraphPropertiesChanged")

        self._selector: list[str] = str(self.properties["selector"]).split(",")
        self._value_type_list: list[PortValueType] = [
            name_to_port_value_type(name)
            for name in str(self.properties["value_type_list"]).split(",")
        ]

        output_properties = StaticTypeOutputPort("properties", self._value_type_list)
        self._output_properties = output_properties

        self.outputs[output_properties.name] = output_properties

        self._warned_missing_keys: set[str] = set()
        self._warned_cast_keys: set[str] = set()
        self._selector_set: frozenset[str] = frozenset()
        self._emit_plan: list[tuple[str, Callable[[Any], Any], Any, PortValue]] = []
        self._rebuild_emit_plan()

    def set_properties(self, properties: dict[str, PropertyDataType]):
        selector = self._selector
        if "selector" in properties:
            selector_str = properties["selector"]
            if not isinstance(selector_str, str):
                raise ValueError("selector must be a string")
            selector = selector_str.split(",")

        value_type_list = self._value_type_list
        if "value_type_list" in properties:
            value_type_list_str = properties["value_type_list"]
            if not isinstance(value_type_list_str, str):
                raise ValueError("value_type_list must be a string")
            value_type_list = [
                name_to_port_value_type(name) for name in value_type_list_str.split(",")
            ]
            # Validate: must be scalar and numeric/bool/string type
            allowed_types = {
                DataType.Int8,
                DataType.Uint8,
                DataType.Int16,
                DataType.Uint16,
                DataType.Int32,
                DataType.Uint32,
                DataType.Int64,
                DataType.Uint64,
                DataType.Float32,
                DataType.Float64,
                DataType.Bool,
                DataType.String,
            }
            for vt in value_type_list:
                if vt.shape != ():
                    raise ValueError(f"value_type must be scalar, got shape {vt.shape}")
                if vt.data_type not in allowed_types:
                    raise ValueError(
                        f"value_type must be numeric/bool/string, got {vt.data_type}"
                    )

        if len(selector) != len(value_type_list):
            raise ValueError("selector and value_type_list must have the same length")

        new_output_properties = self._output_properties
        if value_type_list != self._value_type_list:
            new_output_properties = StaticTypeOutputPort("properties", value_type_list)

        if new_output_properties != self._output_properties:
            replace_node_output_port(
                self, self._output_properties, new_output_properties
            )
            self._output_properties = new_output_properties

        self._value_type_list = value_type_list
        self._selector = selector

        self.properties["selector"] = ",".join(selector)
        self.properties["value_type_list"] = ",".join([t.name for t in value_type_list])

        self._rebuild_emit_plan()
        self._warn_missing_selector_keys()

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def finalize(self):
        if self.parent_graph is not None:
            self.parent_graph.unsubscribe_properties_changed(id(self))

    def set_parent_graph(self, parent_graph):
        self.parent_graph = parent_graph

        parent_graph.subscribe_properties_changed(id(self), self._on_properties_changed)
        self._warn_missing_selector_keys()

    def activate(self):
        # Emit the current property snapshot once at activation. Skip if
        # something already emitted (the engine loader fires graph
        # set_properties with the full property dict before activation).
        if self.parent_graph is None:
            return
        if self._output_properties.current_values is not None:
            return
        self._on_properties_changed(self.parent_graph.properties)

    def _rebuild_emit_plan(self):
        # Selector and value types only change here (cold path); the
        # emission path reuses the precomputed plan. Empty arrays are
        # element-free, so sharing one instance per slot is safe.
        plan = []
        for name, value_type in zip(self._selector, self._value_type_list):
            cast, dtype = _VALUE_BUILDERS[value_type.data_type]
            plan.append((name, cast, dtype, np.array([], dtype=dtype)))
        self._selector_set = frozenset(self._selector)
        self._emit_plan = plan

    def _warn_missing_selector_keys(self):
        graph = self.parent_graph
        if graph is None:
            return
        for name in self._selector:
            if name not in graph.properties and name not in self._warned_missing_keys:
                self._warned_missing_keys.add(name)
                logger.warning(
                    f"{self.name}: selector key {name!r} not found in graph "
                    f"properties (declared: {sorted(graph.properties)})"
                )

    def _on_properties_changed(self, properties: dict[str, PropertyDataType]):
        if self._selector_set.isdisjoint(properties):
            return
        graph = self.parent_graph
        if graph is None:
            return
        base = graph.properties
        values: list[PortValue] = []
        for name, cast, dtype, empty in self._emit_plan:
            v = properties.get(name, base.get(name))
            if v is None:
                values.append(empty)
                continue
            try:
                values.append(np.array([cast(v)], dtype=dtype))
            except (TypeError, ValueError, OverflowError) as e:
                # Graph properties-changed callbacks must not raise; a value
                # that cannot be represented in the selected type becomes
                # "no value" for its slot.
                values.append(empty)
                if name not in self._warned_cast_keys:
                    self._warned_cast_keys.add(name)
                    logger.warning(
                        f"{self.name}: cannot represent property {name!r} "
                        f"value {v!r} in the selected type: {e}"
                    )
        self._output_properties.dispatch(values)
        # No flush: configuration-path emission — the caller of
        # set_properties()/activate() owns the commit (see
        # BaseNodeGraph.flush_outputs).


class GraphLoadedNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Emit a signal when the parent graph is loaded",
            category="Graph",
            inputs={},
            outputs={"loaded": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "GraphLoaded")

        output_loaded = StaticTypeOutputPort("loaded", [PortValueType(DataType.Bool)])
        self._output_loaded = output_loaded

        self.outputs[output_loaded.name] = output_loaded

    def finalize(self):
        if self.parent_graph is not None:
            self.parent_graph.unsubscribe_graph_loaded(id(self))

    def set_parent_graph(self, parent_graph: BaseNodeGraph):
        self.parent_graph = parent_graph

        parent_graph.subscribe_graph_loaded(id(self), self._on_graph_loaded)

    def _on_graph_loaded(self, graph: BaseNodeGraph):
        self._output_loaded.dispatch([np.array([True], dtype=np.bool_)])
