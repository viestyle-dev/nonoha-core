import numpy as np
import logging

from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)
from nonoha_core.node import (
    BaseNode,
    NodeDoc,
    replace_node_input_port,
    replace_node_output_port,
)
from nonoha_core.data_type import (
    NUMBER_DATA_TYPES,
    DataType,
    PortValueType,
    PropertyDataType,
    name_to_port_value_type,
)

logger = logging.getLogger(__name__)

# <https://numpy.org/doc/stable/reference/routines.math.html#arithmetic-operations>


class AddNode(BaseNode):
    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input port value types (e.g. 'f32,f32,f32'). All entries must share the same data type. Supports 2+ inputs for N-ary addition. Changing this rebuilds input/output ports.",
            "data_type": "str",
            "default_value": "f32,f32",
        },
    }

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="N-ary element-wise addition via np.add (left fold). Supports 2+ inputs of the same numeric/bool type with numpy broadcasting.",
            category="Arithmetic",
            inputs={
                "values": "Numeric arrays to sum. Count and types set by in_types."
            },
            outputs={"value": "Element-wise sum with broadcast shape."},
        )

    def __init__(self, name: str):
        super().__init__(name, "Add")

        in_types = [PortValueType(DataType.Float32), PortValueType(DataType.Float32)]

        input_values = StaticTypeInputPort("values", in_types)
        input_values.subscribe(id(self), self._on_input_values)

        out_type = self._get_out_type(in_types)
        output_value = StaticTypeOutputPort("value", [out_type])

        self._input_values = input_values
        self._output_value = output_value
        self._in_types = in_types

        self.inputs[input_values.name] = input_values
        self.outputs[output_value.name] = output_value

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

    def _get_out_type(self, in_types: list[PortValueType]) -> PortValueType:
        if len(in_types) == 0:
            raise ValueError("No input types provided")

        data_type = in_types[0].data_type
        for in_type in in_types:
            if in_type.data_type != data_type:
                raise ValueError("All input types must be the same")

        if data_type not in NUMBER_DATA_TYPES and data_type not in {
            DataType.Bool,
        }:
            raise ValueError(f"Unsupported data type: {data_type}")

        out_shape = np.broadcast_shapes(*[(1, *in_type.shape) for in_type in in_types])

        return PortValueType(data_type, out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string")

            in_types = [
                name_to_port_value_type(in_type_str)
                for in_type_str in in_types_str.split(",")
            ]

        if in_types != self._in_types:
            out_type = self._get_out_type(in_types)
            new_input_values = StaticTypeInputPort("values", in_types)
            new_output_value = StaticTypeOutputPort("value", [out_type])

            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values

            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        self._in_types = in_types
        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, values: list[PortValue]):
        try:
            out = values[0]
            for value in values[1:]:
                out = np.add(out, value)
        except Exception as e:
            logger.warning(f"{self.name}: Error while adding numbers: {e}")
            return

        self._output_value.dispatch([out])


class SubtractNode(BaseNode):
    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input port value types (e.g. 'f32,f32'). Exactly 2 entries required, same data type. Changing this rebuilds input/output ports.",
            "data_type": "str",
            "default_value": "f32,f32",
        },
    }

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise subtraction via np.subtract. Exactly 2 inputs (minuend, subtrahend) of the same numeric/bool type with numpy broadcasting.",
            category="Arithmetic",
            inputs={
                "values": "Exactly 2 arrays: [minuend, subtrahend]. Types set by in_types."
            },
            outputs={
                "value": "Element-wise difference (values[0] - values[1]) with broadcast shape."
            },
        )

    def __init__(self, name: str):
        super().__init__(name, "Subtract")

        in_types = [PortValueType(DataType.Float32), PortValueType(DataType.Float32)]

        input_values = StaticTypeInputPort("values", in_types)
        input_values.subscribe(id(self), self._on_input_values)

        out_type = self._get_out_type(in_types)
        output_value = StaticTypeOutputPort("value", [out_type])

        self._input_values = input_values
        self._output_value = output_value
        self._in_types = in_types

        self.inputs[input_values.name] = input_values
        self.outputs[output_value.name] = output_value

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

    def _get_out_type(self, in_types: list[PortValueType]) -> PortValueType:
        if len(in_types) != 2:
            raise ValueError("Exactly two input types are required")

        data_type = in_types[0].data_type
        for in_type in in_types:
            if in_type.data_type != data_type:
                raise ValueError("All input types must be the same")

        if data_type not in NUMBER_DATA_TYPES and data_type not in {
            DataType.Bool,
        }:
            raise ValueError(f"Unsupported data type: {data_type}")
        out_shape = np.broadcast_shapes(*[(1, *in_type.shape) for in_type in in_types])
        return PortValueType(data_type, out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string")

            in_types = [
                name_to_port_value_type(in_type_str)
                for in_type_str in in_types_str.split(",")
            ]

        if in_types != self._in_types:
            out_type = self._get_out_type(in_types)
            new_input_values = StaticTypeInputPort("values", in_types)
            new_output_value = StaticTypeOutputPort("value", [out_type])

            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values

            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        self._in_types = in_types
        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, values: list[PortValue]):
        try:
            out = values[0]
            for value in values[1:]:
                out = np.subtract(out, value)
        except Exception as e:
            logger.warning(f"{self.name}: Error while subtracting numbers: {e}")
            return

        self._output_value.dispatch([out])
        # print(f"{out=}")


