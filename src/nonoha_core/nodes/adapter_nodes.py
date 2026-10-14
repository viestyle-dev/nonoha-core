from typing import Any
import logging
import numpy as np

from nonoha_core.node import (
    BaseNode,
    NodeDoc,
    PropertyDataType,
    replace_node_input_port,
    replace_node_output_port,
)
from nonoha_core.data_type import (
    DataType,
    PortValueType,
    name_to_port_value_type,
)
from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)

logger = logging.getLogger(__name__)


class ComposeNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Compose multiple inputs into a single output",
            category="Adapter",
            inputs={"dispatch": "", "in_0": "", "in_1": ""},
            outputs={"out": ""},
        )

    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input types",
            "data_type": "str",
            "default_value": "f32,f32",
        },
        "inputs_to_dispatch": {
            "description": "Comma-separated input indices that trigger dispatch",
            "data_type": "str",
            "default_value": "",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Compose")

        input_dispatch = StaticTypeInputPort("dispatch", [PortValueType(DataType.Any)])
        input_dispatch.subscribe(id(self), self._on_dispatch)

        in_types = [
            name_to_port_value_type(name.strip())
            for name in str(self.properties["in_types"]).split(",")
        ]
        in_ports = [
            StaticTypeInputPort(f"in_{i}", [in_type])
            for i, in_type in enumerate(in_types)
        ]
        out_port = StaticTypeOutputPort("out", in_types)

        for i, port in enumerate(in_ports):
            port.subscribe(
                id(self), lambda values, index=i: self._on_input(values, index)
            )

        self._in_types = in_types
        self._input_dispatch = input_dispatch
        self._in_ports = in_ports
        self._out_port = out_port
        self._in_flags: int = 0x00
        self._in_flags_to_flush = 0x00

        self.inputs[input_dispatch.name] = input_dispatch
        for in_port in in_ports:
            self.inputs[in_port.name] = in_port
        self.outputs[out_port.name] = out_port

    def set_properties(self, properties: dict[str, PropertyDataType]):

        in_flags_to_flush = self._in_flags_to_flush
        inputs_to_dispatch_str = self.properties["inputs_to_dispatch"]
        if "inputs_to_dispatch" in properties:
            inputs_to_dispatch_str = properties["inputs_to_dispatch"]
            if not isinstance(inputs_to_dispatch_str, str):
                raise ValueError("inputs_to_dispatch must be a string")
            if inputs_to_dispatch_str != "":
                inputs_to_dispatch = [
                    int(name.strip()) for name in inputs_to_dispatch_str.split(",")
                ]
                in_flags_to_flush = 0x00
                for i in inputs_to_dispatch:
                    in_flags_to_flush |= 1 << i

        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string")
            in_types = [
                name_to_port_value_type(name.strip())
                for name in in_types_str.split(",")
            ]

            if len(in_types) > 16:
                raise ValueError("Too many input ports. Maximum is 16")

        if in_types != self._in_types:
            new_in_ports = [
                StaticTypeInputPort(f"in_{i}", [in_type])
                for i, in_type in enumerate(in_types)
            ]
            new_out_port = StaticTypeOutputPort("out", in_types)

            # Replace output port (name fixed)
            replace_node_output_port(self, self._out_port, new_out_port)

            # Replace overlapping input ports, remove extras, add new
            old_count = len(self._in_ports)
            new_count = len(new_in_ports)
            overlap = min(old_count, new_count)

            for i in range(overlap):
                replace_node_input_port(
                    self,
                    self._in_ports[i],
                    new_in_ports[i],
                    lambda values, index=i: self._on_input(values, index),
                )
            for i in range(overlap, old_count):
                if self.parent_graph is not None:
                    self.parent_graph.disconnect_all_from_node_input(
                        self.name, self._in_ports[i].name
                    )
                self._in_ports[i].unsubscribe(id(self))
                self.inputs.pop(self._in_ports[i].name)
            for i in range(overlap, new_count):
                new_in_ports[i].subscribe(
                    id(self), lambda values, index=i: self._on_input(values, index)
                )
                self.inputs[new_in_ports[i].name] = new_in_ports[i]

            self._in_flags = 0x00
            self._in_ports = new_in_ports
            self._out_port = new_out_port
            self._in_types = in_types

        if in_flags_to_flush != self._in_flags_to_flush:
            self._in_flags_to_flush = in_flags_to_flush

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])
        self.properties["inputs_to_dispatch"] = inputs_to_dispatch_str

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_dispatch(self, values_any: list[PortValue]):
        values = [
            (in_port.current_values[0] if in_port.current_values is not None else None)
            for in_port in self._in_ports
        ]

        if any(value is None for value in values):
            logger.debug(f"{self.name}: Not all inputs received. {values=}")
            return

        self._out_port.dispatch(values)  # type: ignore

    def _on_input(self, values_any: list[Any], index: int):
        current_bit = 1 << index

        if self._in_flags_to_flush & current_bit:
            values = [
                (
                    in_port.current_values[0]
                    if in_port.current_values is not None
                    else None
                )
                for in_port in self._in_ports
            ]
            if any(value is None for value in values):
                logger.debug(f"{self.name}: Not all inputs received")
                return
            self._in_flags = 0x00
            self._out_port.dispatch(values)  # type: ignore


class DecomposeNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Decompose a single input into multiple individual outputs",
            category="Adapter",
            inputs={"in": ""},
            outputs={"completed": "", "out_0": "", "out_1": ""},
        )

    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input types",
            "data_type": "str",
            "default_value": "f32,f32",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Decompose")

        in_types = [
            name_to_port_value_type(name.strip())
            for name in str(self.properties["in_types"]).split(",")
        ]
        input_values = StaticTypeInputPort("in", in_types)
        input_values.subscribe(id(self), self._on_input_values)

        output_completed = StaticTypeOutputPort(
            "completed", [PortValueType(DataType.Bool)]
        )

        output_values_list = [
            StaticTypeOutputPort(f"out_{i}", [in_type])
            for i, in_type in enumerate(in_types)
        ]

        self._input_values = input_values
        self._output_values_list = output_values_list
        self._output_completed = output_completed
        self._in_types = in_types

        self.inputs[input_values.name] = input_values
        self.outputs[output_completed.name] = output_completed
        for output_values in output_values_list:
            self.outputs[output_values.name] = output_values

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types

        if "in_types" in properties:
            if not isinstance(properties["in_types"], str):
                raise ValueError("in_types must be a string")
            in_types = [
                name_to_port_value_type(name.strip())
                for name in properties["in_types"].split(",")
            ]

            if len(in_types) < 1:
                raise ValueError("in_types must have at least one element")

        if in_types != self._in_types:
            new_input = StaticTypeInputPort("in", in_types)
            new_output_list = [
                StaticTypeOutputPort(f"out_{i}", [in_type])
                for i, in_type in enumerate(in_types)
            ]

            # Replace input port (name fixed)
            replace_node_input_port(
                self, self._input_values, new_input, self._on_input_values
            )

            # Replace overlapping output ports, remove extras, add new
            old_count = len(self._output_values_list)
            new_count = len(new_output_list)
            overlap = min(old_count, new_count)

            for i in range(overlap):
                replace_node_output_port(
                    self, self._output_values_list[i], new_output_list[i]
                )
            for i in range(overlap, old_count):
                if self.parent_graph is not None:
                    self.parent_graph.disconnect_all_from_node_output(
                        self.name, self._output_values_list[i].name
                    )
                self.outputs.pop(self._output_values_list[i].name)
            for i in range(overlap, new_count):
                self.outputs[new_output_list[i].name] = new_output_list[i]

            self._input_values = new_input
            self._output_values_list = new_output_list
            self._in_types = in_types

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, values_any: list[PortValue]):
        for i, output_values in enumerate(self._output_values_list):
            output_values.dispatch([values_any[i]])

        self._output_completed.dispatch([np.array([True])])
