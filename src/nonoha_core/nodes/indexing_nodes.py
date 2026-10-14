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


class MaskAssignNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Assign values to array elements selected by a boolean mask",
            category="Indexing",
            inputs={"in": ""},
            outputs={"x": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "MaskAssign")

        x_type = PortValueType(DataType.Float32)
        value_type = PortValueType(DataType.Float32)
        mask_type = PortValueType(DataType.Bool)

        input_in = StaticTypeInputPort(
            "in",
            [x_type, mask_type, value_type],
            ["x", "mask", "value"],
        )
        output_x = StaticTypeOutputPort("x", [x_type])

        input_in.subscribe(id(self), self._on_input_in)

        self._x_type = x_type
        self._input_in = input_in
        self._output_x = output_x
        self._mask_type = mask_type
        self._value_type = value_type

        self.inputs[input_in.name] = input_in
        self.outputs[output_x.name] = output_x

        self.properties["x_type"] = x_type.name
        self.properties["mask_shape"] = mask_type.shape_str
        self.properties["value_type"] = value_type.name

    def _validate_mask_shape(self, mask_shape: tuple, array_shape: tuple):
        if len(array_shape) < len(mask_shape):
            raise ValueError(
                f"Mask shape {mask_shape} is larger than array shape {array_shape}"
            )

        for i, (mask_dim, array_dim) in enumerate(zip(mask_shape, array_shape)):
            if mask_dim != array_dim:
                raise ValueError(
                    f"Mask dimension {mask_dim} does not match array dimension {array_dim} at index {i}"
                )
        return True

    def set_properties(self, properties: dict[str, PropertyDataType]):
        x_type = self._x_type
        if "x_type" in properties:
            x_type_str = properties["x_type"]
            if not isinstance(x_type_str, str):
                raise ValueError("x_type must be a string")
            x_type = name_to_port_value_type(x_type_str)

        mask_type = self._mask_type
        if "mask_shape" in properties:
            mask_shape_str = properties["mask_shape"]
            if not isinstance(mask_shape_str, str):
                raise ValueError("mask_shape must be a string")
            mask_type = name_to_port_value_type(f"bool{mask_shape_str}")

        value_type = self._value_type
        if "value_type" in properties:
            value_type_str = properties["value_type"]
            if not isinstance(value_type_str, str):
                raise ValueError("value_type must be a string")
            value_type = name_to_port_value_type(value_type_str)

        new_output_x = self._output_x
        if x_type != self._x_type:
            new_output_x = StaticTypeOutputPort("x", [x_type])

        new_input_in = self._input_in
        if (
            x_type != self._x_type
            or mask_type != self._mask_type
            or value_type != self._value_type
        ):
            new_input_in = StaticTypeInputPort(
                "in", [x_type, mask_type, value_type], ["x", "mask", "value"]
            )

        if new_input_in != self._input_in:

            self._input_in.unsubscribe(id(self))
            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_input(
                    self.name, self._input_in.name
                )
            new_input_in.subscribe(id(self), self._on_input_in)

            self._input_in = new_input_in
            self.inputs[new_input_in.name] = new_input_in

        if new_output_x != self._output_x:
            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_output(
                    self.name, self._output_x.name
                )

            self._output_x = new_output_x
            self.outputs[new_output_x.name] = new_output_x

        self._x_type = x_type
        self._mask_type = mask_type
        self._value_type = value_type

        self.properties["x_type"] = x_type.name
        self.properties["mask_shape"] = mask_type.shape_str
        self.properties["value_type"] = value_type.name

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_in(self, values: list[PortValue]):
        x_array, mask_array, value_array = values

        x_array = x_array.copy()

        try:
            if len(mask_array) == 1:
                x_array[:, mask_array[0]] = value_array
            else:
                x_array[mask_array] = value_array
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return

        # print(f"{self.name}: {values[0].shape}, {x_array.shape}, {x_array.shape=}, {mask_array.shape=}, {value_array=}")
        self._output_x.dispatch([x_array])


class ExtractNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Extract array elements along an axis using a boolean mask",
            category="Indexing",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Extract")

        x_type = PortValueType(DataType.Float32, (128,))
        mask_type = PortValueType(DataType.Bool, (128,))
        axis: int = 1
        out_type = self.get_out_type(x_type, mask_type, axis)

        input_in = StaticTypeInputPort(
            "in",
            [x_type, mask_type],
            ["x", "mask"],
        )
        input_in.subscribe(id(self), self._on_input_in)

        output_out = StaticTypeOutputPort("out", [out_type])

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self._x_type = x_type
        self._mask_type = mask_type
        self._axis = axis
        self._out_type = out_type
        self._input_in = input_in
        self._output_out = output_out

        self.properties["x_type"] = x_type.name
        self.properties["mask_shape"] = mask_type.shape_str
        self.properties["axis"] = axis

    def get_out_type(self, x_type: PortValueType, mask_type: PortValueType, axis: int):
        in_np_shape = (1, *x_type.shape)
        out_np_shape = list(in_np_shape)
        out_np_shape[axis] = -1

        return PortValueType(x_type.data_type, tuple(out_np_shape[1:]))

    def set_properties(self, properties: dict[str, PropertyDataType]):
        x_type = self._x_type
        if "x_type" in properties:
            x_type_str = properties["x_type"]
            if not isinstance(x_type_str, str):
                raise ValueError("x_type must be a string")
            x_type = name_to_port_value_type(x_type_str)

        mask_type = self._mask_type
        if "mask_shape" in properties:
            mask_shape_str = properties["mask_shape"]
            if not isinstance(mask_shape_str, str):
                raise ValueError("mask_shape must be a string")
            mask_type = name_to_port_value_type(f"bool{mask_shape_str}")

        axis = self._axis
        if "axis" in properties:
            axis = int(properties["axis"])

        out_type = self.get_out_type(x_type, mask_type, axis)

        new_input_in = self._input_in
        if x_type != self._x_type or mask_type != self._mask_type:
            new_input_in = StaticTypeInputPort("in", [x_type, mask_type], ["x", "mask"])

        new_output_out = self._output_out
        if out_type != self._out_type:
            new_output_out = StaticTypeOutputPort("out", [out_type])

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        self._x_type = x_type
        self._mask_type = mask_type
        self._axis = axis
        self._out_type = out_type

        self.properties["x_type"] = x_type.name
        self.properties["mask_shape"] = mask_type.shape_str
        self.properties["axis"] = axis

    def _on_input_in(self, values: list[PortValue]):
        x_array, mask_array = values
        axis = self._axis

        indices: list[slice | np.ndarray] = [slice(None)] * len(x_array.shape)
        indices[axis] = mask_array[0] if len(mask_array) == 1 else mask_array

        try:
            out = x_array[tuple(indices)]
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return

        self._output_out.dispatch([out])
