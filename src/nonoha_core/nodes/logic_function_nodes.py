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
    DataType,
    PortValueType,
    PropertyDataType,
    name_to_port_value_type,
)

logger = logging.getLogger(__name__)

# <https://numpy.org/doc/stable/reference/routines.logic.html>


class EqualNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="in[0] == in[1]",
            category="Logic",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Equal")

        in_types = [PortValueType(DataType.Float32), PortValueType(DataType.Float32)]
        out_type = self._get_out_type(in_types)

        input_in = StaticTypeInputPort("in", in_types)
        output_out = StaticTypeOutputPort("out", [out_type])

        input_in.subscribe(id(self), self._on_input_in)

        self._in_types = in_types
        self._input_in = input_in
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

    def _get_out_type(self, in_types: list[PortValueType]):
        if len(in_types) != 2:
            raise ValueError("LessNode requires exactly two input types.")

        out_shape = np.broadcast_shapes(*[(1, *in_type.shape) for in_type in in_types])
        return PortValueType(DataType.Bool, out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string.")

            in_types = [
                name_to_port_value_type(name.strip())
                for name in in_types_str.split(",")
            ]

        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_types != self._in_types:
            out_type = self._get_out_type(in_types)

            new_input_in = StaticTypeInputPort("in", in_types)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in
        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out, None)
            self._output_out = new_output_out
        self._in_types = in_types
        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        a, b = values
        out = np.equal(a, b)
        self._output_out.dispatch([out])


class NotEqualNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="in[0] != in[1]",
            category="Logic",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "NotEqual")

        in_types = [PortValueType(DataType.Float32), PortValueType(DataType.Float32)]
        out_type = self._get_out_type(in_types)

        input_in = StaticTypeInputPort("in", in_types)
        output_out = StaticTypeOutputPort("out", [out_type])

        input_in.subscribe(id(self), self._on_input_in)

        self._in_types = in_types
        self._input_in = input_in
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

    def _get_out_type(self, in_types: list[PortValueType]):
        if len(in_types) != 2:
            raise ValueError("LessNode requires exactly two input types.")

        out_shape = np.broadcast_shapes(*[(1, *in_type.shape) for in_type in in_types])
        return PortValueType(DataType.Bool, out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string.")

            in_types = [
                name_to_port_value_type(name.strip())
                for name in in_types_str.split(",")
            ]

        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_types != self._in_types:
            out_type = self._get_out_type(in_types)

            new_input_in = StaticTypeInputPort("in", in_types)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in
        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out, None)
            self._output_out = new_output_out
        self._in_types = in_types
        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        a, b = values

        try:
            out = np.not_equal(a, b)
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return

        self._output_out.dispatch([out])


class LessNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="in[0] < in[1]",
            category="Logic",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Less")

        in_types = [PortValueType(DataType.Float32), PortValueType(DataType.Float32)]
        out_type = self._get_out_type(in_types)

        input_in = StaticTypeInputPort("in", in_types)
        output_out = StaticTypeOutputPort("out", [out_type])

        input_in.subscribe(id(self), self._on_input_in)

        self._in_types = in_types
        self._input_in = input_in
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

    def _get_out_type(self, in_types: list[PortValueType]):
        if len(in_types) != 2:
            raise ValueError("LessNode requires exactly two input types.")

        out_shape = np.broadcast_shapes(*[(1, *in_type.shape) for in_type in in_types])
        return PortValueType(DataType.Bool, out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string.")

            in_types = [
                name_to_port_value_type(name.strip())
                for name in in_types_str.split(",")
            ]

        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_types != self._in_types:
            out_type = self._get_out_type(in_types)

            new_input_in = StaticTypeInputPort("in", in_types)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out, None)
            self._output_out = new_output_out

        self._in_types = in_types

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_in(self, values: list[PortValue]):
        a = values[0]
        b = values[1]

        out = np.less(a, b)
        self._output_out.dispatch([out])


class GreaterNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="in[0] > in[1]",
            category="Logic",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Greater")

        in_types = [PortValueType(DataType.Float32), PortValueType(DataType.Float32)]
        out_type = self._get_out_type(in_types)

        input_in = StaticTypeInputPort("in", in_types)
        output_out = StaticTypeOutputPort("out", [out_type])

        input_in.subscribe(id(self), self._on_input_in)

        self._in_types = in_types
        self._input_in = input_in
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

    def _get_out_type(self, in_types: list[PortValueType]):
        if len(in_types) != 2:
            raise ValueError("GreaterNode requires exactly two input types.")

        out_shape = np.broadcast_shapes(*[(1, *in_type.shape) for in_type in in_types])
        return PortValueType(DataType.Bool, out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string.")

            in_types = [
                name_to_port_value_type(name.strip())
                for name in in_types_str.split(",")
            ]

        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_types != self._in_types:
            out_type = self._get_out_type(in_types)

            new_input_in = StaticTypeInputPort("in", in_types)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        if new_input_in != self._input_in:
            self._input_in.unsubscribe(id(self))
            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_input(
                    self.name, self._input_in.name
                )

            new_input_in.subscribe(id(self), self._on_input_in)
            self._input_in = new_input_in
            self.inputs[new_input_in.name] = new_input_in

        if new_output_out != self._output_out:
            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_output(
                    self.name, self._output_out.name
                )

            self._output_out = new_output_out
            self.outputs[new_output_out.name] = new_output_out

        self._in_types = in_types

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_in(self, values: list[PortValue]):
        a = values[0]
        b = values[1]

        out = np.greater(a, b)
        self._output_out.dispatch([out])


class WithinRangeNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Test whether x is within [lower, upper] range (boundary inclusivity configurable)",
            category="Logic",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "WithinRange")

        inclusive_lower = False
        inclusive_upper = False

        x_type = PortValueType(DataType.Float32)
        upper_type = PortValueType(DataType.Float32)
        lower_type = PortValueType(DataType.Float32)
        out_type = self._get_out_type(x_type, lower_type, upper_type)

        input_in = StaticTypeInputPort(
            "in",
            [x_type, lower_type, upper_type],
            value_name_list=["x", "lower", "upper"],
        )
        output_out = StaticTypeOutputPort("out", [out_type])
        input_in.subscribe(id(self), self._on_input_in)

        self._input_in = input_in
        self._output_out = output_out
        self._inclusive_lower = inclusive_lower
        self._inclusive_upper = inclusive_upper

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["x_type"] = x_type.name
        self.properties["lower_type"] = lower_type.name
        self.properties["upper_type"] = upper_type.name
        self.properties["inclusive_lower"] = inclusive_lower
        self.properties["inclusive_upper"] = inclusive_upper

    def _get_out_type(
        self,
        x_type: PortValueType,
        lower_type: PortValueType,
        upper_type: PortValueType,
    ):
        out_shape = np.broadcast_shapes(
            (1, *x_type.shape), (1, *lower_type.shape), (1, *upper_type.shape)
        )
        return PortValueType(DataType.Bool, out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        x_type = self._input_in.value_type_list[0]
        lower_type = self._input_in.value_type_list[1]
        upper_type = self._input_in.value_type_list[2]

        if "x_type" in properties:
            x_type_str = properties["x_type"]
            if not isinstance(x_type_str, str):
                raise ValueError("x_type must be a string.")
            x_type = name_to_port_value_type(x_type_str)
        if "lower_type" in properties:
            lower_type_str = properties["lower_type"]
            if not isinstance(lower_type_str, str):
                raise ValueError("lower_type must be a string.")
            lower_type = name_to_port_value_type(lower_type_str)
        if "upper_type" in properties:
            upper_type_str = properties["upper_type"]
            if not isinstance(upper_type_str, str):
                raise ValueError("upper_type must be a string.")
            upper_type = name_to_port_value_type(upper_type_str)

        inclusive_lower = self._inclusive_lower
        inclusive_upper = self._inclusive_upper

        if "inclusive_lower" in properties:
            inclusive_lower = bool(properties["inclusive_lower"])
        if "inclusive_upper" in properties:
            inclusive_upper = bool(properties["inclusive_upper"])

        new_input_in = self._input_in
        if (
            x_type != self._input_in.value_type_list[0]
            or lower_type != self._input_in.value_type_list[1]
            or upper_type != self._input_in.value_type_list[2]
        ):
            new_input_in = StaticTypeInputPort(
                "in",
                [x_type, lower_type, upper_type],
                ["x", "lower", "upper"],
            )

        new_output_out = self._output_out
        if (
            x_type != self._input_in.value_type_list[0]
            or lower_type != self._input_in.value_type_list[1]
            or upper_type != self._input_in.value_type_list[2]
        ):
            out_type = self._get_out_type(x_type, lower_type, upper_type)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        if new_input_in != self._input_in:
            self._input_in.unsubscribe(id(self))
            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_input(
                    self.name, self._input_in.name
                )

            new_input_in.subscribe(id(self), self._on_input_in)
            self._input_in = new_input_in
            self.inputs[new_input_in.name] = new_input_in

        if new_output_out != self._output_out:
            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_output(
                    self.name, self._output_out.name
                )

            self._output_out = new_output_out
            self.outputs[new_output_out.name] = new_output_out

        self._inclusive_lower = inclusive_lower
        self._inclusive_upper = inclusive_upper
        self.properties["x_type"] = x_type.name
        self.properties["lower_type"] = lower_type.name
        self.properties["upper_type"] = upper_type.name
        self.properties["inclusive_lower"] = inclusive_lower
        self.properties["inclusive_upper"] = inclusive_upper

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_in(self, values: list[PortValue]):
        x, lower, upper = values

        # Select the boundary comparison functions from the inclusivity flags
        lower_compare = np.greater_equal if self._inclusive_lower else np.greater
        upper_compare = np.less_equal if self._inclusive_upper else np.less

        # Combine both conditions in a single call
        out = np.logical_and(lower_compare(x, lower), upper_compare(x, upper))

        self._output_out.dispatch([out])


class LogicalAndNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise logical AND of boolean inputs",
            category="Logic",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "LogicalAnd")

        in_types = [PortValueType(DataType.Bool), PortValueType(DataType.Bool)]
        out_type = self._get_out_type(in_types)

        input_in = StaticTypeInputPort("in", in_types)
        output_out = StaticTypeOutputPort("out", [out_type])

        input_in.subscribe(id(self), self._on_input_in)

        self._in_types = in_types
        self._input_in = input_in
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])
        in_types = [PortValueType(DataType.Bool)]

    def _get_out_type(self, in_types: list[PortValueType]):
        if len(in_types) < 2:
            raise ValueError("LogicalAndNode requires exactly two input types.")
        if any(in_type.data_type != DataType.Bool for in_type in in_types):
            raise ValueError("LogicalAndNode requires boolean input types.")

        out_shape = np.broadcast_shapes(*[(1, *in_type.shape) for in_type in in_types])
        return PortValueType(DataType.Bool, out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string.")

            in_types = [
                name_to_port_value_type(name.strip())
                for name in in_types_str.split(",")
            ]

        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_types != self._in_types:
            out_type = self._get_out_type(in_types)

            new_input_in = StaticTypeInputPort("in", in_types)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out, None)
            self._output_out = new_output_out

        self._in_types = in_types

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_in(self, values: list[PortValue]):
        out = values[0]
        for value in values[1:]:
            out = np.logical_and(out, value)
        self._output_out.dispatch([out])


class LogicalOrNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise logical OR of boolean inputs",
            category="Logic",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "LogicalOr")

        in_types = [PortValueType(DataType.Bool), PortValueType(DataType.Bool)]
        out_type = self._get_out_type(in_types)

        input_in = StaticTypeInputPort("in", in_types)
        output_out = StaticTypeOutputPort("out", [out_type])

        input_in.subscribe(id(self), self._on_input_in)

        self._in_types = in_types
        self._input_in = input_in
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])
        in_types = [PortValueType(DataType.Bool)]

    def _get_out_type(self, in_types: list[PortValueType]):
        if len(in_types) < 2:
            raise ValueError("LogicalOrNode requires exactly two input types.")
        if any(in_type.data_type != DataType.Bool for in_type in in_types):
            raise ValueError("LogicalOrNode requires boolean input types.")

        out_shape = np.broadcast_shapes(*[(1, *in_type.shape) for in_type in in_types])
        return PortValueType(DataType.Bool, out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string.")

            in_types = [
                name_to_port_value_type(name.strip())
                for name in in_types_str.split(",")
            ]

        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_types != self._in_types:
            out_type = self._get_out_type(in_types)

            new_input_in = StaticTypeInputPort("in", in_types)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out, None)
            self._output_out = new_output_out

        self._in_types = in_types

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_in(self, values: list[PortValue]):
        out = values[0]
        for value in values[1:]:
            out = np.logical_or(out, value)
        self._output_out.dispatch([out])


class LogicalNotNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise logical NOT of boolean input",
            category="Logic",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "LogicalNot")

        in_type = PortValueType(DataType.Bool)
        out_type = in_type
        input_in = StaticTypeInputPort("in", [in_type])
        output_out = StaticTypeOutputPort("out", [out_type])
        input_in.subscribe(id(self), self._on_input_in)

        self._in_type = in_type
        self._input_in = input_in
        self._output_out = output_out
        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_type"] = in_type.name

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("in_type must be a string.")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type != DataType.Bool:
                raise ValueError("in_type must be a boolean type.")

        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_out = StaticTypeOutputPort("out", [in_type])

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out, None)
            self._output_out = new_output_out

        self._in_type = in_type

        self.properties["in_type"] = in_type.name

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_in(self, values: list[PortValue]):
        out = np.logical_not(values[0])
        self._output_out.dispatch([out])


class AllNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Test whether all elements are true along an axis",
            category="Logic",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "All")

        axis: int | None = 1
        in_type = PortValueType(DataType.Bool, shape=(2,))
        out_type = self._get_out_type(in_type, axis)

        input_in = StaticTypeInputPort("in", [in_type])
        input_in.subscribe(id(self), self._on_input_in)
        output_out = StaticTypeOutputPort("out", [out_type])

        self._in_type = in_type
        self._axis = axis
        self._input_in = input_in
        self._output_out = output_out
        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis

    def _get_out_type(self, in_type: PortValueType, axis: int | None):
        if axis is None:
            return PortValueType(DataType.Bool)

        if axis < 0:
            raise ValueError("axis must be greater than 0.")

        if axis == 0:
            return PortValueType(DataType.Bool, in_type.shape)

        np_shape = [1, *in_type.shape]
        del np_shape[axis]

        return PortValueType(DataType.Bool, tuple(np_shape[1:]))

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("in_type must be a string.")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type != DataType.Bool:
                raise ValueError("in_type must be a boolean type.")

        axis = self._axis
        if "axis" in properties:
            axis = None if (val := properties.get("axis", "")) == "" else int(val)

        new_input_in = self._input_in
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])

        new_output_out = self._output_out
        if in_type != self._in_type or axis != self._axis:
            out_type = self._get_out_type(in_type, axis)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        self._in_type = in_type
        self._axis = axis
        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis if axis is not None else ""

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        out = np.all(values[0], axis=self._axis)

        if self._axis is None or self._axis == 0:
            out = np.expand_dims(out, axis=0)

        # print(f"{out=}")
        self._output_out.dispatch([out])


class AnyNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Test whether any element is true along an axis",
            category="Logic",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Any")

        axis: int | None = 1
        in_type = PortValueType(DataType.Bool, shape=(2,))
        out_type = self._get_out_type(in_type, axis)

        input_in = StaticTypeInputPort("in", [in_type])
        input_in.subscribe(id(self), self._on_input_in)
        output_out = StaticTypeOutputPort("out", [out_type])

        self._in_type = in_type
        self._axis = axis
        self._input_in = input_in
        self._output_out = output_out
        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis

    def _get_out_type(self, in_type: PortValueType, axis: int | None):
        if axis is None:
            return PortValueType(DataType.Bool)

        if axis < 0:
            raise ValueError("axis must be greater than 0.")

        if axis == 0:
            return PortValueType(DataType.Bool, in_type.shape)

        np_shape = [1, *in_type.shape]
        del np_shape[axis]

        return PortValueType(DataType.Bool, tuple(np_shape[1:]))

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("in_type must be a string.")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type != DataType.Bool:
                raise ValueError("in_type must be a boolean type.")

        axis = self._axis
        if "axis" in properties:
            axis = None if (val := properties.get("axis", "")) == "" else int(val)

        new_input_in = self._input_in
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])

        new_output_out = self._output_out
        if in_type != self._in_type or axis != self._axis:
            out_type = self._get_out_type(in_type, axis)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        self._in_type = in_type
        self._axis = axis
        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis if axis is not None else ""

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        out = np.any(values[0], axis=self._axis)

        if self._axis is None or self._axis == 0:
            out = np.expand_dims(out, axis=0)

        # print(f"{out=}")
        self._output_out.dispatch([out])
