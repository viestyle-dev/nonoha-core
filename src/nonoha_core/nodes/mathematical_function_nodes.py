import logging
import numpy as np

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
    name_to_data_type,
    data_type_to_name,
)
from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)

logger = logging.getLogger(__name__)


# <https://numpy.org/doc/stable/reference/routines.math.html>


class AbsNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise absolute value",
            category="Math",
            inputs={"value": ""},
            outputs={"value": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Abs")

        in_type = PortValueType(DataType.Float32)

        input_value = StaticTypeInputPort("value", [in_type])
        input_value.subscribe(id(self), self._on_input_value)

        out_type = self._get_out_type(in_type)

        output_value = StaticTypeOutputPort("value", [out_type])

        self._input_value = input_value
        self._output_value = output_value
        self._in_type = in_type
        self._out_type = out_type

        self.inputs[input_value.name] = input_value
        self.outputs[output_value.name] = output_value

        self.properties["in_type"] = in_type.name

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract and validate properties
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("In type must be a string")
            in_type = name_to_port_value_type(in_type_str)

        # 2. Create new ports if necessary
        new_input_value = self._input_value
        new_output_value = self._output_value
        out_type = self._out_type
        if in_type != self._in_type:
            out_type = self._get_out_type(in_type)
            new_input_value = StaticTypeInputPort("value", [in_type])
            new_output_value = StaticTypeOutputPort("value", [out_type])

        # 3. Replace ports atomically if changed
        if new_input_value != self._input_value:
            replace_node_input_port(
                self, self._input_value, new_input_value, self._on_input_value
            )
            self._input_value = new_input_value

        if new_output_value != self._output_value:
            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        # 4. Update instance variables and properties
        self._in_type = in_type
        self._out_type = out_type
        self.properties["in_type"] = in_type.name

        # 5. Notify graph of updates
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _get_out_type(self, in_type: PortValueType) -> PortValueType:
        match in_type.data_type:
            case (
                DataType.Float32
                | DataType.Float64
                | DataType.Int8
                | DataType.Int16
                | DataType.Int32
                | DataType.Int64
            ):
                return PortValueType(in_type.data_type, in_type.shape)
            case DataType.Complex64:
                return PortValueType(DataType.Float32, in_type.shape)
            case DataType.Complex128:
                return PortValueType(DataType.Float64, in_type.shape)
            case _:
                raise ValueError(f"Unsupported data type: {in_type.data_type}")

    def _on_input_value(self, values: list[PortValue]):
        value_array: np.ndarray = values[0]  # type: ignore

        out = np.abs(value_array)

        self._output_value.dispatch([out])


class SumNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Sum of array elements along an axis",
            category="Math",
            inputs={"value": ""},
            outputs={"value": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Sum")

        in_type = PortValueType(DataType.Float32, shape=(2,))
        axis: int | None = 1
        out_type = self._get_out_type(in_type, axis)

        input_value = StaticTypeInputPort("value", [in_type])
        input_value.subscribe(id(self), self._on_input_value)

        output_value = StaticTypeOutputPort("value", [out_type])

        self._input_value = input_value
        self._output_value = output_value
        self._in_type = in_type
        self._axis = axis

        self.inputs[input_value.name] = input_value
        self.outputs[output_value.name] = output_value

        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis

    def _get_out_type(self, in_type: PortValueType, axis: int | None) -> PortValueType:
        if axis is None:
            return PortValueType(in_type.data_type)
        if axis == 0:
            return PortValueType(in_type.data_type, in_type.shape)

        np_in_shape = (1, *in_type.shape)
        out_shape = np_in_shape[:axis] + np_in_shape[axis + 1 :]
        out_shape = out_shape[1:]
        return PortValueType(in_type.data_type, out_shape)

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract and validate properties
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("In type must be a string")
            in_type = name_to_port_value_type(in_type_str)

        axis = self._axis
        if "axis" in properties:
            axis = properties["axis"]
            if isinstance(axis, str) and axis == "":
                axis = None
            else:
                axis = int(axis)

        # 2. Create new ports if necessary
        new_input_value = self._input_value
        if in_type != self._in_type:
            new_input_value = StaticTypeInputPort("value", [in_type])

        new_output_value = self._output_value
        if axis != self._axis or in_type != self._in_type:
            out_type = self._get_out_type(in_type, axis)
            new_output_value = StaticTypeOutputPort("value", [out_type])

        # 3. Replace ports atomically if changed
        if new_input_value != self._input_value:
            replace_node_input_port(
                self, self._input_value, new_input_value, self._on_input_value
            )
            self._input_value = new_input_value

        if new_output_value != self._output_value:
            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        # 4. Update instance variables and properties
        self._in_type = in_type
        self._axis = axis
        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis if axis is not None else ""

        # 5. Notify graph of updates
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_value(self, values: list[PortValue]):
        value_array = values[0]
        out = np.sum(value_array, axis=self._axis)

        if self._axis is None or self._axis == 0:
            # print(f"{out.ndim=}")
            out = np.expand_dims(out, axis=0)

        # print(f"{out=}, {out.shape=}")
        self._output_value.dispatch([out])


class MinNode(BaseNode):
    # <https://numpy.org/doc/stable/reference/generated/numpy.min.html>
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Minimum value of array elements along an axis",
            category="Math",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Min")

        in_type = PortValueType(DataType.Float32, shape=(2,))
        axis: int | None = 1
        out_type = self._get_out_type(in_type, axis)

        input_in = StaticTypeInputPort("in", [in_type])
        input_in.subscribe(id(self), self._on_input_in)

        output_out = StaticTypeOutputPort("out", [out_type])

        self._input_in = input_in
        self._output_out = output_out
        self._in_type = in_type
        self._out_type = out_type
        self._axis = axis

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis

    def _get_out_type(self, in_type: PortValueType, axis: int | None) -> PortValueType:
        if axis is None:
            return PortValueType(in_type.data_type)
        if axis == 0:
            return PortValueType(in_type.data_type, in_type.shape)

        np_in_shape = (1, *in_type.shape)
        out_shape = np_in_shape[:axis] + np_in_shape[axis + 1 :]
        out_shape = out_shape[1:]
        return PortValueType(in_type.data_type, out_shape)

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract and validate properties
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("In type must be a string")
            in_type = name_to_port_value_type(in_type_str)

        axis = self._axis
        if "axis" in properties:
            axis = properties["axis"]
            if isinstance(axis, str) and axis == "":
                axis = None
            else:
                axis = int(axis)

        # 2. Create new ports if necessary
        new_input_in = self._input_in
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])

        new_output_out = self._output_out
        out_type = self._out_type
        if axis != self._axis or in_type != self._in_type:
            out_type = self._get_out_type(in_type, axis)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        # 4. Update instance variables and properties
        self._in_type = in_type
        self._out_type = out_type
        self._axis = axis
        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis if axis is not None else ""

        # 5. Notify graph of updates
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        value_array = values[0]
        out = np.min(value_array, axis=self._axis)

        if self._axis is None or self._axis == 0:
            out = np.expand_dims(out, axis=0)

        self._output_out.dispatch([out])


