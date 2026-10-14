from typing import Any
import numpy as np
import logging
import json
from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)
from nonoha_core.node import BaseNode, NodeDoc, replace_node_input_port, replace_node_output_port
from nonoha_core.data_type import (
    DataType,
    PortValueType,
    PropertyDataType,
    name_to_port_value_type,
    name_to_data_type,
    data_type_to_name,
    data_type_to_numpy_dtype,
    str_to_shape,
)

logger = logging.getLogger(__name__)


class RealNumberValueNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Outputs a configurable real number scalar with optional input override",
            category="Value",
            inputs={"dispatch": ""},
            outputs={"value": ""},
        )

    PROPERTIES = {
        "value_type": {
            "description": "Data type of the value",
            "data_type": "str",
            "default_value": "f32",
        },
        "default": {
            "description": "Default output value",
            "data_type": "f64",
            "default_value": 0,
        },
        "dispatch_on_init": {
            "description": (
                "Emit `default` value at activation. Set to false when this node is "
                "one of multiple sources writing to a shared destination port, to "
                "avoid order-dependent latched values. When false, the node only "
                "dispatches on explicit `dispatch` input."
            ),
            "data_type": "bool",
            "default_value": True,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "RealNumberValue")

        value_type = PortValueType(DataType.Float32)

        input_dispatch = StaticTypeInputPort("dispatch", [PortValueType(DataType.Any)])
        input_dispatch.subscribe(id(self), self._on_input_dispatch)

        output_value = StaticTypeOutputPort("value", [value_type])
        default = 0
        dispatch_on_init = True

        self._value_type = value_type
        self._output_value = output_value
        self._default = default
        self._dispatch_on_init = dispatch_on_init

        self.inputs[input_dispatch.name] = input_dispatch
        self.outputs[output_value.name] = output_value

    def activate(self):
        # Emit the configured default once at activation when dispatch_on_init is set.
        # Skip if current_values is already populated (e.g. the `dispatch` port fired
        # during edge connection) to avoid a duplicate emit.
        # No flush_outputs() here: node-to-node propagation completes synchronously
        # via dispatch; committing buffered graph outputs is the graph's concern.
        if self._dispatch_on_init and self._output_value.current_values is None:
            self._output_value.dispatch([np.array([self._default])])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        value_type = self._value_type

        if "value_type" in properties:
            value_type_str = properties["value_type"]
            if not isinstance(value_type_str, str):
                raise ValueError("value_type must be a string")

            value_type = name_to_port_value_type(value_type_str)

        if value_type.data_type not in [
            DataType.Bool,
            DataType.Int8,
            DataType.Uint8,
            DataType.Int16,
            DataType.Uint16,
            DataType.Int32,
            DataType.Uint32,
            DataType.Int64,
            DataType.Uint64,
            DataType.Float32,
            DataType.Float64,
        ]:
            raise ValueError("Invalid data_type. Must be real number type.")

        if value_type.shape != ():
            raise ValueError("Invalid shape. Must be scalar.")

        default = self._default

        if "default" in properties:
            value_prop = properties["default"]
            match value_type.data_type:
                case DataType.Bool:
                    default = bool(value_prop)
                case DataType.Float32 | DataType.Float64:
                    default = float(value_prop)
                case _:
                    default = int(value_prop)

        dispatch_on_init = self._dispatch_on_init
        if "dispatch_on_init" in properties:
            dispatch_on_init = bool(properties["dispatch_on_init"])

        new_output_value = self._output_value
        if self._value_type != value_type:
            new_output_value = StaticTypeOutputPort("value", [value_type])

        should_value_dispatch = (self._default != default) or (
            self._output_value != new_output_value
        )

        if new_output_value != self._output_value:
            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        self._value_type = value_type
        self._default = default
        self._dispatch_on_init = dispatch_on_init

        self.properties["value_type"] = value_type.name
        self.properties["default"] = default
        self.properties["dispatch_on_init"] = dispatch_on_init

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

        if should_value_dispatch and self._dispatch_on_init and self._is_active:
            self._output_value.dispatch([np.array([default])])
            if self.parent_graph is not None:
                self.parent_graph.flush_outputs()

    def _on_input_dispatch(self, values_any: list[Any]):
        # Always emit the configured default — independent of any prior `in`
        # input and of dispatch_on_init state. Makes this node usable as a
        # pulse-triggered constant emitter.
        self._output_value.dispatch([np.array([self._default])])


class ComplexNumberValueNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Outputs a configurable complex number scalar with optional input override",
            category="Value",
            inputs={"dispatch": ""},
            outputs={"value": ""},
        )

    PROPERTIES = {
        "value_type": {
            "description": "Data type of the value (c64 or c128)",
            "data_type": "str",
            "default_value": "c64",
        },
        "default": {
            "description": "Default output value (complex string)",
            "data_type": "str",
            "default_value": "0.0+0.0j",
        },
        "dispatch_on_init": {
            "description": (
                "Emit `default` value at activation. Set to false when this node is "
                "one of multiple sources writing to a shared destination port, to "
                "avoid order-dependent latched values. When false, the node only "
                "dispatches on explicit `dispatch` input."
            ),
            "data_type": "bool",
            "default_value": True,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ComplexNumberValue")

        value_type = PortValueType(DataType.Complex64)

        input_dispatch = StaticTypeInputPort("dispatch", [PortValueType(DataType.Any)])
        input_dispatch.subscribe(id(self), self._on_input_dispatch)

        output_value = StaticTypeOutputPort("value", [value_type])
        default = complex(0)
        dispatch_on_init = True

        self._value_type = value_type
        self._output_value = output_value
        self._default = default
        self._dispatch_on_init = dispatch_on_init

        self.inputs[input_dispatch.name] = input_dispatch
        self.outputs[output_value.name] = output_value

    def activate(self):
        # Emit the configured default once at activation when dispatch_on_init is set.
        # Skip if current_values is already populated (e.g. the `dispatch` port fired
        # during edge connection) to avoid a duplicate emit.
        # No flush_outputs() here: node-to-node propagation completes synchronously
        # via dispatch; committing buffered graph outputs is the graph's concern.
        if self._dispatch_on_init and self._output_value.current_values is None:
            self._output_value.dispatch([np.array([self._default])])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        value_type = self._value_type

        if "value_type" in properties:
            value_type_str = properties["value_type"]
            if not isinstance(value_type_str, str):
                raise ValueError("value_type must be a string")

            value_type = name_to_port_value_type(value_type_str)

        if value_type.data_type not in [
            DataType.Complex64,
            DataType.Complex128,
        ]:
            raise ValueError("Invalid value_type")

        if value_type.shape != ():
            raise ValueError("Invalid shape. Must be scalar.")

        default = self._default

        if "default" in properties:
            value_prop = properties["default"]
            match value_type.data_type:
                case DataType.Complex64 | DataType.Complex128:
                    default = complex(value_prop)
                case _:
                    default = complex(float(value_prop))

        dispatch_on_init = self._dispatch_on_init
        if "dispatch_on_init" in properties:
            dispatch_on_init = bool(properties["dispatch_on_init"])

        new_output_value = self._output_value

        if self._value_type != value_type:
            new_output_value = StaticTypeOutputPort("value", [value_type])

        should_value_dispatch = (self._default != default) or (
            self._output_value != new_output_value
        )

        if new_output_value != self._output_value:
            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        self._value_type = value_type
        self._default = default
        self._dispatch_on_init = dispatch_on_init

        self.properties["value_type"] = value_type.name
        self.properties["default"] = (
            f"{default.real}{'+' if default.imag >= 0 else ''}{default.imag}j"
        )
        self.properties["dispatch_on_init"] = dispatch_on_init

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

        if should_value_dispatch and self._dispatch_on_init and self._is_active:
            self._output_value.dispatch([np.array([default])])
            if self.parent_graph is not None:
                self.parent_graph.flush_outputs()

    def _on_input_dispatch(self, values_any: list[Any]):
        # Always emit the configured default — independent of any prior `in`
        # input and of dispatch_on_init state. Makes this node usable as a
        # pulse-triggered constant emitter.
        self._output_value.dispatch([np.array([self._default])])


class StringValueNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Outputs a configurable string value with optional input override",
            category="Value",
            inputs={"dispatch": ""},
            outputs={"value": ""},
        )

    PROPERTIES = {
        "default": {
            "description": "Default output string",
            "data_type": "str",
            "default_value": "hello_world!",
        },
        "dispatch_on_init": {
            "description": (
                "Emit `default` value at activation. Set to false when this node is "
                "one of multiple sources writing to a shared destination port, to "
                "avoid order-dependent latched values. When false, the node only "
                "dispatches on explicit `dispatch` input."
            ),
            "data_type": "bool",
            "default_value": True,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "StringValue")

        input_dispatch = StaticTypeInputPort("dispatch", [PortValueType(DataType.Any)])
        input_dispatch.subscribe(id(self), self._on_input_dispatch)

        output_value = StaticTypeOutputPort("value", [PortValueType(DataType.String)])
        default = "hello_world!"
        dispatch_on_init = True

        self._output_value = output_value
        self._default = default
        self._dispatch_on_init = dispatch_on_init

        self.inputs[input_dispatch.name] = input_dispatch
        self.outputs[output_value.name] = output_value

    def activate(self):
        # Emit the configured default once at activation when dispatch_on_init is set.
        # Skip if current_values is already populated (e.g. the `dispatch` port fired
        # during edge connection) to avoid a duplicate emit.
        # No flush_outputs() here: node-to-node propagation completes synchronously
        # via dispatch; committing buffered graph outputs is the graph's concern.
        if self._dispatch_on_init and self._output_value.current_values is None:
            self._output_value.dispatch(
                [np.array([self._default], dtype=np.dtypes.StringDType)]  # type: ignore
            )

    def set_properties(self, properties: dict[str, PropertyDataType]):
        default = self._default

        if "default" in properties:
            default = str(properties["default"])

        dispatch_on_init = self._dispatch_on_init
        if "dispatch_on_init" in properties:
            dispatch_on_init = bool(properties["dispatch_on_init"])

        default_changed = self._default != default

        self._default = default
        self._dispatch_on_init = dispatch_on_init

        self.properties["default"] = default
        self.properties["dispatch_on_init"] = dispatch_on_init

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

        if default_changed and self._dispatch_on_init and self._is_active:
            self._output_value.dispatch(
                [np.array([default], dtype=np.dtypes.StringDType)]  # type: ignore
            )
            if self.parent_graph is not None:
                self.parent_graph.flush_outputs()

    def _on_input_dispatch(self, values_any: list[PortValue]):
        # Always emit the configured default — independent of any prior `in`
        # input and of dispatch_on_init state. Makes this node usable as a
        # pulse-triggered constant emitter.
        self._output_value.dispatch(
            [np.array([self._default], dtype=np.dtypes.StringDType())]  # type: ignore[call-arg]
        )


class ArrayValueNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Outputs a configurable array value with optional input override",
            category="Value",
            inputs={"dispatch": ""},
            outputs={"value": ""},
        )

    PROPERTIES = {
        "value_type": {
            "description": "Data type and shape of the array",
            "data_type": "str",
            "default_value": "f32[3]",
        },
        "default": {
            "description": "Default array value (JSON)",
            "data_type": "str",
            "default_value": "[0, 0, 0]",
        },
        "dispatch_on_init": {
            "description": (
                "Emit `default` value at activation. Set to false when this node is "
                "one of multiple sources writing to a shared destination port, to "
                "avoid order-dependent latched values. When false, the node only "
                "dispatches on explicit `dispatch` input."
            ),
            "data_type": "bool",
            "default_value": True,
        },
    }

    _DATA_TYPE_TO_NUMPY_DTYPE = {
        DataType.Bool: np.bool_,
        DataType.Int8: np.int8,
        DataType.Uint8: np.uint8,
        DataType.Int16: np.int16,
        DataType.Uint16: np.uint16,
        DataType.Int32: np.int32,
        DataType.Uint32: np.uint32,
        DataType.Int64: np.int64,
        DataType.Uint64: np.uint64,
        DataType.Float32: np.float32,
        DataType.Float64: np.float64,
        DataType.Complex64: np.complex64,
        DataType.Complex128: np.complex128,
    }

    def __init__(self, name: str):
        super().__init__(name, "ArrayValue")

        value_type = PortValueType(DataType.Float32, (3,))
        input_dispatch = StaticTypeInputPort("dispatch", [PortValueType(DataType.Any)])
        input_dispatch.subscribe(id(self), self._on_input_dispatch)
        output_value = StaticTypeOutputPort("value", [value_type])

        # Default: 1 batch with 3 elements, all zeros
        np_dtype = self._DATA_TYPE_TO_NUMPY_DTYPE[value_type.data_type]
        default = np.array([[0, 0, 0]], dtype=np_dtype)
        default_json = json.dumps([0, 0, 0])  # Store as flat list in JSON
        dispatch_on_init = True

        self._value_type = value_type
        self._output_value = output_value
        self._default_json = default_json
        # Cache the parsed default array so `dispatch` trigger and other paths
        # can re-emit it without re-parsing the JSON.
        self._default_array = default
        self._dispatch_on_init = dispatch_on_init

        self.inputs[input_dispatch.name] = input_dispatch
        self.outputs[output_value.name] = output_value

    def activate(self):
        # Emit the configured default once at activation when dispatch_on_init is set.
        # Skip if current_values is already populated (e.g. the `dispatch` port fired
        # during edge connection) to avoid a duplicate emit.
        # No flush_outputs() here: node-to-node propagation completes synchronously
        # via dispatch; committing buffered graph outputs is the graph's concern.
        if self._dispatch_on_init and self._output_value.current_values is None:
            self._output_value.dispatch([self._default_array])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        value_type = self._value_type
        if "value_type" in properties:
            value_type_str = properties["value_type"]
            if not isinstance(value_type_str, str):
                raise ValueError("value_type must be a string")

            value_type = name_to_port_value_type(value_type_str)

        # Validate data type
        if value_type.data_type == DataType.Any:
            raise ValueError("DataType.Any is not supported")

        default_json = self._default_json
        if "default" in properties:
            default_json_prop = properties["default"]
            if not isinstance(default_json_prop, str):
                raise ValueError("default must be a string")
            default_json = default_json_prop

        dispatch_on_init = self._dispatch_on_init
        if "dispatch_on_init" in properties:
            dispatch_on_init = bool(properties["dispatch_on_init"])

        # Parse and validate default value
        default_array = None
        should_dispatch = False
        if default_json != self._default_json or value_type != self._value_type:
            try:
                parsed_list = json.loads(default_json)

                # Convert to appropriate dtype based on data_type
                if value_type.data_type == DataType.String:
                    default_array = np.array(parsed_list, dtype=np.dtypes.StringDType)  # type: ignore
                elif value_type.data_type in [DataType.Complex64, DataType.Complex128]:
                    # Parse complex numbers from string list: ["1+2j", "3+4j"]
                    # or from [real, imag] pairs: [[1, 2], [3, 4]]
                    if len(parsed_list) > 0 and isinstance(parsed_list[0], str):
                        # String format: ["1+2j", "3+4j"]
                        complex_values = [complex(s) for s in parsed_list]
                    elif len(parsed_list) > 0 and isinstance(
                        parsed_list[0], (list, tuple)
                    ):
                        # [real, imag] pair format: [[1, 2], [3, 4]]
                        complex_values = [complex(r, i) for r, i in parsed_list]
                    else:
                        # Assume real numbers, convert to complex
                        complex_values = [complex(x) for x in parsed_list]

                    dtype = (
                        np.complex64
                        if value_type.data_type == DataType.Complex64
                        else np.complex128
                    )
                    default_array = np.array(complex_values, dtype=dtype)
                else:
                    # Real number types
                    np_dtype = self._DATA_TYPE_TO_NUMPY_DTYPE.get(
                        value_type.data_type, np.float32
                    )
                    default_array = np.array(parsed_list, dtype=np_dtype)

                # Reshape with batch dimension (-1) as first dimension
                if value_type.shape != ():
                    target_shape = (-1,) + value_type.shape
                    default_array = default_array.reshape(target_shape)
                else:
                    # Scalar case - ensure it's a 1D array
                    default_array = default_array.reshape(-1)

                should_dispatch = True

            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")
            except ValueError as e:
                raise ValueError(
                    f"Failed to reshape array: {e}. Expected total elements to match shape {value_type.shape}"
                )

        new_output_value = self._output_value
        if value_type != self._value_type:
            new_output_value = StaticTypeOutputPort("value", [value_type])

        if new_output_value != self._output_value:
            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        self._value_type = value_type
        self._default_json = default_json
        self._dispatch_on_init = dispatch_on_init

        self.properties["value_type"] = value_type.name
        self.properties["default"] = default_json
        self.properties["dispatch_on_init"] = dispatch_on_init

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

        # Cache the new parsed default array for future `dispatch` triggers
        # and emission gating (independent of dispatch_on_init).
        if should_dispatch and default_array is not None:
            self._default_array = default_array

        # Dispatch new default value if changed
        if (
            should_dispatch
            and default_array is not None
            and self._dispatch_on_init
            and self._is_active
        ):
            self._output_value.dispatch([default_array])
            if self.parent_graph is not None:
                self.parent_graph.flush_outputs()

    def _on_input_dispatch(self, values: list[PortValue]):
        # Always emit the configured default array — independent of any prior
        # `in` input and of dispatch_on_init state. Makes this node usable as
        # a pulse-triggered constant emitter.
        self._output_value.dispatch([self._default_array])


class EmptyValueNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Outputs an empty (zero-batch) array of the configured type and shape",
            category="Value",
            inputs={},
            outputs={"value": ""},
        )

    PROPERTIES = {
        "value_type": {
            "description": "Data type and shape of the empty array",
            "data_type": "str",
            "default_value": "f32",
        },
    }

    _DATA_TYPE_TO_NUMPY_DTYPE = {
        DataType.Bool: np.bool_,
        DataType.Int8: np.int8,
        DataType.Uint8: np.uint8,
        DataType.Int16: np.int16,
        DataType.Uint16: np.uint16,
        DataType.Int32: np.int32,
        DataType.Uint32: np.uint32,
        DataType.Int64: np.int64,
        DataType.Uint64: np.uint64,
        DataType.Float32: np.float32,
        DataType.Float64: np.float64,
        DataType.Complex64: np.complex64,
        DataType.Complex128: np.complex128,
    }

    def __init__(self, name: str):
        super().__init__(name, "EmptyValue")

        value_type = PortValueType(DataType.Float32)

        output_value = StaticTypeOutputPort("value", [value_type])

        # Empty array with shape (0,) for scalar, (0, *shape) for shaped types
        empty_value = self._create_empty_array(value_type)

        self._empty_value = empty_value
        self._output_value = output_value
        self._value_type = value_type

        self.outputs[output_value.name] = output_value

        output_value.dispatch([self._empty_value])

    def _create_empty_array(self, value_type: PortValueType) -> np.ndarray:
        """Create empty array with correct dtype and shape."""
        if value_type.data_type not in self._DATA_TYPE_TO_NUMPY_DTYPE:
            raise ValueError(
                f"Unsupported data type for EmptyValue: {value_type.data_type}"
            )
        np_dtype = self._DATA_TYPE_TO_NUMPY_DTYPE[value_type.data_type]

        # Shape: (0,) for scalar, (0, *shape) for shaped types
        empty_shape = (0,) + value_type.shape
        return np.empty(empty_shape, dtype=np_dtype)

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract and validate properties
        value_type = self._value_type
        if "value_type" in properties:
            value_type_str = properties["value_type"]
            if not isinstance(value_type_str, str):
                raise ValueError("value_type must be a string")
            value_type = name_to_port_value_type(value_type_str)

        # Validate data type
        if value_type.data_type not in self._DATA_TYPE_TO_NUMPY_DTYPE:
            raise ValueError(
                f"Unsupported data type for EmptyValue: {value_type.data_type}"
            )

        # 2. Create new port if necessary
        new_output_value = self._output_value
        if value_type != self._value_type:
            new_output_value = StaticTypeOutputPort("value", [value_type])

        # 3. Create empty array with correct dtype and shape
        empty_value = self._create_empty_array(value_type)

        # 4. Replace port atomically if changed
        should_dispatch = new_output_value is not self._output_value
        if should_dispatch:
            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        # 5. Update instance variables and properties dictionary
        self._value_type = value_type
        self._empty_value = empty_value
        self.properties["value_type"] = value_type.name

        # 6. Notify graph of updates
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

        # Dispatch new empty value if port changed
        if should_dispatch:
            self._output_value.dispatch([self._empty_value])
            if self.parent_graph is not None:
                self.parent_graph.flush_outputs()


class ValuesGetLastNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Extract the last batch element from each value in the port",
            category="Value",
            inputs={"values": ""},
            outputs={"values": ""},
        )

    PROPERTIES = {
        "value_type_list": {
            "description": "Comma-separated value types",
            "data_type": "str",
            "default_value": "f32,f32",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ValuesGetLast")

        value_type_list = [
            PortValueType(DataType.Float32),
            PortValueType(DataType.Float32),
        ]

        input_values = StaticTypeInputPort("values", value_type_list)
        input_values.subscribe(id(self), self._on_input_values)

        output_values = StaticTypeOutputPort("values", value_type_list)

        self._input_values = input_values
        self._output_values = output_values
        self._value_type_list = value_type_list

        self.inputs[input_values.name] = input_values
        self.outputs[output_values.name] = output_values

    def set_properties(self, properties: dict[str, PropertyDataType]):
        value_type_list = self._value_type_list

        if "value_type_list" in properties:
            value_type_list_str = properties["value_type_list"]
            if not isinstance(value_type_list_str, str):
                raise ValueError("value_type_list must be a string")

            value_type_list = [
                name_to_port_value_type(name.strip())
                for name in value_type_list_str.split(",")
            ]

        new_input_values = self._input_values
        new_output_values = self._output_values

        if value_type_list != self._value_type_list:
            new_input_values = StaticTypeInputPort("values", value_type_list)

            new_output_values = StaticTypeOutputPort("values", value_type_list)

        if new_input_values != self._input_values:
            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values

        if new_output_values != self._output_values:
            replace_node_output_port(
                self,
                self._output_values,
                new_output_values,
            )
            self._output_values = new_output_values

        self._value_type_list = value_type_list

        self.properties["value_type_list"] = ",".join([t.name for t in value_type_list])

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, values: list[PortValue]):
        out = [value_array[-1:] for value_array in values]
        self._output_values.dispatch(out)


class ValueCounterNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Counts cumulative number of received batch elements",
            category="Value",
            inputs={"value": "", "reset": ""},
            outputs={"count": ""},
        )

    PROPERTIES = {
        "reset_on_input": {
            "description": "Reset counter on each input",
            "data_type": "bool",
            "default_value": False,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ValueCounter")

        input_values = StaticTypeInputPort("value", [PortValueType(DataType.Any)])
        input_values.subscribe(id(self), self._on_values)
        input_reset = StaticTypeInputPort("reset", [PortValueType(DataType.Any)])
        input_reset.subscribe(id(self), self._on_reset)

        output_count = StaticTypeOutputPort("count", [PortValueType(DataType.Int32)])

        self._count = 0
        self._input_values = input_values
        self._output_count = output_count
        self._reset_on_input = False

        self.inputs[input_values.name] = input_values
        self.inputs[input_reset.name] = input_reset
        self.outputs[output_count.name] = output_count

    def set_properties(self, properties: dict[str, PropertyDataType]):
        reset_on_input = self._reset_on_input
        if "reset_on_input" in properties:
            reset_on_input = bool(properties["reset_on_input"])
            self._reset_on_input = reset_on_input

        self.properties["reset_on_input"] = reset_on_input

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_reset(self, values: list[PortValue]):
        self._count = 0
        self._output_count.dispatch([np.array([self._count])])

    def _on_values(self, values: list[PortValue]):
        value_array = values[0]
        self._count += len(value_array)
        self._output_count.dispatch([np.array([self._count])])
        if self._reset_on_input:
            self._count = 0


class EnumerateNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Assigns cumulative sequential indices to each sample in a batch",
            category="Value",
            inputs={"value": "", "start": ""},
            outputs={"index": ""},
        )

    """Assigns cumulative sequential indices to each sample in a batch.

    Each dispatch on ``value`` produces ``[counter, counter+1, ..., counter+N-1]``
    where *N* is the batch size of the input.  The counter advances across
    dispatches.

    The ``start`` input resets the counter to the received value.
    """

    def __init__(self, name: str):
        super().__init__(name, "Enumerate")

        input_value = StaticTypeInputPort("value", [PortValueType(DataType.Any)])
        input_value.subscribe(id(self), self._on_value)
        input_start = StaticTypeInputPort("start", [PortValueType(DataType.Int32)])
        input_start.subscribe(id(self), self._on_start)

        output_index = StaticTypeOutputPort("index", [PortValueType(DataType.Int32)])

        self._counter = 0
        self._input_value = input_value
        self._input_start = input_start
        self._output_index = output_index

        self.inputs[input_value.name] = input_value
        self.inputs[input_start.name] = input_start
        self.outputs[output_index.name] = output_index

    def _on_start(self, values: list[PortValue]):
        self._counter = int(values[0][-1])

    def _on_value(self, values: list[PortValue]):
        n = len(values[0])
        indices = np.arange(self._counter, self._counter + n, dtype=np.int32)
        self._counter += n
        self._output_index.dispatch([indices])


class AsTypeNode(BaseNode):
    # <https://numpy.org/devdocs/reference/generated/numpy.ndarray.astype.html>
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Cast array to a different data type",
            category="Value",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    PROPERTIES = {
        "in_type": {
            "description": "Input data type and shape",
            "data_type": "str",
            "default_value": "f32",
        },
        "out_data_type": {
            "description": "Output data type",
            "data_type": "str",
            "default_value": "i16",
        },
    }

    _DATA_TYPE_TO_NUMPY_DTYPE = {
        DataType.Bool: np.bool_,
        DataType.Int8: np.int8,
        DataType.Uint8: np.uint8,
        DataType.Int16: np.int16,
        DataType.Uint16: np.uint16,
        DataType.Int32: np.int32,
        DataType.Uint32: np.uint32,
        DataType.Int64: np.int64,
        DataType.Uint64: np.uint64,
        DataType.Float32: np.float32,
        DataType.Float64: np.float64,
        DataType.Complex64: np.complex64,
        DataType.Complex128: np.complex128,
    }

    def __init__(self, name: str):
        super().__init__(name, "AsType")

        in_type = PortValueType(DataType.Float32)
        out_data_type = DataType.Int16

        out_type = PortValueType(out_data_type, in_type.shape)

        input_in = StaticTypeInputPort("in", [in_type])
        input_in.subscribe(id(self), self._on_input_in)

        output_out = StaticTypeOutputPort("out", [out_type])

        self._in_type = in_type
        self._out_data_type = out_data_type
        self._out_np_dtype = self._DATA_TYPE_TO_NUMPY_DTYPE[out_data_type]
        self._input_in = input_in
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_type = self._in_type
        out_data_type = self._out_data_type
        out_np_dtype = self._out_np_dtype

        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("in_type must be a string")

            in_type = name_to_port_value_type(in_type_str)

        if "out_data_type" in properties:
            out_data_type_str = properties["out_data_type"]
            if not isinstance(out_data_type_str, str):
                raise ValueError("out_data_type must be a string")

            out_data_type = name_to_data_type(out_data_type_str)
            out_np_dtype = self._DATA_TYPE_TO_NUMPY_DTYPE[out_data_type]

        new_input_in = self._input_in
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])

        new_output_out = self._output_out
        if (in_type.shape != self._in_type.shape) or (
            out_data_type != self._out_data_type
        ):
            new_output_out = StaticTypeOutputPort(
                "out", [PortValueType(out_data_type, in_type.shape)]
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
        self._out_data_type = out_data_type
        self._out_np_dtype = out_np_dtype

        self.properties["in_type"] = in_type.name
        self.properties["out_data_type"] = data_type_to_name(out_data_type)

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        value_array = values[0]
        try:
            converted = value_array.astype(self._out_np_dtype, copy=False)
        except Exception as e:
            logger.warning(f"{self.name}: Failed to convert value: {e}")
            return

        self._output_out.dispatch([converted])


class FullLikeNode(BaseNode):
    # <https://numpy.org/doc/stable/reference/generated/numpy.full_like.html>
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Create an array with the same shape as input, filled with a specified value",
            category="Value",
            inputs={"in": "", "fill_value": ""},
            outputs={"out": ""},
        )

    PROPERTIES = {
        "value_type": {
            "description": "Data type and shape",
            "data_type": "str",
            "default_value": "f32[3]",
        },
        "fill_value_shape": {
            "description": "Shape of the fill value (empty=scalar)",
            "data_type": "str",
            "default_value": "",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "FullLike")

        value_type = PortValueType(DataType.Float32, (3,))
        fill_value_type = PortValueType(DataType.Float32)  # scalar

        input_in = StaticTypeInputPort("in", [value_type])
        input_in.subscribe(id(self), self._on_input_in)

        input_fill_value = StaticTypeInputPort("fill_value", [fill_value_type])
        input_fill_value.subscribe(id(self), self._on_input_fill_value)

        output_out = StaticTypeOutputPort("out", [value_type])

        self._value_type = value_type
        self._fill_value_type = fill_value_type
        self._n_expand = len(value_type.shape) - len(fill_value_type.shape)
        self._fill_value_ready = self._make_default_fill(
            value_type, fill_value_type, self._n_expand
        )
        self._input_in = input_in
        self._input_fill_value = input_fill_value
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.inputs[input_fill_value.name] = input_fill_value
        self.outputs[output_out.name] = output_out

    @staticmethod
    def _expand_fill(fill: np.ndarray, n_expand: int) -> np.ndarray:
        if n_expand > 0:
            new_shape = fill.shape[:1] + (1,) * n_expand + fill.shape[1:]
            return fill.reshape(new_shape)
        return fill

    @staticmethod
    def _make_default_fill(
        value_type: PortValueType,
        fill_value_type: PortValueType,
        n_expand: int,
    ) -> np.ndarray:
        dtype = data_type_to_numpy_dtype(value_type.data_type)
        fill = np.zeros((1,) + fill_value_type.shape, dtype=dtype)
        return FullLikeNode._expand_fill(fill, n_expand)

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract + validate
        value_type = self._value_type
        if "value_type" in properties:
            value_type_str = properties["value_type"]
            if not isinstance(value_type_str, str):
                raise ValueError("value_type must be a string")
            value_type = name_to_port_value_type(value_type_str)

        if value_type.data_type == DataType.Any:
            raise ValueError("DataType.Any is not supported for FullLike")
        if any(d < 0 for d in value_type.shape):
            raise ValueError("Variable dimensions not supported for FullLike")

        fill_value_shape = self._fill_value_type.shape
        if "fill_value_shape" in properties:
            fvs_str = properties["fill_value_shape"]
            if not isinstance(fvs_str, str):
                raise ValueError("fill_value_shape must be a string")
            fill_value_shape = str_to_shape(fvs_str)
            if any(d < 0 for d in fill_value_shape):
                raise ValueError(
                    "Variable dimensions not supported for fill_value_shape"
                )

        # 2. Derive
        fill_value_type = PortValueType(value_type.data_type, fill_value_shape)

        # 3. Prepare ports
        new_input_in = self._input_in
        new_input_fill_value = self._input_fill_value
        new_output_out = self._output_out
        if value_type != self._value_type:
            new_input_in = StaticTypeInputPort("in", [value_type])
            new_output_out = StaticTypeOutputPort("out", [value_type])
        if fill_value_type != self._fill_value_type:
            new_input_fill_value = StaticTypeInputPort("fill_value", [fill_value_type])

        # 4. Replace ports + commit port refs
        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in
        if new_input_fill_value != self._input_fill_value:
            replace_node_input_port(
                self,
                self._input_fill_value,
                new_input_fill_value,
                self._on_input_fill_value,
            )
            self._input_fill_value = new_input_fill_value
        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        # 5. Commit non-port state
        if value_type != self._value_type or fill_value_type != self._fill_value_type:
            n_expand = len(value_type.shape) - len(fill_value_type.shape)
            self._n_expand = n_expand
            self._fill_value_ready = self._make_default_fill(
                value_type, fill_value_type, n_expand
            )
        self._value_type = value_type
        self._fill_value_type = fill_value_type

        # 6. Update properties dict
        self.properties["value_type"] = value_type.name
        self.properties["fill_value_shape"] = fill_value_type.shape_str

        # 7. Notify graph
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_fill_value(self, values: list[PortValue]):
        self._fill_value_ready = self._expand_fill(values[0], self._n_expand)

    def _on_input_in(self, values: list[PortValue]):
        out = np.empty_like(values[0])
        out[...] = self._fill_value_ready
        self._output_out.dispatch([out])


# class RealNumberRangeNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealNumberRange")

#         output_values = StaticTypePort(
#             "values", PortDirection.OUTPUT, [DataType.Float32]
#         )

#         self._start = 0.0
#         self._stop = 1.0
#         self._step = 0.01
#         self._output_values = output_values

#         self.outputs[output_values.name] = output_values

#         self.properties["start"] = self._start
#         self.properties["stop"] = self._stop
#         self.properties["step"] = self._step

#         # 初期値を生成して出力
#         self._generate_and_dispatch()

#     def set_properties(self, properties: dict[str, PropertyDataType]):
#         changed = False

#         if "start" in properties:
#             self._start = float(properties["start"])
#             changed = True

#         if "stop" in properties:
#             self._stop = float(properties["stop"])
#             changed = True

#         if "step" in properties:
#             self._step = float(properties["step"])
#             changed = True

#         self.properties["start"] = self._start
#         self.properties["stop"] = self._stop
#         self.properties["step"] = self._step

#         if changed:
#             self._generate_and_dispatch()

#         if self.parent_graph is not None:
#             self.parent_graph.notify_properties_changed(self)

#     def _generate_and_dispatch(self):
#         values = np.arange(self._start, self._stop + self._step / 2, self._step)

#         self._output_values.dispatch([values])


class ValueAccumulatorNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Accumulates input values into a running sum with optional clamping",
            category="Value",
            inputs={"in": "", "reset": "", "clamp_min": "", "clamp_max": ""},
            outputs={"value": "", "overflow": "", "underflow": ""},
        )

    PROPERTIES = {
        "value_type": {
            "description": "Data type of the accumulated value",
            "data_type": "str",
            "default_value": "i32",
        },
        "initial_clamp_min": {
            "description": "Initial clamp minimum (empty=unclamped)",
            "data_type": "str",
            "default_value": "",
        },
        "initial_clamp_max": {
            "description": "Initial clamp maximum (empty=unclamped)",
            "data_type": "str",
            "default_value": "",
        },
    }

    """Accumulates input values into a running sum.

    Each dispatch on ``in`` adds the received value to an internal sum and
    outputs the result.  The ``reset`` input resets the sum to 0.

    Optional ``initial_clamp_min`` / ``initial_clamp_max`` properties set
    initial clamp bounds.  The ``clamp_min`` / ``clamp_max`` input ports
    allow dynamic updates without triggering ``notify_node_updated``.
    Sending an empty array resets the clamp to None (unclamped).

    When the sum exceeds ``clamp_max``, the excess is dispatched on
    ``overflow``.  When the sum goes below ``clamp_min``, the deficit is
    dispatched on ``underflow``.
    """

    _REAL_NUMBER_TYPES = {
        DataType.Int8,
        DataType.Uint8,
        DataType.Int16,
        DataType.Uint16,
        DataType.Int32,
        DataType.Uint32,
        DataType.Int64,
        DataType.Uint64,
        DataType.Float32,
        DataType.Float64,
    }

    def __init__(self, name: str):
        super().__init__(name, "ValueAccumulator")

        value_type = PortValueType(DataType.Int32)

        input_in = StaticTypeInputPort("in", [value_type])
        input_in.subscribe(id(self), self._on_input)

        input_reset = StaticTypeInputPort("reset", [PortValueType(DataType.Any)])
        input_reset.subscribe(id(self), self._on_reset)

        input_clamp_min = StaticTypeInputPort("clamp_min", [value_type])
        input_clamp_min.subscribe(id(self), self._on_clamp_min)

        input_clamp_max = StaticTypeInputPort("clamp_max", [value_type])
        input_clamp_max.subscribe(id(self), self._on_clamp_max)

        output_value = StaticTypeOutputPort("value", [value_type])
        output_overflow = StaticTypeOutputPort("overflow", [value_type])
        output_underflow = StaticTypeOutputPort("underflow", [value_type])

        self._sum = 0
        self._value_type = value_type
        self._dtype = data_type_to_numpy_dtype(value_type.data_type)
        self._clamp_min: int | float | None = None
        self._clamp_max: int | float | None = None
        self._input_in = input_in
        self._input_clamp_min = input_clamp_min
        self._input_clamp_max = input_clamp_max
        self._output_value = output_value
        self._output_overflow = output_overflow
        self._output_underflow = output_underflow

        self.inputs[input_in.name] = input_in
        self.inputs[input_reset.name] = input_reset
        self.inputs[input_clamp_min.name] = input_clamp_min
        self.inputs[input_clamp_max.name] = input_clamp_max
        self.outputs[output_value.name] = output_value
        self.outputs[output_overflow.name] = output_overflow
        self.outputs[output_underflow.name] = output_underflow

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract
        value_type = self._value_type
        if "value_type" in properties:
            value_type_str = properties["value_type"]
            if not isinstance(value_type_str, str):
                raise ValueError("value_type must be a string")
            value_type = name_to_port_value_type(value_type_str)

        if value_type.data_type not in self._REAL_NUMBER_TYPES:
            raise ValueError("Invalid data_type. Must be real number type.")
        if value_type.shape != ():
            raise ValueError("Invalid shape. Must be scalar.")

        clamp_min = self._clamp_min
        if "initial_clamp_min" in properties:
            v = properties["initial_clamp_min"]
            if v == "" or v is None:
                clamp_min = None
            else:
                clamp_min = (
                    float(v)
                    if value_type.data_type in (DataType.Float32, DataType.Float64)
                    else int(v)
                )

        clamp_max = self._clamp_max
        if "initial_clamp_max" in properties:
            v = properties["initial_clamp_max"]
            if v == "" or v is None:
                clamp_max = None
            else:
                clamp_max = (
                    float(v)
                    if value_type.data_type in (DataType.Float32, DataType.Float64)
                    else int(v)
                )

        # 2. Prepare new ports
        new_input_in = self._input_in
        new_input_clamp_min = self._input_clamp_min
        new_input_clamp_max = self._input_clamp_max
        new_output_value = self._output_value
        new_output_overflow = self._output_overflow
        new_output_underflow = self._output_underflow
        if value_type != self._value_type:
            new_input_in = StaticTypeInputPort("in", [value_type])
            new_input_clamp_min = StaticTypeInputPort("clamp_min", [value_type])
            new_input_clamp_max = StaticTypeInputPort("clamp_max", [value_type])
            new_output_value = StaticTypeOutputPort("value", [value_type])
            new_output_overflow = StaticTypeOutputPort("overflow", [value_type])
            new_output_underflow = StaticTypeOutputPort("underflow", [value_type])

        # 3. Update
        if new_input_in is not self._input_in:
            replace_node_input_port(self, self._input_in, new_input_in, self._on_input)
            self._input_in = new_input_in

        if new_input_clamp_min is not self._input_clamp_min:
            replace_node_input_port(
                self, self._input_clamp_min, new_input_clamp_min, self._on_clamp_min
            )
            self._input_clamp_min = new_input_clamp_min

        if new_input_clamp_max is not self._input_clamp_max:
            replace_node_input_port(
                self, self._input_clamp_max, new_input_clamp_max, self._on_clamp_max
            )
            self._input_clamp_max = new_input_clamp_max

        if new_output_value is not self._output_value:
            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        if new_output_overflow is not self._output_overflow:
            replace_node_output_port(self, self._output_overflow, new_output_overflow)
            self._output_overflow = new_output_overflow

        if new_output_underflow is not self._output_underflow:
            replace_node_output_port(self, self._output_underflow, new_output_underflow)
            self._output_underflow = new_output_underflow

        if value_type != self._value_type:
            self._sum = 0

        self._value_type = value_type
        self._dtype = data_type_to_numpy_dtype(value_type.data_type)
        self._clamp_min = clamp_min
        self._clamp_max = clamp_max

        if self._clamp_max is not None and self._sum > self._clamp_max:
            self._sum = self._clamp_max
        if self._clamp_min is not None and self._sum < self._clamp_min:
            self._sum = self._clamp_min

        self.properties["value_type"] = value_type.name
        self.properties["initial_clamp_min"] = "" if clamp_min is None else clamp_min
        self.properties["initial_clamp_max"] = "" if clamp_max is None else clamp_max

        # 4. Notify
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_clamp_min(self, values: list[PortValue]):
        arr = values[0]
        if len(arr) == 0:
            self._clamp_min = None
        else:
            self._clamp_min = arr[-1].item()

    def _on_clamp_max(self, values: list[PortValue]):
        arr = values[0]
        if len(arr) == 0:
            self._clamp_max = None
        else:
            self._clamp_max = arr[-1].item()

    def _on_input(self, values: list[PortValue]):
        arr = values[0]
        raw_sum = self._sum + np.sum(arr).item()
        overflow = 0
        underflow = 0
        if self._clamp_max is not None and raw_sum > self._clamp_max:
            overflow = raw_sum - self._clamp_max
            raw_sum = self._clamp_max
        if self._clamp_min is not None and raw_sum < self._clamp_min:
            underflow = raw_sum - self._clamp_min
            raw_sum = self._clamp_min
        self._sum = raw_sum
        if overflow > 0:
            self._output_overflow.dispatch([np.array([overflow], dtype=self._dtype)])
        if underflow < 0:
            self._output_underflow.dispatch([np.array([underflow], dtype=self._dtype)])
        self._output_value.dispatch([np.array([self._sum], dtype=self._dtype)])

    def _on_reset(self, values: list[PortValue]):
        self._sum = 0
        self._output_value.dispatch([np.array([0], dtype=self._dtype)])
