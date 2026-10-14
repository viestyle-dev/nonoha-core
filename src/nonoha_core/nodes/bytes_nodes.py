import logging
import math
import sys

import numpy as np

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


class BytesValueNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Output a constant zero-filled byte array of configurable length",
            category="Bytes",
            inputs={},
            outputs={"bytes": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "BytesValue")

        length = 512

        output_bytes = StaticTypeOutputPort(
            "bytes", [PortValueType(DataType.Uint8, (length,))]
        )

        self._length = length
        self._output_bytes = output_bytes

        self.outputs[output_bytes.name] = output_bytes

        self.properties["length"] = length

        output_bytes.dispatch([np.zeros((1, length), dtype=np.uint8)])
        # output_bytes.dispatch([np.ones((1, length), dtype=np.uint8)])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        length = self._length

        if "length" in properties:
            length = int(properties["length"])
            if length <= 0:
                raise ValueError("Length must be a positive integer.")

        new_output_bytes = self._output_bytes

        if length != self._length:
            new_output_bytes = StaticTypeOutputPort(
                "bytes", [PortValueType(DataType.Uint8, (length,))]
            )

        need_dispatch = False
        if new_output_bytes != self._output_bytes:
            replace_node_output_port(self, self._output_bytes, new_output_bytes)

            self._output_bytes = new_output_bytes
            need_dispatch = True

        self._length = length
        self.properties["length"] = length

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

        if need_dispatch:
            new_output_bytes.dispatch([np.zeros((1, length), dtype=np.uint8)])

            if self.parent_graph is not None:
                self.parent_graph.flush_outputs()


class BytesInplaceInsertNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Insert bytes into a byte array at a specified offset",
            category="Bytes",
            inputs={"in": ""},
            outputs={"bytes": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "BytesInplaceInsert")

        length = 512
        offset = 0
        insert_length = 4

        input_in = StaticTypeInputPort(
            "in",
            [
                PortValueType(DataType.Uint8, (length,)),
                PortValueType(DataType.Uint8, (insert_length,)),
            ],
            ["bytes", "insert_bytes"],
        )

        output_bytes = StaticTypeOutputPort(
            "bytes", [PortValueType(DataType.Uint8, (length,))]
        )

        input_in.subscribe(id(self), self._on_input_in)

        self._length = length
        self._offset = offset
        self._insert_length = insert_length
        self._input_in = input_in
        self._output_bytes = output_bytes

        self.inputs[input_in.name] = input_in
        self.outputs[output_bytes.name] = output_bytes

        self.properties["length"] = length
        self.properties["offset"] = offset
        self.properties["insert_length"] = insert_length

    def set_properties(self, properties: dict[str, PropertyDataType]):
        length = self._length
        offset = self._offset
        insert_length = self._insert_length

        if "length" in properties:
            length = int(properties["length"])
            if length <= 0:
                raise ValueError("Length must be a positive integer.")

        if "offset" in properties:
            offset = int(properties["offset"])
            if offset < 0:
                raise ValueError("Offset must be a non-negative integer.")

        if "insert_length" in properties:
            insert_length = int(properties["insert_length"])
            if insert_length <= 0:
                raise ValueError("Insert length must be a positive integer.")

        if offset + insert_length > length:
            raise ValueError("Offset + Insert length must be <= Length.")

        new_input_in = self._input_in

        if length != self._length or insert_length != self._insert_length:
            new_input_in = StaticTypeInputPort(
                "in",
                [
                    PortValueType(DataType.Uint8, (length,)),
                    PortValueType(DataType.Uint8, (insert_length,)),
                ],
                ["bytes", "insert_bytes"],
            )

        new_output_bytes = self._output_bytes
        if length != self._length:
            new_output_bytes = StaticTypeOutputPort(
                "bytes", [PortValueType(DataType.Uint8, (length,))]
            )

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_bytes != self._output_bytes:
            replace_node_output_port(self, self._output_bytes, new_output_bytes)
            self._output_bytes = new_output_bytes

        self._length = length
        self._offset = offset
        self._insert_length = insert_length

        self.properties["length"] = length
        self.properties["offset"] = offset
        self.properties["insert_length"] = insert_length

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        bytes_array = values[0]
        insert_bytes_array = values[1]

        bytes_array[:, self._offset : self._offset + self._insert_length] = (
            insert_bytes_array
        )
        self._output_bytes.dispatch([bytes_array])


