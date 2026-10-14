import logging
import math
from typing import Literal

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
)
from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)

logger = logging.getLogger(__name__)

# The sets of nodes for bit-wise operations.
# <https://numpy.org/doc/stable/reference/routines.bitwise.html>

_PACKBITS_DTYPES = {DataType.Uint8, DataType.Bool}
BitOrder = Literal["big", "little"]


# https://numpy.org/doc/stable/reference/generated/numpy.packbits.html
class PackbitsNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Pack binary values into bits along an axis",
            category="Bitwise",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    _bitorder: BitOrder
    _axis: int

    def __init__(self, name: str):
        super().__init__(name, "Packbits")

        in_type = PortValueType(DataType.Uint8, (8,))
        axis = 1
        bitorder: BitOrder = "big"

        out_type = self._get_out_type(in_type, axis)

        input_in = StaticTypeInputPort("in", [in_type])
        input_in.subscribe(id(self), self._on_input)

        output_out = StaticTypeOutputPort("out", [out_type])

        self._input_in = input_in
        self._output_out = output_out
        self._in_type = in_type
        self._out_type = out_type
        self._axis = axis
        self._bitorder = bitorder

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis
        self.properties["bitorder"] = bitorder

    @staticmethod
    def _get_out_type(in_type: PortValueType, axis: int) -> PortValueType:
        if not in_type.shape:
            raise ValueError("Packbits requires at least 1 dimension")
        if in_type.data_type not in _PACKBITS_DTYPES:
            raise ValueError(
                f"Packbits only accepts u8 or bool, got {in_type.data_type}"
            )

        np_in_shape = (1, *in_type.shape)
        packed_dim = np_in_shape[axis]
        if packed_dim == -1:
            new_dim = -1
        else:
            new_dim = math.ceil(packed_dim / 8)

        out_np_shape = list(np_in_shape)
        out_np_shape[axis] = new_dim
        out_shape = tuple(out_np_shape[1:])
        return PortValueType(DataType.Uint8, out_shape)

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

        bitorder: BitOrder = self._bitorder
        if "bitorder" in properties:
            v = str(properties["bitorder"])
            if v not in ("big", "little"):
                raise ValueError(f"bitorder must be 'big' or 'little', got '{v}'")
            bitorder = v  # type: ignore[assignment]

        new_input_in = self._input_in
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])

        new_output_out = self._output_out
        if axis != self._axis or in_type != self._in_type:
            out_type = self._get_out_type(in_type, axis)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        if new_input_in != self._input_in:
            replace_node_input_port(self, self._input_in, new_input_in, self._on_input)
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        self._in_type = in_type
        self._axis = axis
        self._bitorder = bitorder
        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis
        self.properties["bitorder"] = bitorder

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input(self, values: list[PortValue]):
        value_array: np.ndarray = values[0]  # type: ignore
        try:
            out = np.packbits(value_array, axis=self._axis, bitorder=self._bitorder)
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return
        self._output_out.dispatch([out])
