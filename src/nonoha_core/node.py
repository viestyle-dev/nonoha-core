from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import itertools
from pathlib import Path
from typing import (
    Callable,
    ClassVar,
    Generic,
    KeysView,
    Required,
    TypeAlias,
    TypeVar,
    TypedDict,
    NotRequired,
)
import logging

from .port import (
    PortCallback,
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
    make_edge_dispatch,
    make_index_dispatch,
    port_is_connectable,
    port_is_connectable_with_index,
)

from .data_type import PropertyDataType, name_to_port_value_type

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class NodeDoc:
    """Catalog documentation for a node. Not used at runtime."""

    description: str = ""
    category: str = ""
    inputs: dict[str, str] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)


class PropertyDescription(TypedDict, total=False):
    description: Required[str]
    data_type: str  # PortValueType name: "f64", "i32", "str", "bool", etc.
    default_value: PropertyDataType
    min_value: int | float | None
    max_value: int | float | None


class BaseNode:
    PROPERTIES: ClassVar[dict[str, PropertyDescription]] = {}

    @classmethod
    def describe(
        cls, properties: dict[str, PropertyDataType] | None = None
    ) -> NodeDoc | None:
        """Return catalog documentation for this node.

        Args:
            properties: Current property values for dynamic port descriptions.
                        None uses default properties.
        Returns:
            NodeDoc, or None if no documentation is provided.
        """
        return None

    PROPERTY_PORT_PREFIX: ClassVar[str] = "@"

    def __init__(self, name: str, type: str):
        self._name = name
        self._type = type
        self._is_active = False

        self.inputs: dict[str, StaticTypeInputPort] = {}
        self.outputs: dict[str, StaticTypeOutputPort] = {}

        # Auto-initialize properties from PROPERTIES class variable
        self.properties: dict[str, PropertyDataType] = {
            key: desc["default_value"]
            for key, desc in self.PROPERTIES.items()
            if "default_value" in desc
        }
        self.parent_graph: "BaseNodeGraph[NodeGraphPersist] | None" = None

        # Property port grouping (configured at graph level)
        self._property_group_by_key: dict[str, _PropertyGroup] = {}

        # Auto-create property ports from PROPERTIES
        self._auto_create_property_ports()

    @property
    def is_active(self) -> bool:
        """Whether the node is in operational state (after activate, before finalize)."""
        return self._is_active

    def _do_activate(self):
        """Called by the system. Sets is_active and calls activate().
        Do not call directly — the framework calls this at the right time.
        """
        self._is_active = True
        self.activate()

    def activate(self):
        """Called when the node is added to a running graph.
        Override to set up runtime resources (event loop, threads, connections).
        __init__ must remain side-effect-free; move runtime initialization here.
        """
        pass

    def _do_finalize(self):
        """Called by the system. Calls finalize() and clears is_active.
        Do not call directly — the framework calls this at the right time.
        """
        self.finalize()
        self._is_active = False

    def finalize(self):
        """Called when the node is removed from a graph.
        Override to release runtime resources. No need to call super().
        """
        pass

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    def set_properties(self, properties: dict[str, PropertyDataType]):
        pass

    def set_parent_graph(self, parent_graph: "BaseNodeGraph"):
        self.parent_graph = parent_graph

    def _auto_create_property_ports(self):
        """Auto-create individual input ports from PROPERTIES entries that have data_type."""
        for key, desc in self.PROPERTIES.items():
            if "data_type" not in desc:
                continue
            port_type = name_to_port_value_type(desc["data_type"])
            port_name = f"{self.PROPERTY_PORT_PREFIX}{key}"
            port = StaticTypeInputPort(port_name, [port_type])
            port.subscribe(
                id(self),
                lambda values, k=key: self._on_single_property(k, values),
            )
            self.inputs[port_name] = port

    def _on_single_property(self, key: str, values: list[PortValue]):
        """Handle a value received on an individual property port."""
        value = values[0][-1]

        if key in self._property_group_by_key:
            pg = self._property_group_by_key[key]
            idx = pg.keys.index(key)
            pg.values_store[idx] = value
            # Same semantics as data port dispatch_flags:
            # fire when flag=True value arrives AND all values are present
            if pg.dispatch_flags[idx] and all(v is not None for v in pg.values_store):
                props: dict[str, PropertyDataType] = {
                    k: v for k, v in zip(pg.keys, pg.values_store)  # type: ignore[misc]
                }
                try:
                    self.set_properties(props)
                except Exception as e:
                    logger.warning(f"Error setting properties: {e}")
        else:
            # Ungrouped: apply immediately
            try:
                self.set_properties({key: value})
            except Exception as e:
                logger.warning(f"Error setting property {key}: {e}")

    def set_property_groups(self, groups: list[dict]):
        """Configure property groups for atomic updates (called from graph layer).

        Each group: {"keys": ["a", "b"], "dispatch_flags": [False, True]}
        Same semantics as data port dispatch_flags.
        """
        self._property_group_by_key = {}
        for group_def in groups:
            keys = group_def["keys"]
            flags = group_def.get("dispatch_flags", [False] * len(keys))
            pg = _PropertyGroup(
                keys=keys, dispatch_flags=flags, values_store=[None] * len(keys)
            )
            for key in keys:
                self._property_group_by_key[key] = pg