class MaxNode(BaseNode):
    # <https://numpy.org/doc/stable/reference/generated/numpy.max.html>
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Maximum value of array elements along an axis",
            category="Math",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Max")

        in_type = PortValueType(DataType.Float32, shape=(2,))
        axis: int | None = 1
        out_type = self._get_out_type(in_type, axis)

        input_in = StaticTypeInputPort("in", [in_type])
        input_in.subscribe(id(self), self._on_input_in)

        output_out = StaticTypeOutputPort("out", [out_type])

        self._input_in = input_in
        self._output_out = output_out
        self._in_type = in_type
        self._out_type = out_type
        self._axis = axis

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis

    def _get_out_type(self, in_type: PortValueType, axis: int | None) -> PortValueType:
        if axis is None:
            return PortValueType(in_type.data_type)
        if axis == 0:
            return PortValueType(in_type.data_type, in_type.shape)

        np_in_shape = (1, *in_type.shape)
        out_shape = np_in_shape[:axis] + np_in_shape[axis + 1 :]
        out_shape = out_shape[1:]
        return PortValueType(in_type.data_type, out_shape)

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract and validate properties
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("In type must be a string")
            in_type = name_to_port_value_type(in_type_str)

        axis = self._axis
        if "axis" in properties:
            axis = properties["axis"]
            if isinstance(axis, str) and axis == "":
                axis = None
            else:
                axis = int(axis)

        # 2. Create new ports if necessary
        new_input_in = self._input_in
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])

        new_output_out = self._output_out
        out_type = self._out_type
        if axis != self._axis or in_type != self._in_type:
            out_type = self._get_out_type(in_type, axis)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        # 4. Update instance variables and properties
        self._in_type = in_type
        self._out_type = out_type
        self._axis = axis
        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis if axis is not None else ""

        # 5. Notify graph of updates
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        value_array = values[0]
        out = np.max(value_array, axis=self._axis)

        if self._axis is None or self._axis == 0:
            out = np.expand_dims(out, axis=0)

        self._output_out.dispatch([out])


class InterpolateNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="1-D linear interpolation for given x against reference points (xp, fp)",
            category="Math",
            inputs={"in": ""},
            outputs={"y": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Interpolate")

        # Support f32, f64, c64, c128
        data_type = DataType.Float32
        n_points = 2

        input_in = StaticTypeInputPort(
            "in",
            [
                PortValueType(data_type),
                PortValueType(
                    data_type,
                    shape=(n_points,),
                ),
                PortValueType(
                    data_type,
                    shape=(n_points,),
                ),
            ],
            ["x", "xp", "fp"],
        )
        input_in.subscribe(id(self), self._on_input_in)

        output_y = StaticTypeOutputPort("y", [PortValueType(data_type)])

        self._input_in = input_in
        self._output_y = output_y
        self._data_type = data_type
        self._n_points = n_points

        self.inputs[input_in.name] = input_in
        self.outputs[output_y.name] = output_y

        self.properties["data_type"] = data_type_to_name(data_type)
        self.properties["n_points"] = n_points

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract and validate properties
        data_type = self._data_type
        if "data_type" in properties:
            data_type_str = properties["data_type"]
            if not isinstance(data_type_str, str):
                raise ValueError("Data type must be a string")
            data_type = name_to_data_type(data_type_str)
            if data_type not in [
                DataType.Float32,
                DataType.Float64,
                DataType.Complex64,
                DataType.Complex128,
            ]:
                raise ValueError(
                    f"Unsupported data type: {data_type.name}. "
                    "Only f32, f64, c64, c128 are supported."
                )

        n_points = self._n_points
        if "n_points" in properties:
            n_points = int(properties["n_points"])
            if n_points < 2:
                raise ValueError("n_points must be at least 2")

        # 2. Create new ports if necessary
        new_input_in = self._input_in
        if data_type != self._data_type or n_points != self._n_points:
            new_input_in = StaticTypeInputPort(
                "in",
                [
                    PortValueType(data_type),
                    PortValueType(
                        data_type,
                        shape=(n_points,),
                    ),
                    PortValueType(
                        data_type,
                        shape=(n_points,),
                    ),
                ],
                ["x", "xp", "fp"],
            )

        new_output_y = self._output_y
        if data_type != self._data_type:
            new_output_y = StaticTypeOutputPort("y", [PortValueType(data_type)])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_y != self._output_y:
            replace_node_output_port(self, self._output_y, new_output_y)
            self._output_y = new_output_y

        # 4. Update instance variables and properties
        self._data_type = data_type
        self._n_points = n_points
        self.properties["data_type"] = data_type_to_name(data_type)
        self.properties["n_points"] = n_points

        # 5. Notify graph of updates
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        x_array = values[0]
        xp_array = values[1]
        fp_array = values[2]

        # xp_array and fp_array have shape (N, n_points)
        # Use the last element along the batch dimension (axis 0)

        y_array = np.interp(x_array, xp_array[-1], fp_array[-1])

        self._output_y.dispatch([y_array])


class SqrtNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise square root",
            category="Math",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Sqrt")

        in_type = PortValueType(DataType.Float32)

        input_in = StaticTypeInputPort("in", [in_type])
        input_in.subscribe(id(self), self._on_input_in)

        output_out = StaticTypeOutputPort("out", [in_type])

        self._input_in = input_in
        self._output_out = output_out
        self._in_type = in_type

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_type"] = in_type.name

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract and validate properties
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("In type must be a string")

            in_type = name_to_port_value_type(in_type_str)

        # 2. Create new ports if necessary
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_out = StaticTypeOutputPort("out", [in_type])

        # 3. Replace ports if changed
        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        # 4. Update instance variables and properties
        self._in_type = in_type
        self.properties["in_type"] = in_type.name

        # 5. Notify graph of updates
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        value_array: np.ndarray = values[0]  # type: ignore
        out = np.sqrt(value_array)
        self._output_out.dispatch([out])
