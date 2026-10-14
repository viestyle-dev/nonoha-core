import numpy as np
import logging
import traceback
from numpy.lib.stride_tricks import sliding_window_view

from nonoha_core.port import (
    StaticTypeInputPort,
    StaticTypeOutputPort,
    PortValue,
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
    data_type_to_numpy_dtype,
    name_to_port_value_type,
)

logger = logging.getLogger(__name__)


class ValuesBufferNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Accumulate values into a fixed-size buffer with flush and shift operations",
            category="Buffer",
            inputs={
                "values": "Values to accumulate into the buffer",
                "inplace_update": "Update buffer values at specific positions (excess is discarded)",
                "flush": "Trigger to output buffered values",
                "shift": "Number of values to shift out from buffer front",
                "reset": "Reset buffer position to beginning",
            },
            outputs={
                "values": "Buffered values on flush or shift",
            },
        )

    PROPERTIES = {
        "size": {
            "description": "Buffer capacity (number of samples)",
            "data_type": "i32",
            "default_value": 1024,
        },
        "value_type_list": {
            "description": "Comma-separated port value types (e.g. 'f32,f32')",
            "data_type": "str",
            "default_value": "f32,f32",
        },
        "reset_on_flush": {
            "description": "Reset buffer position after flush",
            "data_type": "bool",
            "default_value": True,
        },
        "flush_on_full": {
            "description": "Auto-flush when buffer is full",
            "data_type": "bool",
            "default_value": False,
        },
        "dispatch_empty": {
            "description": "Dispatch empty arrays when no data available",
            "data_type": "bool",
            "default_value": False,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ValuesBuffer")

        value_type_list = [
            PortValueType(DataType.Float32),
            PortValueType(DataType.Float32),
        ]
        input_values = StaticTypeInputPort(
            "values",
            value_type_list,
        )
        input_values.subscribe(id(self), self._on_values)

        input_inplace_update = StaticTypeInputPort(
            "inplace_update",
            [PortValueType(DataType.Int32), *value_type_list],
            ["position", *(f"value_{i}" for i in range(len(value_type_list)))],
        )
        input_inplace_update.subscribe(id(self), self._on_input_inplace_update)

        input_flush = StaticTypeInputPort(
            "flush",
            [PortValueType(DataType.Any)],
        )
        input_flush.subscribe(id(self), self._on_flush)

        input_shift = StaticTypeInputPort(
            "shift",
            [PortValueType(DataType.Int32)],
        )
        input_shift.subscribe(id(self), self._on_input_shift)

        input_reset = StaticTypeInputPort(
            "reset",
            [PortValueType(DataType.Any)],
        )
        input_reset.subscribe(id(self), self._on_reset)

        output_values = StaticTypeOutputPort(
            "values",
            value_type_list,
        )

        self._buffer_size = int(self.properties["size"])
        self._value_type_list = value_type_list
        self._buffer: list[np.ndarray] = self._make_buffer(
            self._buffer_size, value_type_list
        )
        self._buffer_index = 0
        self._reset_on_flush = bool(self.properties["reset_on_flush"])
        self._flush_on_full = bool(self.properties["flush_on_full"])
        self._dispatch_empty = bool(self.properties["dispatch_empty"])

        self._input_values = input_values
        self._input_inplace_update = input_inplace_update
        self._output_values = output_values

        self.inputs[input_values.name] = input_values
        self.inputs[input_flush.name] = input_flush
        self.inputs[input_shift.name] = input_shift
        self.inputs[input_reset.name] = input_reset
        self.inputs[input_inplace_update.name] = input_inplace_update
        self.outputs[output_values.name] = output_values

    @staticmethod
    def _make_buffer(
        buffer_size: int, value_type_list: list[PortValueType]
    ) -> list[np.ndarray]:
        return [
            np.zeros(
                (buffer_size,) + vt.shape, dtype=data_type_to_numpy_dtype(vt.data_type)
            )
            for vt in value_type_list
        ]

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract properties
        size = self._buffer_size
        if "size" in properties:
            size = int(properties["size"])
            if size < 1:
                raise ValueError("size must be greater than 0")

        value_type_list = self._value_type_list
        if "value_type_list" in properties:
            value_type_list_str = properties["value_type_list"]
            if not isinstance(value_type_list_str, str):
                raise ValueError("value_type_list must be a string")
            value_type_list = [
                name_to_port_value_type(v) for v in value_type_list_str.split(",")
            ]
            for vt in value_type_list:
                if vt.data_type == DataType.Any:
                    raise ValueError(
                        f"DataType.Any is not supported for buffer: {vt.name}"
                    )
                if any(d < 0 for d in vt.shape):
                    raise ValueError(
                        f"Variable dimensions not supported for buffer: {vt.name}"
                    )

        reset_on_flush = self._reset_on_flush
        if "reset_on_flush" in properties:
            reset_on_flush = bool(properties["reset_on_flush"])

        flush_on_full = self._flush_on_full
        if "flush_on_full" in properties:
            flush_on_full = bool(properties["flush_on_full"])

        # 2. Prepare new ports
        new_input_values = self._input_values
        new_output_values = self._output_values
        new_input_inplace_update = self._input_inplace_update
        if value_type_list != self._value_type_list:
            new_input_values = StaticTypeInputPort("values", value_type_list)
            new_output_values = StaticTypeOutputPort("values", value_type_list)
            new_input_inplace_update = StaticTypeInputPort(
                "inplace_update",
                [PortValueType(DataType.Int32), *value_type_list],
                ["position", *(f"value_{i}" for i in range(len(value_type_list)))],
            )

        # 3. Update internal state
        if new_input_values != self._input_values:
            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_values
            )
            self._input_values = new_input_values

        if new_input_inplace_update != self._input_inplace_update:
            replace_node_input_port(
                self,
                self._input_inplace_update,
                new_input_inplace_update,
                self._on_input_inplace_update,
            )
            self._input_inplace_update = new_input_inplace_update

        if new_output_values != self._output_values:
            replace_node_output_port(self, self._output_values, new_output_values)
            self._output_values = new_output_values

        need_realloc = False
        if value_type_list != self._value_type_list:
            self._value_type_list = value_type_list
            need_realloc = True

        if size != self._buffer_size:
            self._buffer_size = size
            need_realloc = True

        if need_realloc:
            self._buffer = self._make_buffer(self._buffer_size, self._value_type_list)
            self._buffer_index = 0

        dispatch_empty = self._dispatch_empty
        if "dispatch_empty" in properties:
            dispatch_empty = bool(properties["dispatch_empty"])

        self._reset_on_flush = reset_on_flush
        self._flush_on_full = flush_on_full
        self._dispatch_empty = dispatch_empty

        self.properties["size"] = self._buffer_size
        self.properties["value_type_list"] = ",".join(v.name for v in value_type_list)
        self.properties["reset_on_flush"] = self._reset_on_flush
        self.properties["flush_on_full"] = self._flush_on_full
        self.properties["dispatch_empty"] = self._dispatch_empty

        # 4. Notify graph
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_reset(self, values: list[PortValue]):
        self._buffer_index = 0

    def _on_flush(self, values: list[PortValue]):
        count = self._buffer_index

        if count > 0:
            self._output_values.dispatch([b[:count] for b in self._buffer])
            if self._reset_on_flush:
                self._buffer_index = 0
        elif self._dispatch_empty:
            self._output_values.dispatch([b[:0] for b in self._buffer])

    def _on_input_shift(self, values: list[PortValue]):
        shift_counts = values[0]
        buffer_index = self._buffer_index
        offset = 0

        for count in shift_counts:
            count = int(count)
            available = buffer_index - offset

            if count <= 0 or available <= 0:
                if self._dispatch_empty:
                    self._output_values.dispatch([b[:0] for b in self._buffer])
            else:
                actual = min(count, available)
                self._output_values.dispatch(
                    [b[offset : offset + actual] for b in self._buffer]
                )
                offset += actual

        if offset > 0:
            remaining = buffer_index - offset
            if remaining > 0:
                for b in self._buffer:
                    b[:remaining] = b[offset:buffer_index]
            self._buffer_index = remaining

    def _on_input_inplace_update(self, values: list[PortValue]):
        position_array = values[0].astype(np.uint32, copy=False)
        value_arrays = values[1:]

        valid = position_array < self._buffer_size
        valid_positions = position_array[valid]

        for buffer, vals in zip(self._buffer, value_arrays):
            if len(vals) == 0:
                continue
            # print(f"{valid_positions[0]=}, {position_array[0]=}, {vals[0]=}")
            buffer[valid_positions] = vals[valid]

    def _on_values(self, values: list[PortValue]):
        values_length = len(values[0])
        if not np.all([len(v) == values_length for v in values]):
            logger.warning("Input values must have the same length")
            return

        buffer_index = self._buffer_index
        buffer_size = self._buffer_size
        leftover_count = buffer_size - buffer_index
        append_count = min(leftover_count, values_length)

        try:
            for i, _ in enumerate(self._value_type_list):
                self._buffer[i][buffer_index : buffer_index + append_count] = values[i][
                    :append_count
                ]

        except Exception:
            traceback.print_exc()
            return

        buffer_index += values_length

        if buffer_index >= buffer_size:
            if self._flush_on_full and append_count > 0:
                self._output_values.dispatch(self._buffer)

            start = append_count
            # print(f"{append_count=}")

            while values_length - start >= buffer_size:
                if self._flush_on_full:
                    self._output_values.dispatch(
                        [
                            value_array[start : start + buffer_size]
                            for value_array in values
                        ]
                    )

                start += buffer_size

            # print(f"{start=},{values_length=}")

            if self._reset_on_flush and self._flush_on_full:
                for i in range(len(self._buffer)):
                    value_array = values[i]
                    self._buffer[i][: values_length - start] = value_array[start:]
                buffer_index = values_length - start
            else:

                overflow_count = buffer_index - buffer_size

                if overflow_count >= buffer_size:
                    for i in range(len(self._buffer)):
                        value_array = values[i]
                        self._buffer[i][0:buffer_size] = value_array[-buffer_size:]
                else:
                    keep_count = buffer_size - overflow_count
                    for i in range(len(self._buffer)):
                        value_array = values[i]
                        self._buffer[i][:keep_count] = self._buffer[i][
                            overflow_count:buffer_size
                        ]
                        self._buffer[i][keep_count:] = value_array[append_count:]

                buffer_index = buffer_size

                if self._flush_on_full and values_length - start > 0:
                    self._output_values.dispatch(self._buffer)

        self._buffer_index = buffer_index


class SlidingWindowNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Apply a sliding window over streaming input data",
            category="Buffer",
            inputs={
                "values": "Streaming values to apply sliding window",
                "reset": "Clear internal buffer",
            },
            outputs={
                "values": "Windowed output with shape [..., win_size]",
            },
        )

    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input value types",
            "data_type": "str",
            "default_value": "f32",
        },
        "win_size": {
            "description": "Sliding window size",
            "data_type": "i32",
            "default_value": 100,
        },
        "axis": {
            "description": "Axis along which to slide the window",
            "data_type": "i32",
            "default_value": 0,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "SlidingWindow")

        in_types = [PortValueType(DataType.Float32)]
        win_size = int(self.properties["win_size"])
        axis = int(self.properties["axis"])
        buffers: list[np.ndarray | None] = [None] * len(in_types)

        input_values = StaticTypeInputPort(
            "values",
            in_types,
        )
        input_values.subscribe(id(self), self._on_input_values)

        input_reset = StaticTypeInputPort(
            "reset",
            [PortValueType(DataType.Any)],
        )
        input_reset.subscribe(id(self), self._on_input_reset)

        out_types = self._get_out_types(in_types, win_size, axis)
        output_values = StaticTypeOutputPort(
            "values",
            out_types,
        )

        self._input_values = input_values
        self._output_values = output_values
        self._win_size = win_size
        self._buffers = buffers
        self._in_types = in_types
        self._axis = axis

        self.inputs[input_values.name] = input_values
        self.inputs[input_reset.name] = input_reset
        self.outputs[output_values.name] = output_values

    def _get_out_types(
        self, in_types: list[PortValueType], win_size: int, axis: int
    ) -> list[PortValueType]:
        out_types = []
        for in_type in in_types:
            np_out_shape = [1, *in_type.shape, win_size]
            if axis > 0:
                sliding_count = np_out_shape[axis] - win_size + 1
                if sliding_count < 1:
                    raise ValueError(
                        f"Invalid axis {axis} for input shape {in_type.shape} and win_size {win_size}"
                    )
                np_out_shape[axis] = sliding_count

            out_types.append(PortValueType(in_type.data_type, tuple(np_out_shape[1:])))
        return out_types

    def set_properties(self, properties: dict[str, PropertyDataType]):
        win_size = self._win_size
        if "win_size" in properties:
            win_size = int(properties["win_size"])
            if win_size < 1:
                raise ValueError("win_size must be greater than 0")

        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string")
            in_types = [name_to_port_value_type(v) for v in in_types_str.split(",")]

        axis = self._axis
        if "axis" in properties:
            axis = int(properties["axis"])
            if axis < 0:
                raise ValueError("axis must be greater than or equal to 0")

        if (
            in_types != self._in_types
            or axis != self._axis
            or win_size != self._win_size
        ):
            out_types = self._get_out_types(in_types, win_size, axis)
            output_values = StaticTypeOutputPort("values", out_types)
            if self.parent_graph is not None:
                self.parent_graph.disconnect_all_from_node_output(
                    self.name, self._output_values.name
                )
            self._output_values = output_values
            self.outputs[output_values.name] = output_values

            if in_types != self._in_types:
                input_values = StaticTypeInputPort("values", in_types)
                input_values.subscribe(id(self), self._on_input_values)

                if self.parent_graph is not None:
                    self.parent_graph.disconnect_all_from_node_input(
                        self.name, self._input_values.name
                    )

                self._input_values.unsubscribe(id(self))
                self._input_values = input_values

                self.inputs[input_values.name] = input_values

            self._buffers: list[np.ndarray | None] = [None] * len(in_types)

        self._in_types = in_types
        self._axis = axis
        self._win_size = win_size

        self.properties["in_types"] = ",".join(t.name for t in in_types)
        self.properties["win_size"] = self._win_size
        self.properties["axis"] = self._axis

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_reset(self, reset_any: list[PortValue]):
        self._buffers: list[np.ndarray | None] = [None] * len(self._in_types)

    def _on_input_values(self, values_any: list[PortValue]):
        first_len = len(values_any[0])
        if not np.all([len(v) == first_len for v in values_any]):
            logger.warning("Input values must have the same length")
            return

        out_values: list = [None] * len(self._in_types)

        for i, (value_array, value_type, buffer) in enumerate(
            zip(values_any, self._in_types, self._buffers)
        ):
            # print(f"{buffer=}, {value_array=}")
            if buffer is None:
                buffer = value_array.copy()
            else:
                buffer = np.concatenate([buffer, value_array])
            self._buffers[i] = buffer

            if len(buffer) < self._win_size:
                return

            try:
                out_value = sliding_window_view(buffer, self._win_size, axis=self._axis)
            except Exception as e:
                logger.warning(f"{self.name}: {e=}")
                return
            out_values[i] = out_value

            buffer = buffer[len(buffer) - self._win_size + 1 :].copy()
            self._buffers[i] = buffer

        self._output_values.dispatch(out_values)
        # print(f"{out_values=}, {out_values[0].shape=}")


class SeriesShiftNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Time-shift multiple series by different offsets for alignment",
            category="Buffer",
            inputs={
                "in": "Multiple time series to align",
            },
            outputs={
                "out": "Time-shifted and aligned series",
            },
        )

    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input value types",
            "data_type": "str",
            "default_value": "f32,f32",
        },
        "shifts": {
            "description": "Comma-separated shift offsets per series",
            "data_type": "str",
            "default_value": "0,1",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "SeriesShift")

        in_types = [PortValueType(DataType.Float32), PortValueType(DataType.Float32)]
        shifts = [0, 1]

        input_in = StaticTypeInputPort(
            "in",
            in_types,
        )
        input_in.subscribe(id(self), self._on_input_in)

        output_out = StaticTypeOutputPort(
            "out",
            in_types,
        )

        self._input_in = input_in
        self._output_out = output_out
        self._shifts = shifts
        self._in_types = in_types
        self._buffers: list[np.ndarray | None] = [None] * len(in_types)
        self._max_shift = max(shifts)
        self._shifted = False

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string")
            in_types = [name_to_port_value_type(v) for v in in_types_str.split(",")]

        shifts = self._shifts
        if "shifts" in properties:
            shifts_str = properties["shifts"]
            if not isinstance(shifts_str, str):
                raise ValueError("shifts must be a string")
            shifts = [int(s) for s in shifts_str.split(",")]

        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_types != self._in_types:
            new_input_in = StaticTypeInputPort("in", in_types)
            new_output_out = StaticTypeOutputPort("out", in_types)

        if len(shifts) != len(in_types):
            raise ValueError("shifts must be the same length as in_types")

        if shifts != self._shifts or in_types != self._in_types:
            self._max_shift = max(shifts)
            self._shifts = shifts
            self._buffers: list[np.ndarray | None] = [None] * len(in_types)
            self._shifted = False

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        self._in_types = in_types
        self.properties["in_types"] = ",".join(t.name for t in in_types)
        self.properties["shifts"] = ",".join(str(s) for s in shifts)

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        first_len = len(values[0])
        if not np.all([len(v) == first_len for v in values]):
            logger.warning("Input values must have the same length")
            return

        out_values: list = [None] * len(self._in_types)

        for i, (value_array, value_type, shift) in enumerate(
            zip(values, self._in_types, self._shifts)
        ):
            buffer = self._buffers[i]

            if buffer is None:
                buffer = value_array.copy()
            else:
                buffer = np.concatenate([buffer, value_array])

            # print(f"{i=}, {buffer=}")

            # Check the buffered length
            buffer_len = len(buffer)
            if not self._shifted and buffer_len <= self._max_shift:
                self._buffers[i] = buffer
                continue  # not enough data yet; keep accumulating

            # Precompute the slice bounds to keep both branches cheap
            if self._shifted:
                slice_end = buffer_len - (self._max_shift - shift)
                out_values[i] = buffer[:slice_end]
                # Keep only the part still needed
                self._buffers[i] = buffer[slice_end:].copy()
                # print(f"{self._buffers[i]=}")
            else:
                # First output: slice starting at the shift offset
                output_end = buffer_len - (self._max_shift - shift)
                out_values[i] = buffer[shift:output_end]
                # Keep only the remaining part still needed
                self._buffers[i] = buffer[output_end:].copy()
                # print(f"{self._buffers[i]=}")

        if out_values[0] is None:
            return

        self._shifted = True
        # print(f"{out_values=}")
        self._output_out.dispatch(out_values)