@dataclass
class _PropertyGroup:
    """Internal state for a property group with dispatch_flags semantics."""

    keys: list[str]
    dispatch_flags: list[bool]
    values_store: list[PropertyDataType | None] = field(default_factory=list)

    def __post_init__(self):
        if not self.values_store:
            self.values_store = [None] * len(self.keys)


class Edge:
    def __init__(self, valid: bool = True):
        self.valid = valid


class NodeGraphPersist(ABC):

    @property
    @abstractmethod
    def data_dir_path(self) -> Path:
        """Return the directory path where the persist data is stored."""
        pass

    @abstractmethod
    def add_input_port(self, port: StaticTypeInputPort) -> None:
        """Add an input port to the persist storage."""
        pass

    @abstractmethod
    def remove_input_port(self, port_name: str) -> None:
        """Remove an input port from the persist storage."""
        pass

    @abstractmethod
    def add_output_port(self, port: StaticTypeOutputPort) -> None:
        """Add an output port to the persist storage."""
        pass

    @abstractmethod
    def remove_output_port(self, port_name: str) -> None:
        """Remove an output port from the persist storage."""
        pass

    @abstractmethod
    def add_node(self, node: BaseNode) -> None:
        """Add a node to the persist storage."""
        pass

    @abstractmethod
    def remove_node(self, node_name: str) -> None:
        """Remove a node from the persist storage."""
        pass

    @abstractmethod
    def update_edges(self, edges: dict[tuple[str, str], Edge]) -> None:
        """Update the edges in the persist storage."""
        pass

    @abstractmethod
    def update_node(self, node: BaseNode) -> None:
        """Update a node in the persist storage."""
        pass

    @abstractmethod
    def update_properties(self, node: BaseNode) -> None:
        """Update the properties of a node in the persist storage."""
        pass

    @abstractmethod
    def update_graph_properties(self, properties: dict[str, PropertyDataType]) -> None:
        """Update the graph's own properties in the persist storage."""
        pass


def extract_last_number(s: str) -> int | None:
    splits = s.split("_")
    if len(splits) == 1:
        return None
    try:
        return int(splits[-1])
    except ValueError:
        return None


PropertiesChangedCallback: TypeAlias = Callable[[dict[str, PropertyDataType]], None]
GraphLoadedCallback: TypeAlias = Callable[["BaseNodeGraph"], None]
FlushOutputsCallback: TypeAlias = Callable[[], None]


TPersist = TypeVar("TPersist", bound=NodeGraphPersist)