class MultiplyNode(BaseNode):
    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input port value types (e.g. 'f32,f32,f32'). All entries must share the same data type. Supports 2+ inputs for N-ary multiplication. Changing this rebuilds input/output ports.",
            "data_type": "str",
            "default_value": "f32,f32",
        },
    }

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="N-ary element-wise multiplication via np.multiply (left fold). Supports 2+ inputs of the same numeric/bool type with numpy broadcasting.",
            category="Arithmetic",
            inputs={
                "values": "Numeric arrays to multiply. Count and types set by in_types."
            },
            outputs={"value": "Element-wise product with broadcast shape."},
        )

    def __init__(self, name: str):
        super().__init__(name, "Multiply")

        in_types = [PortValueType(DataType.Float32), PortValueType(DataType.Float32)]

        input_values = StaticTypeInputPort("values", in_types)
        input_values.subscribe(id(self), self._on_input_values)

        out_type = self._get_out_type(in_types)
        output_value = StaticTypeOutputPort("value", [out_type])

        self._input_values = input_values
        self._output_value = output_value
        self._in_types = in_types

        self.inputs[input_values.name] = input_values
        self.outputs[output_value.name] = output_value

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

    def _get_out_type(self, in_types: list[PortValueType]) -> PortValueType:
        if len(in_types) == 0:
            raise ValueError("No input types provided")

        data_type = in_types[0].data_type
        for in_type in in_types:
            if in_type.data_type != data_type:
                raise ValueError("All input types must be the same")

        if data_type not in NUMBER_DATA_TYPES and data_type not in {
            DataType.Bool,
        }:
            raise ValueError(f"Unsupported data type: {data_type}")

        out_shape = np.broadcast_shapes(*[(1, *in_type.shape) for in_type in in_types])

        return PortValueType(data_type, out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string")

            in_types = [
                name_to_port_value_type(in_type_str)
                for in_type_str in in_types_str.split(",")
            ]

        if in_types != self._in_types:
            out_type = self._get_out_type(in_types)
            new_input_values = StaticTypeInputPort("values", in_types)
            new_output_value = StaticTypeOutputPort("value", [out_type])

            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values

            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        self._in_types = in_types
        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, values: list[PortValue]):
        try:
            out = values[0]
            for value in values[1:]:
                out = np.multiply(out, value)
        except Exception as e:
            logger.warning(f"{self.name}: Error while multiplying numbers: {e}")
            return

        self._output_value.dispatch([out])
        # print(f"{out=}")


