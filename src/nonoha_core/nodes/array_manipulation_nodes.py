import logging
import math
import numpy as np
import time

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
    str_to_shape,
)
from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)

logger = logging.getLogger(__name__)


# <https://numpy.org/doc/stable/reference/routines.array-manipulation.html>


class ColumnStackNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Concatenate multiple input arrays into a single array using np.column_stack. Each input is treated as a column.",
            category="Array",
            inputs={
                "in": "Multiple arrays to stack as columns. Count and types set by in_types property."
            },
            outputs={"out": "Column-stacked result."},
        )

    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input types (e.g. 'f32,f32,i32'). Determines input port count and types.",
            "data_type": "str",
            "default_value": "f32,f32",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ColumnStack")

        in_types = [
            name_to_port_value_type(name.strip())
            for name in str(self.properties["in_types"]).split(",")
        ]
        out_type = self._get_out_type(in_types)

        input_in = StaticTypeInputPort(
            "in",
            in_types,
        )
        input_in.subscribe(id(self), self._on_input_in)

        output_out = StaticTypeOutputPort(
            "out",
            [out_type],
        )

        self._in_types = in_types
        self._input_in = input_in
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string")
            in_types = [
                name_to_port_value_type(name.strip())
                for name in in_types_str.split(",")
            ]

        if in_types != self._in_types:
            input_in = StaticTypeInputPort(
                "in",
                in_types,
            )
            input_in.subscribe(id(self), self._on_input_in)

            out_type = self._get_out_type(in_types)
            output_out = StaticTypeOutputPort(
                "out",
                [out_type],
            )

            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_input(
                    self.name, self._input_in.name
                )
                self.parent_graph.disconnect_all_from_node_output(
                    self.name, output_out.name
                )

            self._input_in.unsubscribe(id(self))

            self._in_types = in_types
            self._input_in = input_in
            self._output_out = output_out

            self.inputs[input_in.name] = input_in
            self.outputs[output_out.name] = output_out

        self.properties["in_types"] = ",".join([in_type.name for in_type in in_types])

    def _get_out_type(self, in_types: list[PortValueType]) -> PortValueType:
        data_type = in_types[0].data_type

        # Compute the output shape
        # 1. All inputs are scalars
        if all(not t.shape for t in in_types):
            return PortValueType(data_type, (len(in_types),))

        # 2. Multi-dimensional inputs:
        # sum the first dimension (rows), keep the remaining dimensions
        row_count = 0
        for in_type in in_types:
            if not in_type.shape:  # scalar -> counts as one row
                row_count += 1
            else:  # array -> first dimension is the row count
                row_count += in_type.shape[0]

        # Trailing dimensions of the output come from the first non-scalar input
        remaining_shape = ()
        for in_type in in_types:
            if in_type.shape and len(in_type.shape) >= 2:
                remaining_shape = in_type.shape[1:]
                break

        # Build the output shape
        out_shape = (row_count,) + remaining_shape
        return PortValueType(data_type, out_shape)

    def _on_input_in(self, values: list[PortValue]):
        try:
            out = np.column_stack(values[0 : len(self._in_types)])
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return

        self._output_out.dispatch([out])


class ColumnUnstackNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Split a multi-dimensional array into individual slices along the last axis. Output count equals the size of the first shape dimension.",
            category="Array",
            inputs={
                "in": "Array to split. First shape dimension determines output count."
            },
            outputs={
                "out": "Individual slices. Each output has shape = input shape with first dimension removed."
            },
        )

    PROPERTIES = {
        "in_type": {
            "description": "Input type with shape (e.g. 'f32[3]' for 3 outputs, 'f32[4x2]' for 4 outputs of shape [2]).",
            "data_type": "str",
            "default_value": "f32[2]",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ColumnUnstack")

        in_type = name_to_port_value_type(str(self.properties["in_type"]))
        input_in = StaticTypeInputPort(
            "in",
            [in_type],
        )
        input_in.subscribe(id(self), self._on_input_in)
        out_types = self._get_out_types(in_type)
        output_out = StaticTypeOutputPort(
            "out",
            out_types,
        )

        self._input_in = input_in
        self._in_type = in_type
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

    def _get_out_types(self, in_type: PortValueType) -> list[PortValueType]:
        data_type = in_type.data_type
        shape = in_type.shape
        return [PortValueType(data_type, shape[1:]) for _ in range(shape[0])]

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)

        if in_type != self._in_type:
            input_in = StaticTypeInputPort(
                "in",
                [in_type],
            )
            input_in.subscribe(id(self), self._on_input_in)
            out_types = self._get_out_types(in_type)
            output_out = StaticTypeOutputPort(
                "out",
                out_types,
            )

            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_input(
                    self.name, self._input_in.name
                )
                self.parent_graph.disconnect_all_from_node_output(
                    self.name, output_out.name
                )

            self._input_in.unsubscribe(id(self))

            self._input_in = input_in
            self._in_type = in_type
            self._output_out = output_out
            self.inputs[input_in.name] = input_in
            self.outputs[output_out.name] = output_out

        self.properties["in_type"] = in_type.name

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_in(self, values: list[PortValue]):
        value_array: np.ndarray = values[0]  # type: ignore

        try:
            out = [value_array[:, i] for i in range(value_array.shape[1])]
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return
        # print(f"{out=}")
        self._output_out.dispatch(out)


class StackNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Join multiple arrays along a new axis using np.stack. Axis 0 refers to the first per-element dimension (not the batch dimension).",
            category="Array",
            inputs={
                "in": "Arrays to stack. All must have the same shape. Count set by 'count' property."
            },
            outputs={"out": "Stacked array with a new dimension inserted at 'axis'."},
        )

    PROPERTIES = {
        "in_type": {
            "description": "Input element type (e.g. 'f32', 'f32[3]').",
            "data_type": "str",
            "default_value": "f32",
        },
        "count": {
            "description": "Number of inputs to stack (min: 2).",
            "data_type": "i32",
            "default_value": 2,
        },
        "axis": {
            "description": "Axis for new dimension (1-based, relative to per-element shape).",
            "data_type": "i32",
            "default_value": 1,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Stack")

        count: int = int(self.properties["count"])
        axis: int = int(self.properties["axis"])
        in_type = name_to_port_value_type(str(self.properties["in_type"]))

        input_in = StaticTypeInputPort(
            "in",
            [in_type] * count,
        )
        input_in.subscribe(id(self), self._on_input_in)

        out_shape = self._get_out_type(in_type.shape, count, axis)

        output_out = StaticTypeOutputPort(
            "out",
            [PortValueType(in_type.data_type, out_shape)],
        )

        self._in_type = in_type
        self._count = count
        self._axis = axis
        self._input_in = input_in
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

    def _get_out_type(self, in_shape: tuple[int, ...], input_count, axis: int):
        np_in_shape = (1,) + in_shape

        if axis < 0:
            axis = len(np_in_shape) + 1 + axis

        if axis == 0:
            raise ValueError("axis must be greater than 0")

        # Compute the output shape
        if axis > len(np_in_shape):
            raise ValueError("axis must be less than input shape")

        out_shape = list(np_in_shape)
        out_shape.insert(axis, input_count)

        return tuple(out_shape[1:])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        count = self._count
        if "count" in properties:
            count = int(properties["count"])
            if count < 2:
                raise ValueError("count must be at least 2")

        axis = self._axis
        if "axis" in properties:
            axis = int(properties["axis"])

        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)

        if in_type != self._in_type or count != self._count or axis != self._axis:
            out_shape = self._get_out_type(in_type.shape, count, axis)

            if count != self._count or in_type != self._in_type:
                input_in = StaticTypeInputPort(
                    "in",
                    [in_type] * count,
                )
                input_in.subscribe(id(self), self._on_input_in)

                if self.parent_graph is not None:
                    self.parent_graph.disconnect_all_from_node_input(
                        self.name, self._input_in.name
                    )
                self._input_in.unsubscribe(id(self))
                self._input_in = input_in
                self.inputs[input_in.name] = input_in

            output_out = StaticTypeOutputPort(
                "out",
                [PortValueType(in_type.data_type, out_shape)],
            )
            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_output(
                    self.name, output_out.name
                )

            self._output_out = output_out
            self.outputs[output_out.name] = output_out

        self._in_type = in_type
        self._count = count
        self._axis = axis

        self.properties["in_type"] = in_type.name
        self.properties["count"] = count
        self.properties["axis"] = axis

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_in(self, values: list[PortValue]):
        try:
            out = np.stack(values, axis=self._axis)
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return

        # print(f"{out.shape=}, {out=}")
        self._output_out.dispatch([out])


class UnstackNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Split an array into multiple sub-arrays along a specified axis. Output count equals the input size at that axis. Inverse of StackNode.",
            category="Array",
            inputs={"in": "Array to split along axis."},
            outputs={
                "out": "Individual sub-arrays. Count equals input size at the specified axis."
            },
        )

    PROPERTIES = {
        "in_type": {
            "description": "Input type with shape (e.g. 'f32[2]' splits into 2 outputs).",
            "data_type": "str",
            "default_value": "f32[2]",
        },
        "axis": {
            "description": "Axis along which to split (1-based, relative to per-element shape).",
            "data_type": "i32",
            "default_value": 1,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Unstack")

        axis = int(self.properties["axis"])
        in_type = name_to_port_value_type(str(self.properties["in_type"]))
        input_in = StaticTypeInputPort(
            "in",
            [in_type],
        )
        input_in.subscribe(id(self), self._on_input_in)
        out_types = self._get_out_types(in_type, axis)
        output_out = StaticTypeOutputPort(
            "out",
            out_types,
        )

        self._input_in = input_in
        self._in_type = in_type
        self._axis = axis
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)

        axis = self._axis
        if "axis" in properties:
            axis = int(properties["axis"])

        new_input_in = self._input_in
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort(
                "in",
                [in_type],
            )

        new_output_out = self._output_out
        if axis != self._axis or in_type != self._in_type:
            out_types = self._get_out_types(in_type, axis)
            new_output_out = StaticTypeOutputPort(
                "out",
                out_types,
            )

        if new_input_in is not self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out is not self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        self._in_type = in_type
        self._axis = axis

        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _get_out_types(self, in_type: PortValueType, axis: int):
        data_type = in_type.data_type
        np_shape = (1, *in_type.shape)
        if axis <= 0:
            raise ValueError("axis must be greater than 0")

        if axis > len(np_shape):
            raise ValueError("axis must be less than input shape")

        count = np_shape[axis]
        np_out_shape = np_shape[:axis] + np_shape[axis + 1 :]

        return [PortValueType(data_type, np_out_shape[1:]) for _ in range(count)]

    def _on_input_in(self, values: list[PortValue]):
        value_array: np.ndarray = values[0]
        try:
            # start = time.perf_counter()
            axis = self._axis % value_array.ndim
            moved = np.moveaxis(value_array, axis, 0)
            out = [moved[i] for i in range(moved.shape[0])]

            # Waiting for numpy v2.1
            # out = np.unstack(value_array, axis=self._axis)

            # elapsed = time.perf_counter() - start
            # print(
            # f"{self.name}: Unstacked {len(out)} arrays in {elapsed:.6f} seconds"
            # )
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return

        # print(f"{out=}")
        self._output_out.dispatch(out)


class RollNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Cyclically shift array elements along an axis using np.roll. Elements that roll past the end reappear at the beginning.",
            category="Array",
            inputs={"in": "Input array to roll."},
            outputs={"out": "Rolled array (same shape as input)."},
        )

    PROPERTIES = {
        "in_type": {
            "description": "Input element type (e.g. 'f32', 'f32[4]').",
            "data_type": "str",
            "default_value": "f32",
        },
        "shift": {
            "description": "Number of positions to shift. Positive=forward, negative=backward.",
            "data_type": "i32",
            "default_value": 1,
        },
        "axis": {
            "description": "Axis along which to roll (numpy axis including batch dimension).",
            "data_type": "i32",
            "default_value": 0,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Roll")

        in_type = name_to_port_value_type(str(self.properties["in_type"]))
        input_in = StaticTypeInputPort(
            "in",
            [in_type],
        )
        input_in.subscribe(id(self), self._on_input_in)

        out_type = PortValueType(in_type.data_type, in_type.shape)
        output_out = StaticTypeOutputPort(
            "out",
            [out_type],
        )

        self._shift = int(self.properties["shift"])
        self._axis = int(self.properties["axis"])
        self._input_in = input_in
        self._in_type = in_type
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)

        shift = self._shift
        if "shift" in properties:
            shift = int(properties["shift"])

        axis = self._axis
        if "axis" in properties:
            axis = int(properties["axis"])

        new_input_in = self._input_in
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort(
                "in",
                [in_type],
            )

        new_output_out = self._output_out
        if in_type != self._in_type:
            new_output_out = StaticTypeOutputPort(
                "out",
                [PortValueType(in_type.data_type, in_type.shape)],
            )

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        self._in_type = in_type
        self._shift = shift
        self._axis = axis

        self.properties["in_type"] = in_type.name
        self.properties["shift"] = shift
        self.properties["axis"] = axis
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        value_array: np.ndarray = values[0]
        try:
            out = np.roll(value_array, self._shift, axis=self._axis)
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return

        # print(f"{out=}")
        self._output_out.dispatch([out])


class ReshapeNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description=(
                "Reshape each batch element to a new shape without changing data. "
                "All nonoha arrays have a batch dimension as the first axis. "
                "Port type shape describes each element's shape within the batch: "
                "f32 (scalar per element) has array shape (batch_size,), "
                "f32[128] has array shape (batch_size, 128). "
                "This node reshapes each element while preserving batch_size. "
                "Examples: "
                "in_type=f32, out_type_shape=[1]: (batch_size,) -> (batch_size, 1). "
                "in_type=f32[128], out_type_shape=[64x2]: (batch_size, 128) -> (batch_size, 64, 2). "
                "Set in_type to match the upstream node's output type."
            ),
            category="Array",
            inputs={
                "in": "Input array. Shape must be compatible with in_type. Batch dimension is the first axis."
            },
            outputs={"out": "Reshaped output. Same data, new shape per batch element."},
        )

    PROPERTIES = {
        "in_type": {
            "description": "Input port type (e.g. 'f32', 'f32[128]'). Must match the upstream output type for connection.",
            "data_type": "str",
            "default_value": "f32[128]",
        },
        "out_type_shape": {
            "description": "Target shape per batch element (e.g. '[64x2]', '[1]'). Use ? for variable dimension (e.g. '[?x2]').",
            "data_type": "str",
            "default_value": "[64x2]",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Reshape")

        in_type = name_to_port_value_type(str(self.properties["in_type"]))
        input_in = StaticTypeInputPort(
            "in",
            [in_type],
        )
        input_in.subscribe(id(self), self._on_input_in)

        out_type = PortValueType(
            in_type.data_type, str_to_shape(str(self.properties["out_type_shape"]))
        )
        output_out = StaticTypeOutputPort(
            "out",
            [out_type],
        )

        self._in_type = in_type
        self._out_type = out_type
        self._input_in = input_in
        self._output_out = output_out
        self._reshape_target = self._compute_reshape_target(out_type.shape)

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

    @staticmethod
    def _compute_reshape_target(out_shape: tuple[int, ...]) -> tuple[int, ...]:
        if any(d == -1 for d in out_shape):
            return (1, *out_shape)
        else:
            return (-1, *out_shape)

    @staticmethod
    def _validate_shapes(in_shape: tuple[int, ...], out_shape: tuple[int, ...]) -> None:
        if any(d == -1 for d in in_shape) or any(d == -1 for d in out_shape):
            return
        in_elements = math.prod(in_shape)
        out_elements = math.prod(out_shape)
        if out_elements and in_elements % out_elements != 0:
            raise ValueError(
                f"Input shape {in_shape} ({in_elements} elements) is not "
                f"divisible by output shape {out_shape} ({out_elements} elements)"
            )

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)

        out_type = self._out_type
        if "out_type_shape" in properties:
            out_type_shape_str = properties["out_type_shape"]
            if not isinstance(out_type_shape_str, str):
                raise ValueError("out_type_shape must be a string")
            out_type = PortValueType(
                in_type.data_type, str_to_shape(out_type_shape_str)
            )

        # Shape validation disabled: divisibility check is too restrictive
        # for rechunk cases (e.g. u8[10] -> [2]) where batch absorbs remainder.
        # if in_type != self._in_type or out_type != self._out_type:
        #     self._validate_shapes(in_type.shape, out_type.shape)

        new_input_in = self._input_in
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort(
                "in",
                [in_type],
            )

        new_output_out = self._output_out
        if out_type != self._out_type:
            new_output_out = StaticTypeOutputPort(
                "out",
                [out_type],
            )

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        self._in_type = in_type
        self._out_type = out_type
        self._reshape_target = self._compute_reshape_target(out_type.shape)
        self.properties["in_type"] = in_type.name
        self.properties["out_type_shape"] = out_type.shape_str

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        value_array = values[0]
        try:
            out = value_array.reshape(self._reshape_target)
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return
        self._output_out.dispatch([out])