class BaseNodeGraph(BaseNode, Generic[TPersist]):
    """NodeGraph class includes a collection of nodes and connections between them.

    Included nodes are managed by this class.

    Args:
        BaseNode (_type_): _description_
    """

    def __init__(self, name: str, properties: dict[str, PropertyDataType]):
        super().__init__(name, "NodeGraph")
        self._nodes: dict[str, BaseNode] = {}

        # ({node_name}).{port_name}(.{index})
        self._edges: dict[tuple[str, str], Edge] = {}

        # ({node_name}).{port_name} -> [edges]
        self._source_port_to_edges: dict[str, list[tuple[str, str]]] = {}
        self._target_port_to_edges: dict[str, list[tuple[str, str]]] = {}

        self._persist: TPersist | None = None
        self.parent_flow: "BaseNodeFlow | None" = None
        self.properties = properties

        self._properties_changed_callbacks: dict[int, PropertiesChangedCallback] = {}
        self._graph_loaded_callbacks: dict[int, GraphLoadedCallback] = {}
        self._flush_outputs_callbacks: dict[int, FlushOutputsCallback] = {}

        self._max_node_id = 0

    @property
    def nodes(self) -> dict[str, BaseNode]:
        return self._nodes

    def finalize(self):
        for node in self._nodes.values():
            node._do_finalize()

    def _on_output(self, port: StaticTypeOutputPort, values: list[PortValue]):
        # NOTE: Implement the logic in inherited classes
        pass

    def flush_outputs(self):
        """Commit buffered graph outputs. No-op here; subclasses override.

        Propagation between nodes is synchronous via port subscriptions
        and never depends on this call.

        The origin rule: each dispatch cascade is committed exactly once,
        by the code that originated it:

        - Configuration calls MAY make nodes emit: set_properties (node
          and graph), activate(), notify_graph_loaded(). The caller (API
          handler, loader) flushes once after its batch; nodes do not
          flush on these paths.
        - Injecting external values (e.g. a WebSocket input handler):
          flush after dispatching.
        - Async callbacks inside nodes (timers, call_soon, devices): the
          node flushes right after dispatching — no caller exists.
        - Dispatching into another graph: flush that graph
          (GraphProxyNode._on_input).

        Nodes reacting to an in-flight dispatch never call this.
        """
        # NOTE: Implement the logic in inherited classes
        pass

    @property
    def max_node_id(self):
        return self._max_node_id

    @property
    def persist(self):
        return self._persist

    def set_persist(self, persist: TPersist):
        self._persist = persist

    def set_parent_flow(self, flow: "BaseNodeFlow | None"):
        """Set the flow this graph belongs to."""
        self.parent_flow = flow

    def subscribe_properties_changed(
        self, key: int, callback: PropertiesChangedCallback
    ):
        """Register a callback fired by set_properties with the accepted
        change dict (unknown keys are dropped before callbacks fire, so the
        notified change set always equals the applied change set).

        Contract: the callback must not raise — handle domain errors
        inside it (see GraphPropertiesChangedNode) — and must not add or
        remove properties-changed subscriptions, since set_properties
        iterates the subscription dict directly.
        """
        self._properties_changed_callbacks[key] = callback

    def unsubscribe_properties_changed(self, key: int):
        del self._properties_changed_callbacks[key]

    def subscribe_graph_loaded(self, key: int, callback: GraphLoadedCallback):
        self._graph_loaded_callbacks[key] = callback

    def unsubscribe_graph_loaded(self, key: int):
        del self._graph_loaded_callbacks[key]

    def subscribe_flush_outputs(self, key: int, callback: FlushOutputsCallback):
        self._flush_outputs_callbacks[key] = callback

    def unsubscribe_flush_outputs(self, key: int):
        del self._flush_outputs_callbacks[key]

    def notify_graph_loaded(self):
        for callback in self._graph_loaded_callbacks.values():
            callback(self)

    def set_properties(self, properties: dict[str, PropertyDataType]):
        if not properties.keys() <= self.properties.keys():
            unknown = sorted(properties.keys() - self.properties.keys())
            logger.warning(
                f"{self.name}: ignoring unknown graph property keys: {unknown}"
            )
            properties = {
                k: v for k, v in properties.items() if k in self.properties
            }
            if not properties:
                return

        # Callbacks must not raise nor (un)subscribe — see
        # subscribe_properties_changed.
        for callback in self._properties_changed_callbacks.values():
            callback(properties)

        self.properties.update(properties)

        if self._persist is not None:
            self._persist.update_graph_properties(self.properties)

    def add_input_port(self, port: StaticTypeInputPort):
        port_name = port.name
        if port_name in self.inputs:
            raise ValueError("Port name already exists")

        if (last_number := extract_last_number(port_name)) is not None:
            self._max_node_id = max(self._max_node_id, last_number)

        self.inputs[port_name] = port

        if self._persist is not None:
            self._persist.add_input_port(port)

    def remove_input_port(self, port_name: str):
        if port_name not in self.inputs:
            return

        self.disconnect_all_from_input(port_name)
        self.inputs.pop(port_name)

        if self._persist is not None:
            self._persist.remove_input_port(port_name)

    def add_output_port(self, port: StaticTypeOutputPort):
        port_name = port.name
        if port_name in self.outputs:
            raise ValueError("Port name already exists")

        if (last_number := extract_last_number(port_name)) is not None:
            self._max_node_id = max(self._max_node_id, last_number)

        self.outputs[port_name] = port
        port.subscribe(id(self), lambda data: self._on_output(port, data))

        if self._persist is not None:
            self._persist.add_output_port(port)

    def remove_output_port(self, port_name: str):
        if port_name not in self.outputs:
            return

        self.disconnect_all_from_output(port_name)
        self.outputs.pop(port_name)

        if self._persist is not None:
            self._persist.remove_output_port(port_name)

    def add_node(self, node: BaseNode):
        node_name = node.name
        if node_name in self._nodes:
            raise ValueError("Node name already exists")

        if (last_number := extract_last_number(node_name)) is not None:
            self._max_node_id = max(self._max_node_id, last_number)

        self._nodes[node_name] = node
        node.set_parent_graph(self)

        if self._persist is not None:
            self._persist.add_node(node)

    def remove_node(self, name: str):
        node = self._nodes.get(name)
        if node is None:
            return

        for input_port in node.inputs.values():
            self.disconnect_all_from_node_input(name, input_port.name)
        for output_port in node.outputs.values():
            self.disconnect_all_from_node_output(name, output_port.name)

        node._do_finalize()
        self._nodes.pop(name)
        if self._persist is not None:
            self._persist.remove_node(name)

    def get_node(self, name: str):
        return self._nodes.get(name)

    def get_node_names(self):
        return self._nodes.keys()

    def get_edges(self):
        return self._edges.keys()

    @staticmethod
    def _parse_port_value_name(value_name: str):
        parts = value_name.split(".")

        if len(parts) == 1:
            return parts[0], None
        elif len(parts) == 2:
            try:
                return parts[0], int(parts[1])
            except ValueError:
                raise ValueError(f"Invalid port index: {parts[1]}")
        else:
            raise ValueError(f"Invalid port value_name format: {value_name}")

    def connect_input_to_node(
        self, input_port_name: str, node_name: str, node_port_value_name: str
    ):
        node_port_name, node_port_value_index = self._parse_port_value_name(
            node_port_value_name
        )

        input_port = self.inputs[input_port_name]
        node = self._nodes[node_name]
        node_port = node.inputs[node_port_name]

        edge_key = (
            f".{input_port_name}",
            f"{node_name}.{node_port_value_name}",
        )
        if edge_key in self._edges:
            raise ValueError("Edge already exists")

        if input_port.has_callback(id(node_port)):
            raise ValueError("input port is already connected to node port")

        # edge_cb is the complete "values arrived" behavior for this edge
        # (cast slots when needed, then deliver into the node port). It is
        # both subscribed and used for the connect-time replay below.
        if node_port_value_index is None:
            if not port_is_connectable(input_port, node_port):
                raise ValueError(
                    f"Port is not connectable. {input_port.name}, {node_port.name}"
                )
            edge_cb = make_edge_dispatch(input_port, node_port) or node_port.dispatch
        else:
            if not port_is_connectable_with_index(
                input_port, node_port, node_port_value_index
            ):
                raise ValueError(
                    f"Port is not connectable with index. {input_port.name}, {node_port.name}"
                )
            edge_cb = make_index_dispatch(
                input_port, node_port, node_port_value_index
            ) or (
                lambda values, index=node_port_value_index: node_port.receive_value_with_index(
                    index, values
                )
            )
        input_port.subscribe(id(node_port), edge_cb)

        self._edges[edge_key] = Edge()
        self._source_port_to_edges.setdefault(f".{input_port_name}", []).append(
            edge_key
        )
        self._target_port_to_edges.setdefault(
            f"{node_name}.{node_port_value_name}", []
        ).append(edge_key)

        if input_port.current_values is not None:
            edge_cb(input_port.current_values)

            # print("!! i -> n")
            self.flush_outputs()

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def disconnect_input_to_node(
        self, input_port_name: str, node_name: str, node_port_value_name: str
    ):
        node_port_name, _ = self._parse_port_value_name(node_port_value_name)

        input_port = self.inputs[input_port_name]
        node = self._nodes[node_name]
        node_port = node.inputs[node_port_name]

        input_port.unsubscribe(id(node_port))

        edge_key = (
            f".{input_port_name}",
            f"{node_name}.{node_port_value_name}",
        )

        del self._edges[edge_key]
        self._source_port_to_edges[f".{input_port_name}"].remove(edge_key)
        self._target_port_to_edges[f"{node_name}.{node_port_value_name}"].remove(
            edge_key
        )

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def disconnect_all_from_input(self, input_port_name: str):
        input_port = self.inputs[input_port_name]

        for edge_key in self._source_port_to_edges.get(f".{input_port_name}", []):
            target_node_name, target_port_name = edge_key[1].split(".", 1)
            if target_node_name == "":
                target_port = self.outputs[target_port_name]
                input_port.unsubscribe(id(target_port))
            else:
                target_node = self._nodes[target_node_name]
                target_port = target_node.inputs[target_port_name]
                input_port.unsubscribe(id(target_port))

            del self._edges[edge_key]
            self._target_port_to_edges[edge_key[1]].remove(edge_key)

        self._source_port_to_edges[f".{input_port_name}"] = []

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def disconnect_all_from_output(self, output_port_name: str):
        output_port = self.outputs[output_port_name]

        for edge_key in self._target_port_to_edges.get(f".{output_port_name}", []):
            source_node_name, source_port_name = edge_key[0].split(".")
            if source_node_name == "":
                source_port = self.inputs[source_port_name]
                source_port.unsubscribe(id(output_port))
            else:
                source_node = self._nodes[source_node_name]
                source_port = source_node.outputs[source_port_name]
                source_port.unsubscribe(id(output_port))

            del self._edges[edge_key]
            self._source_port_to_edges[edge_key[0]].remove(edge_key)

        self._target_port_to_edges[f".{output_port_name}"] = []

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def connect_node_to_output(
        self, node_name: str, node_port_name: str, output_port_name: str
    ):
        node = self._nodes[node_name]
        node_port = node.outputs[node_port_name]
        output_port = self.outputs[output_port_name]

        if not port_is_connectable(node_port, output_port):
            raise ValueError(
                f"Port is not connectable: {node_name=}, {node_port_name=}, {output_port_name=}"
            )

        edge_key = (
            f"{node_name}.{node_port_name}",
            f".{output_port_name}",
        )
        if edge_key in self._edges:
            raise ValueError("Edge already exists")

        edge_cb = make_edge_dispatch(node_port, output_port) or output_port.dispatch
        node_port.subscribe(id(output_port), edge_cb)
        self._edges[edge_key] = Edge()
        self._source_port_to_edges.setdefault(
            f"{node_name}.{node_port_name}", []
        ).append(edge_key)
        self._target_port_to_edges.setdefault(f".{output_port_name}", []).append(
            edge_key
        )

        if node_port.current_values is not None:
            edge_cb(node_port.current_values)

            # print("!! n -> o")
            self.flush_outputs()

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def disconnect_node_to_output(
        self, node_name: str, node_port_name: str, output_port_name: str
    ):
        node = self._nodes[node_name]
        node_port = node.outputs[node_port_name]
        output_port = self.outputs[output_port_name]

        node_port.unsubscribe(id(output_port))

        edge_key = (
            f"{node_name}.{node_port_name}",
            f".{output_port_name}",
        )

        del self._edges[edge_key]
        self._source_port_to_edges[f"{node_name}.{node_port_name}"].remove(
            (f"{node_name}.{node_port_name}", f".{output_port_name}")
        )
        self._target_port_to_edges[f".{output_port_name}"].remove(
            (f"{node_name}.{node_port_name}", f".{output_port_name}")
        )

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def connect_nodes(
        self,
        output_node_name: str,
        output_port_name: str,
        input_node_name: str,
        input_port_value_name: str,
    ):
        out_node = self._nodes[output_node_name]
        out_port = out_node.outputs[output_port_name]

        in_port_name, in_port_value_index = self._parse_port_value_name(
            input_port_value_name
        )

        in_node = self._nodes[input_node_name]
        in_port = in_node.inputs[in_port_name]

        edge_key = (
            f"{output_node_name}.{output_port_name}",
            f"{input_node_name}.{input_port_value_name}",
        )
        if edge_key in self._edges:
            raise ValueError("Edge already exists")

        if out_port.has_callback(id(in_port)):
            raise ValueError("output port is already connected to node input")

        # edge_cb is the complete "values arrived" behavior for this edge
        # (cast slots when needed, then deliver into the input port). It is
        # both subscribed and used for the connect-time replay below.
        if in_port_value_index is None:
            if not port_is_connectable(out_port, in_port):
                raise ValueError(
                    f"Port is not connectable: {output_node_name=}, {output_port_name=}, {input_node_name=}, {input_port_value_name=}"
                )
            edge_cb = make_edge_dispatch(out_port, in_port) or in_port.dispatch
        else:
            if not port_is_connectable_with_index(
                out_port, in_port, in_port_value_index
            ):
                raise ValueError(
                    f"Port is not connectable: {output_node_name=}, {output_port_name=}, {input_node_name=}, {input_port_value_name=}"
                )
            edge_cb = make_index_dispatch(out_port, in_port, in_port_value_index) or (
                lambda values, index=in_port_value_index: in_port.receive_value_with_index(
                    index, values
                )
            )
        out_port.subscribe(id(in_port), edge_cb)

        self._edges[edge_key] = Edge()
        self._source_port_to_edges.setdefault(
            f"{output_node_name}.{output_port_name}", []
        ).append(edge_key)
        self._target_port_to_edges.setdefault(
            f"{input_node_name}.{input_port_value_name}", []
        ).append(edge_key)

        if out_port.current_values is not None:
            edge_cb(out_port.current_values)
            # print("!! n -> n")
            self.flush_outputs()

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def disconnect_nodes(
        self,
        output_node_name: str,
        output_port_name: str,
        input_node_name: str,
        input_port_value_name: str,
    ):
        out_node = self._nodes[output_node_name]
        out_port = out_node.outputs[output_port_name]

        in_port_name, in_port_value_index = self._parse_port_value_name(
            input_port_value_name
        )

        in_node = self._nodes[input_node_name]
        in_port = in_node.inputs[in_port_name]

        out_port.unsubscribe(id(in_port))

        edge_key = (
            f"{output_node_name}.{output_port_name}",
            f"{input_node_name}.{input_port_value_name}",
        )
        del self._edges[edge_key]

        self._source_port_to_edges[f"{output_node_name}.{output_port_name}"].remove(
            edge_key
        )
        self._target_port_to_edges[f"{input_node_name}.{input_port_value_name}"].remove(
            edge_key
        )

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def disconnect_all_from_node_input(self, node_name: str, node_port_name: str):
        node = self._nodes.get(node_name)
        if node is None:
            return

        node_port = node.inputs[node_port_name]

        target_keys = [
            f"{node_name}.{node_port_name}",
            *(
                f"{node_name}.{node_port_name}.{index}"
                for index in range(len(node_port.value_type_list))
            ),
        ]

        for edge_key in itertools.chain(
            *(
                self._target_port_to_edges.get(target_key, [])
                for target_key in target_keys
            )
        ):
            source_node_name, source_port_name = edge_key[0].split(".")
            if source_node_name == "":
                source_port = self.inputs[source_port_name]
                source_port.unsubscribe(id(node_port))
            else:
                source_node = self._nodes[source_node_name]
                source_port = source_node.outputs[source_port_name]
                source_port.unsubscribe(id(node_port))

            del self._edges[edge_key]
            self._source_port_to_edges[edge_key[0]].remove(edge_key)

        for target_key in target_keys:
            self._target_port_to_edges[target_key] = []

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def disconnect_all_from_node_output(self, node_name: str, node_port_name: str):
        node = self._nodes.get(node_name)
        if node is None:
            return

        node_port = node.outputs[node_port_name]

        for edge_key in self._source_port_to_edges.get(
            f"{node_name}.{node_port_name}", []
        ):
            target_node_name, target_port_value_name = edge_key[1].split(".", 1)
            target_port_name, target_port_value_index = self._parse_port_value_name(
                target_port_value_name
            )
            if target_node_name == "":
                target_port = self.outputs[target_port_name]
                node_port.unsubscribe(id(target_port))
            else:
                target_node = self._nodes[target_node_name]
                target_port = target_node.inputs[target_port_name]
                node_port.unsubscribe(id(target_port))

            del self._edges[edge_key]

            self._target_port_to_edges[edge_key[1]].remove(edge_key)

        self._source_port_to_edges[f"{node_name}.{node_port_name}"] = []

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def reconnect_edges_for_replaced_input(
        self,
        node_name: str,
        old_port: StaticTypeInputPort,
        new_port: StaticTypeInputPort,
    ):
        """Re-evaluate all edges targeting this input port after type change.

        Compatible edges get re-subscribed to the new port.
        Incompatible edges are marked invalid (no callback, edge record preserved).
        """
        port_key = f"{node_name}.{old_port.name}"

        # Full-port edges (value_index=None)
        for edge_key in self._target_port_to_edges.get(port_key, []):
            source_node_name, source_port_name = edge_key[0].split(".")

            if source_node_name == "":
                source_port = self.inputs[source_port_name]
            else:
                source_port = self._nodes[source_node_name].outputs[source_port_name]

            source_port.unsubscribe(id(old_port))
            compatible = port_is_connectable(source_port, new_port)
            if compatible:
                source_port.subscribe(
                    id(new_port),
                    make_edge_dispatch(source_port, new_port) or new_port.dispatch,
                )
            self._edges[edge_key].valid = compatible

        # Sub-value edges (value_index=0, 1, ...)
        for index in range(len(old_port.value_type_list)):
            sub_key = f"{port_key}.{index}"
            for edge_key in self._target_port_to_edges.get(sub_key, []):
                source_node_name, source_port_name = edge_key[0].split(".")

                if source_node_name == "":
                    source_port = self.inputs[source_port_name]
                else:
                    source_port = self._nodes[source_node_name].outputs[
                        source_port_name
                    ]

                source_port.unsubscribe(id(old_port))

                if index < len(new_port.value_type_list):
                    compatible = port_is_connectable_with_index(
                        source_port, new_port, index
                    )
                else:
                    compatible = False

                if compatible:
                    source_port.subscribe(
                        id(new_port),
                        make_index_dispatch(source_port, new_port, index)
                        or (
                            lambda values, idx=index: new_port.receive_value_with_index(
                                idx, values
                            )
                        ),
                    )
                self._edges[edge_key].valid = compatible

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def reconnect_edges_for_replaced_output(
        self,
        node_name: str,
        old_port: StaticTypeOutputPort,
        new_port: StaticTypeOutputPort,
    ):
        """Re-evaluate all edges sourced from this output port after type change.

        Compatible edges get re-subscribed from the new port.
        Incompatible edges are marked invalid (no callback, edge record preserved).
        """
        source_key = f"{node_name}.{old_port.name}"

        for edge_key in self._source_port_to_edges.get(source_key, []):
            target_node_name, target_port_value_name = edge_key[1].split(".", 1)
            target_port_name, target_value_index = self._parse_port_value_name(
                target_port_value_name
            )

            if target_node_name == "":
                # Graph output — full-port connection only (no sub-value)
                target_output = self.outputs[target_port_name]
                old_port.unsubscribe(id(target_output))
                compatible = port_is_connectable(new_port, target_output)
                if compatible:
                    new_port.subscribe(
                        id(target_output),
                        make_edge_dispatch(new_port, target_output)
                        or target_output.dispatch,
                    )
                self._edges[edge_key].valid = compatible
                continue

            # Node input — type narrowed to StaticTypeInputPort
            target_input = self._nodes[target_node_name].inputs[target_port_name]
            old_port.unsubscribe(id(target_input))

            if target_value_index is None:
                compatible = port_is_connectable(new_port, target_input)
                if compatible:
                    new_port.subscribe(
                        id(target_input),
                        make_edge_dispatch(new_port, target_input)
                        or target_input.dispatch,
                    )
            else:
                compatible = port_is_connectable_with_index(
                    new_port, target_input, target_value_index
                )
                if compatible:
                    new_port.subscribe(
                        id(target_input),
                        make_index_dispatch(new_port, target_input, target_value_index)
                        or (
                            lambda values, idx=target_value_index: target_input.receive_value_with_index(
                                idx, values
                            )
                        ),
                    )
            self._edges[edge_key].valid = compatible

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def add_invalid_edge(self, source_key: str, target_key: str):
        """Add an edge record without callback subscription (invalid/disabled edge)."""
        edge_key = (source_key, target_key)
        if edge_key in self._edges:
            return

        self._edges[edge_key] = Edge(valid=False)
        self._source_port_to_edges.setdefault(source_key, []).append(edge_key)
        self._target_port_to_edges.setdefault(target_key, []).append(edge_key)

        if self._persist is not None:
            self._persist.update_edges(self._edges)

    def notify_node_updated(self, node: BaseNode):
        if self._persist is None:
            return

        self._persist.update_node(node)

    def notify_properties_changed(self, node: BaseNode):
        if self._persist is None:
            return

        self._persist.update_properties(node)