class DivideNode(BaseNode):
    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input port value types (e.g. 'f32,f32'). Exactly 2 entries required, same data type. Changing this rebuilds input/output ports.",
            "data_type": "str",
            "default_value": "f32,f32",
        },
    }

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise division via np.divide. Exactly 2 inputs (dividend, divisor) of the same numeric/bool type with numpy broadcasting.",
            category="Arithmetic",
            inputs={
                "values": "Exactly 2 arrays: [dividend, divisor]. Types set by in_types."
            },
            outputs={
                "value": "Element-wise quotient (values[0] / values[1]) with broadcast shape."
            },
        )

    def __init__(self, name: str):
        super().__init__(name, "Divide")

        in_types = [PortValueType(DataType.Float32), PortValueType(DataType.Float32)]

        input_values = StaticTypeInputPort("values", in_types)
        input_values.subscribe(id(self), self._on_input_values)

        out_type = self._get_out_type(in_types)
        output_value = StaticTypeOutputPort("value", [out_type])

        self._input_values = input_values
        self._output_value = output_value
        self._in_types = in_types

        self.inputs[input_values.name] = input_values
        self.outputs[output_value.name] = output_value

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

    def _get_out_type(self, in_types: list[PortValueType]) -> PortValueType:
        if len(in_types) != 2:
            raise ValueError("Exactly two input types are required")

        data_type = in_types[0].data_type
        for in_type in in_types:
            if in_type.data_type != data_type:
                raise ValueError("All input types must be the same")

        if data_type not in NUMBER_DATA_TYPES and data_type not in {
            DataType.Bool,
        }:
            raise ValueError(f"Unsupported data type: {data_type}")

        out_shape = np.broadcast_shapes(*[(1, *in_type.shape) for in_type in in_types])
        return PortValueType(data_type, out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string")

            in_types = [
                name_to_port_value_type(in_type_str)
                for in_type_str in in_types_str.split(",")
            ]

        if in_types != self._in_types:
            out_type = self._get_out_type(in_types)
            new_input_values = StaticTypeInputPort("values", in_types)
            new_output_value = StaticTypeOutputPort("value", [out_type])

            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values

            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        self._in_types = in_types
        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, values: list[PortValue]):
        try:
            out = values[0]
            for value in values[1:]:
                out = np.divide(out, value)
        except Exception as e:
            logger.warning(f"{self.name}: Error while dividing numbers: {e}")
            return

        self._output_value.dispatch([out])
        # print(f"{out=}")


class ReciprocalNode(BaseNode):
    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input port value types (e.g. 'f32' or 'f32,f64'). Each slot is independently transformed. Changing this rebuilds input/output ports.",
            "data_type": "str",
            "default_value": "f32",
        },
    }

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise reciprocal (1/x) via np.reciprocal. Each input slot is independently transformed. Output types mirror input types.",
            category="Arithmetic",
            inputs={"values": "Numeric arrays. Count and types set by in_types."},
            outputs={"values": "Element-wise reciprocals, one per input slot."},
        )

    def __init__(self, name: str):
        super().__init__(name, "Reciprocal")

        in_types = [PortValueType(DataType.Float32)]

        input_values = StaticTypeInputPort("values", in_types)
        input_values.subscribe(id(self), self._on_input_values)

        output_values = StaticTypeOutputPort("values", in_types)

        self._input_values = input_values
        self._output_values = output_values
        self._in_types = in_types

        self.inputs[input_values.name] = input_values
        self.outputs[output_values.name] = output_values

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types

        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string")

            in_types = [
                name_to_port_value_type(in_type_str)
                for in_type_str in in_types_str.split(",")
            ]

        if in_types != self._in_types:
            new_input_values = StaticTypeInputPort("values", in_types)
            new_output_values = StaticTypeOutputPort("values", in_types)

            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values

            replace_node_output_port(self, self._output_values, new_output_values)
            self._output_values = new_output_values

        self._in_types = in_types
        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, values: list[PortValue]):
        try:
            # Process each value separately when multiple inputs are configured
            out_values = [np.reciprocal(v) for v in values]
        except Exception as e:
            logger.warning(f"{self.name}: Error while calculating reciprocal: {e}")
            return

        self._output_values.dispatch(out_values)


class NegativeNode(BaseNode):
    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input port value types (e.g. 'f32' or 'i32,i32'). Each slot is independently transformed. Changing this rebuilds input/output ports.",
            "data_type": "str",
            "default_value": "f32",
        },
    }

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise negation via np.negative. Each input slot is independently transformed. Output types mirror input types.",
            category="Arithmetic",
            inputs={"values": "Numeric arrays. Count and types set by in_types."},
            outputs={"values": "Element-wise negations, one per input slot."},
        )

    def __init__(self, name: str):
        super().__init__(name, "Negative")

        in_types = [PortValueType(DataType.Float32)]
        input_values = StaticTypeInputPort("values", in_types)
        input_values.subscribe(id(self), self._on_input_values)
        output_values = StaticTypeOutputPort("values", in_types)
        self._input_values = input_values
        self._output_values = output_values
        self._in_types = in_types
        self.inputs[input_values.name] = input_values
        self.outputs[output_values.name] = output_values
        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string")
            in_types = [
                name_to_port_value_type(in_type_str)
                for in_type_str in in_types_str.split(",")
            ]
        if in_types != self._in_types:
            new_input_values = StaticTypeInputPort("values", in_types)
            new_output_values = StaticTypeOutputPort("values", in_types)

            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values

            replace_node_output_port(self, self._output_values, new_output_values)
            self._output_values = new_output_values

        self._in_types = in_types
        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, values: list[PortValue]):
        out_values = [np.negative(v) for v in values]

        self._output_values.dispatch(out_values)