class ToBytesNode(BaseNode):
    """Convert numeric array to bytes with endianness control."""

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Convert numeric array to bytes with endianness control",
            category="Bytes",
            inputs={"in": ""},
            outputs={"bytes": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "ToBytes")

        in_type = PortValueType(DataType.Float32, (4,))
        is_little_endian = False

        input_in = StaticTypeInputPort("in", [in_type])
        output_bytes = StaticTypeOutputPort(
            "bytes",
            [
                PortValueType(
                    DataType.Uint8, (self._get_expected_output_length(in_type),)
                )
            ],
        )

        input_in.subscribe(id(self), self._on_input_in)

        self._in_type = in_type
        self._is_little_endian = is_little_endian
        self._input_in = input_in
        self._output_bytes = output_bytes

        self.inputs[input_in.name] = input_in
        self.outputs[output_bytes.name] = output_bytes

        self.properties["in_type"] = in_type.name
        self.properties["is_little_endian"] = is_little_endian

    def _get_expected_output_length(self, value_type: PortValueType) -> int:
        match value_type.data_type:
            case DataType.Bool | DataType.Int8 | DataType.Uint8:
                type_size = 1
            case DataType.Int16 | DataType.Uint16:
                type_size = 2
            case DataType.Int32 | DataType.Uint32 | DataType.Float32:
                type_size = 4
            case DataType.Int64 | DataType.Uint64 | DataType.Float64:
                type_size = 8
            case DataType.Complex64:
                type_size = 8
            case DataType.Complex128:
                type_size = 16
            case DataType.String | DataType.Any | _:
                raise ValueError(f"Unsupported data type: {value_type.data_type}")

        return type_size * math.prod(value_type.shape)

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract and validate properties
        in_type = self._in_type
        if "in_type" in properties:
            in_type_name = str(properties["in_type"])
            in_type = name_to_port_value_type(in_type_name)

        is_little_endian = self._is_little_endian
        if "is_little_endian" in properties:
            is_little_endian = bool(properties["is_little_endian"])

        # 2. Create new ports if necessary
        new_input_in = self._input_in
        new_output_bytes = self._output_bytes

        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_bytes = StaticTypeOutputPort(
                "bytes",
                [
                    PortValueType(
                        DataType.Uint8, (self._get_expected_output_length(in_type),)
                    )
                ],
            )

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_bytes != self._output_bytes:
            replace_node_output_port(self, self._output_bytes, new_output_bytes)
            self._output_bytes = new_output_bytes

        # 4. Update instance variables and properties
        self._in_type = in_type
        self._is_little_endian = is_little_endian

        self.properties["in_type"] = in_type.name
        self.properties["is_little_endian"] = is_little_endian

        # 5. Notify graph
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        in_array: np.ndarray = values[0]  # shape: [Batch, ...]
        batch_size = in_array.shape[0]

        # Determine input byte order from dtype
        input_order = in_array.dtype.byteorder
        if input_order == "=" or input_order == "|":
            # '=' means native, '|' means not applicable (1-byte types)
            input_order = "<" if sys.byteorder == "little" else ">"

        # Determine target byte order
        target_order = "<" if self._is_little_endian else ">"

        # Swap bytes if input and target byte order differ
        if input_order != target_order and in_array.dtype.itemsize > 1:
            in_array = in_array.byteswap()

        # Convert to bytes and reshape to [Batch, bytes_length]
        bytes_array = in_array.view(np.uint8).reshape(batch_size, -1)
        self._output_bytes.dispatch([bytes_array])


class ToBytesStringNode(BaseNode):
    """Convert UTF-8 string to bytes."""

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Convert UTF-8 string to byte array",
            category="Bytes",
            inputs={"in": ""},
            outputs={"bytes": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "ToBytesString")

        input_in = StaticTypeInputPort("in", [PortValueType(DataType.String)])
        output_bytes = StaticTypeOutputPort(
            "bytes", [PortValueType(DataType.Uint8, (-1,))]
        )

        input_in.subscribe(id(self), self._on_input_in)

        self._input_in = input_in
        self._output_bytes = output_bytes

        self.inputs[input_in.name] = input_in
        self.outputs[output_bytes.name] = output_bytes

    def _on_input_in(self, values: list[PortValue]):
        string_array: np.ndarray = values[0]  # shape: [Batch], dtype: StringDType

        # Process each string in the batch
        for s in string_array:
            # StringDType elements are already str, encode to UTF-8
            utf8_bytes = str(s).encode("utf-8")
            self._output_bytes.dispatch(
                [np.frombuffer(utf8_bytes, dtype=np.uint8).reshape(1, -1)]
            )