class ValuesRingBufferNode(BaseNode):
    """Fixed-size ring buffer with index-based random access.

    Accumulates values in a circular buffer. When full, oldest values are
    overwritten. Supports random access via index input (0=newest, -1=previous, etc.).
    """

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Fixed-size ring buffer with index-based random access",
            category="Buffer",
            inputs={
                "values": "Values to write into the ring buffer",
                "index": "Indices for random access (0=newest, -1=previous)",
                "reset": "Reset buffer and count to zero",
            },
            outputs={
                "values": "Values at requested indices",
                "count": "Current number of stored values",
                "index": "Clamped indices actually used for lookup",
            },
        )

    PROPERTIES = {
        "size": {
            "description": "Ring buffer capacity",
            "data_type": "i32",
            "default_value": 120,
        },
        "value_type_list": {
            "description": "Comma-separated port value types",
            "data_type": "str",
            "default_value": "f32,f32",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ValuesRingBuffer")

        value_type_list = [
            PortValueType(DataType.Float32),
            PortValueType(DataType.Float32),
        ]

        input_values = StaticTypeInputPort(
            "values",
            value_type_list,
        )
        input_values.subscribe(id(self), self._on_values)

        input_index = StaticTypeInputPort(
            "index",
            [PortValueType(DataType.Int32)],
        )
        input_index.subscribe(id(self), self._on_index)

        input_reset = StaticTypeInputPort(
            "reset",
            [PortValueType(DataType.Any)],
        )
        input_reset.subscribe(id(self), self._on_reset)

        output_values = StaticTypeOutputPort(
            "values",
            value_type_list,
        )
        output_count = StaticTypeOutputPort(
            "count",
            [PortValueType(DataType.Int32)],
        )
        output_index = StaticTypeOutputPort(
            "index",
            [PortValueType(DataType.Int32)],
        )

        self._buffer_size = int(self.properties["size"])
        self._value_type_list = value_type_list
        self._buffer: list[np.ndarray] = self._make_buffer(
            self._buffer_size, value_type_list
        )
        self._write_pos = 0
        self._count = 0

        self._input_values = input_values
        self._input_index = input_index
        self._output_values = output_values
        self._output_count = output_count
        self._output_index = output_index

        self.inputs[input_values.name] = input_values
        self.inputs[input_index.name] = input_index
        self.inputs[input_reset.name] = input_reset
        self.outputs[output_values.name] = output_values
        self.outputs[output_index.name] = output_index
        self.outputs[output_count.name] = output_count

    @staticmethod
    def _make_buffer(
        buffer_size: int, value_type_list: list[PortValueType]
    ) -> list[np.ndarray]:
        return [
            np.zeros(
                (buffer_size,) + vt.shape,
                dtype=data_type_to_numpy_dtype(vt.data_type),
            )
            for vt in value_type_list
        ]

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract
        size = self._buffer_size
        if "size" in properties:
            size = int(properties["size"])
            if size < 1:
                raise ValueError("size must be greater than 0")

        value_type_list = self._value_type_list
        if "value_type_list" in properties:
            value_type_list_str = properties["value_type_list"]
            if not isinstance(value_type_list_str, str):
                raise ValueError("value_type_list must be a string")
            value_type_list = [
                name_to_port_value_type(v) for v in value_type_list_str.split(",")
            ]
            for vt in value_type_list:
                if vt.data_type == DataType.Any:
                    raise ValueError(
                        f"DataType.Any is not supported for ring buffer: {vt.name}"
                    )
                if any(d < 0 for d in vt.shape):
                    raise ValueError(
                        f"Variable dimensions not supported for ring buffer: {vt.name}"
                    )

        # 2. Prepare new ports
        new_input_values = self._input_values
        new_output_values = self._output_values
        if value_type_list != self._value_type_list:
            new_input_values = StaticTypeInputPort("values", value_type_list)
            new_output_values = StaticTypeOutputPort("values", value_type_list)

        # 3. Update
        if new_input_values is not self._input_values:
            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_values
            )
            self._input_values = new_input_values

        if new_output_values is not self._output_values:
            replace_node_output_port(self, self._output_values, new_output_values)
            self._output_values = new_output_values

        need_realloc = False
        if value_type_list != self._value_type_list:
            self._value_type_list = value_type_list
            need_realloc = True
        if size != self._buffer_size:
            self._buffer_size = size
            need_realloc = True

        if need_realloc:
            self._buffer = self._make_buffer(self._buffer_size, self._value_type_list)
            self._write_pos = 0
            self._count = 0

        self.properties["size"] = self._buffer_size
        self.properties["value_type_list"] = ",".join(
            v.name for v in self._value_type_list
        )

        # 4. Notify
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_reset(self, values: list[PortValue]):
        self._write_pos = 0
        self._count = 0
        self._output_count.dispatch([np.array([0], dtype=np.int32)])

    def _on_values(self, values: list[PortValue]):
        batch_len = len(values[0])
        if not all(len(v) == batch_len for v in values):
            logger.warning(f"{self.name}: Input values must have the same length")
            return

        size = self._buffer_size
        wp = self._write_pos

        if batch_len >= size:
            # Overwrite the whole buffer — only the trailing `size` samples matter
            for ch, buf in enumerate(self._buffer):
                buf[:] = values[ch][-size:]
            self._write_pos = 0
            self._count = size
        else:
            end = wp + batch_len
            if end <= size:
                # No wrap — single slice assignment
                for ch, buf in enumerate(self._buffer):
                    buf[wp:end] = values[ch]
            else:
                # Wraps around — two slice assignments
                first = size - wp
                for ch, buf in enumerate(self._buffer):
                    buf[wp:size] = values[ch][:first]
                    buf[: end - size] = values[ch][first:]
            self._write_pos = end % size
            self._count = min(self._count + batch_len, size)

        self._output_count.dispatch([np.array([self._count], dtype=np.int32)])

    def _on_index(self, values: list[PortValue]):
        indices = values[0]
        count = self._count
        size = self._buffer_size

        if count == 0:
            return

        # Clamp indices to valid range: [-(count-1), 0]
        clamped = np.clip(indices, -(count - 1), 0)

        # Convert logical index to buffer position
        # index=0 → write_pos-1, index=-1 → write_pos-2, ...
        buf_positions = (self._write_pos - 1 + clamped) % size

        self._output_values.dispatch([buf[buf_positions] for buf in self._buffer])
        self._output_index.dispatch([clamped])