def replace_node_input_port(
    node: BaseNode,
    old_input: StaticTypeInputPort,
    new_input: StaticTypeInputPort,
    port_callback: PortCallback | None = None,
):
    if old_input.has_callback(id(node)):
        old_input.unsubscribe(id(node))

    if node.parent_graph is not None:
        node.parent_graph.reconnect_edges_for_replaced_input(
            node.name, old_input, new_input
        )

    if port_callback is not None:
        new_input.subscribe(id(node), port_callback)

    node.inputs[new_input.name] = new_input


def replace_node_output_port(
    node: BaseNode,
    old_output: StaticTypeOutputPort,
    new_output: StaticTypeOutputPort,
    port_callback: PortCallback | None = None,
):
    if old_output.has_callback(id(node)):
        old_output.unsubscribe(id(node))

    if node.parent_graph is not None:
        node.parent_graph.reconnect_edges_for_replaced_output(
            node.name, old_output, new_output
        )

    if port_callback is not None:
        new_output.subscribe(id(node), port_callback)

    node.outputs[new_output.name] = new_output


TGraph = TypeVar("TGraph", bound=BaseNodeGraph)


class BaseNodeFlow(Generic[TGraph]):
    """A named collection of graphs — the container level above the graph.

    Graphs added here receive a ``parent_flow`` back-reference, making the
    flow the resolution scope for graph-to-graph references. Holds only the
    in-memory collection and its lifecycle; insertion order is preserved.
    """

    def __init__(self) -> None:
        self._graphs: dict[str, TGraph] = {}

    @property
    def graphs(self) -> dict[str, TGraph]:
        return self._graphs

    @property
    def graph_names(self) -> KeysView[str]:
        return self._graphs.keys()

    def get_graph(self, name: str) -> TGraph | None:
        return self._graphs.get(name)

    def add_graph(self, graph: TGraph) -> None:
        """Add a graph to this flow, keyed by ``graph.name``.

        Sets the graph's ``parent_flow`` back-reference. Duplicate names
        raise ValueError.
        """
        if graph.name in self._graphs:
            raise ValueError(f"Graph name already exists in flow: {graph.name}")
        self._graphs[graph.name] = graph
        graph.set_parent_flow(self)

    def remove_graph(self, name: str) -> TGraph | None:
        """Remove a graph by name, finalizing it and clearing parent_flow.

        Returns the removed graph, or None if the name is unknown.
        """
        graph = self._graphs.pop(name, None)
        if graph is None:
            return None
        graph.finalize()
        graph.set_parent_flow(None)
        return graph

    def finalize(self) -> None:
        for graph in self._graphs.values():
            graph.finalize()
