from dataclasses import dataclass, field
import logging
from typing import Any, Callable, TypeAlias

from .node import BaseNode
from .data_type import PropertyDataType

logger = logging.getLogger(__name__)

NodeFactory: TypeAlias = Callable[[str], BaseNode]


@dataclass
class PortMetadata:
    name: str
    description: str
    value_types: list[str]
    value_names: list[str | None]


@dataclass
class PropertyMetadata:
    default: PropertyDataType
    description: str


@dataclass
class NodeMetadata:
    description: str
    category: str
    inputs: list[PortMetadata]
    outputs: list[PortMetadata]
    properties: dict[str, PropertyMetadata]


@dataclass
class NodeDefinition:
    type_name: str
    factory: NodeFactory
    metadata: NodeMetadata


class NodeRegistry:
    def __init__(self):
        self._node_definitions: dict[str, NodeDefinition] = {}

    def register_node(self, type_name: str, factory: NodeFactory):
        if type_name in self._node_definitions:
            raise ValueError(f"Node type {type_name} already registered")

        metadata = self._extract_metadata(type_name, factory)
        self._node_definitions[type_name] = NodeDefinition(
            type_name, factory, metadata
        )

    def _extract_metadata(
        self, type_name: str, factory: NodeFactory
    ) -> NodeMetadata:
        """Extract metadata by creating a temporary instance (KNIME-style).

        __init__ must be side-effect-free. If it has side effects (e.g.,
        asyncio.get_running_loop()), this will raise RuntimeError, which
        signals the developer to move the side effect to activate().
        """
        try:
            temp = factory(f"_meta_{type_name}")
        except RuntimeError as e:
            raise RuntimeError(
                f"Node '{type_name}' __init__ has side effects that prevent "
                f"metadata extraction. Move runtime initialization to "
                f"activate(). Error: {e}"
            ) from e

        node_class = type(temp)

        doc = node_class.describe(temp.properties)
        input_descs = doc.inputs if doc else {}
        output_descs = doc.outputs if doc else {}

        inputs = [
            PortMetadata(
                name=port.name,
                description=input_descs.get(port.name, ""),
                value_types=[vt.name for vt in port.value_type_list],
                value_names=list(port.value_name_list),
            )
            for port in temp.inputs.values()
        ]

        outputs = [
            PortMetadata(
                name=port.name,
                description=output_descs.get(port.name, ""),
                value_types=[vt.name for vt in port.value_type_list],
                value_names=list(port.value_name_list),
            )
            for port in temp.outputs.values()
        ]

        properties = {
            name: PropertyMetadata(
                default=value,
                description=node_class.PROPERTIES.get(name, {}).get("description", ""),
            )
            for name, value in temp.properties.items()
        }

        metadata = NodeMetadata(
            description=doc.description if doc else "",
            category=doc.category if doc else "",
            inputs=inputs,
            outputs=outputs,
            properties=properties,
        )

        temp.finalize()
        return metadata

    def create_node(self, type_name: str, name: str) -> BaseNode:
        if type_name not in self._node_definitions:
            raise ValueError(f"Node type {type_name} is not registered")
        return self._node_definitions[type_name].factory(name)

    @property
    def node_definitions(self):
        return self._node_definitions
