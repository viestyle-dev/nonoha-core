"""Trigonometric function nodes for angle and ratio calculations."""

import numpy as np

from nonoha_core.node import BaseNode, NodeDoc, replace_node_input_port, replace_node_output_port
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

# Supported data types for trigonometric functions
_TRIG_SUPPORTED_TYPES = {
    DataType.Float32,
    DataType.Float64,
    DataType.Complex64,
    DataType.Complex128,
}

# Supported data types for atan2 (real numbers only)
_ATAN2_SUPPORTED_TYPES = {
    DataType.Float32,
    DataType.Float64,
}


class SinNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise sine of angle in radians",
            category="Trigonometry",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    """
    Calculate sine of an angle.

    sin(θ) = opposite/hypotenuse = a/c

    Inputs:
        in: f32/f64/c64/c128 - Angle in radians

    Outputs:
        out: f32/f64/c64/c128 - Sine value (same type as input)

    Properties:
        in_type: Input/output data type (default: "f32")
    """

    def __init__(self, name: str):
        super().__init__(name, "Sin")

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
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type not in _TRIG_SUPPORTED_TYPES:
                raise ValueError(
                    f"Unsupported data type: {in_type.data_type}. "
                    f"Supported types: f32, f64, c64, c128"
                )

        # 2. Create new ports if type changed
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_out = StaticTypeOutputPort("out", [in_type])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(self, self._input_in, new_input_in, self._on_input_in)
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
        in_array = values[0]
        out = np.sin(in_array)
        self._output_out.dispatch([out])


class CosNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise cosine of angle in radians",
            category="Trigonometry",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    """
    Calculate cosine of an angle.

    cos(θ) = adjacent/hypotenuse = b/c

    Inputs:
        in: f32/f64/c64/c128 - Angle in radians

    Outputs:
        out: f32/f64/c64/c128 - Cosine value (same type as input)

    Properties:
        in_type: Input/output data type (default: "f32")
    """

    def __init__(self, name: str):
        super().__init__(name, "Cos")

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
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type not in _TRIG_SUPPORTED_TYPES:
                raise ValueError(
                    f"Unsupported data type: {in_type.data_type}. "
                    f"Supported types: f32, f64, c64, c128"
                )

        # 2. Create new ports if type changed
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_out = StaticTypeOutputPort("out", [in_type])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(self, self._input_in, new_input_in, self._on_input_in)
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
        in_array = values[0]
        out = np.cos(in_array)
        self._output_out.dispatch([out])


class TanNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise tangent of angle in radians",
            category="Trigonometry",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    """
    Calculate tangent of an angle.

    tan(θ) = opposite/adjacent = a/b = sin(θ)/cos(θ)

    Inputs:
        in: f32/f64/c64/c128 - Angle in radians

    Outputs:
        out: f32/f64/c64/c128 - Tangent value (same type as input)

    Properties:
        in_type: Input/output data type (default: "f32")
    """

    def __init__(self, name: str):
        super().__init__(name, "Tan")

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
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type not in _TRIG_SUPPORTED_TYPES:
                raise ValueError(
                    f"Unsupported data type: {in_type.data_type}. "
                    f"Supported types: f32, f64, c64, c128"
                )

        # 2. Create new ports if type changed
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_out = StaticTypeOutputPort("out", [in_type])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(self, self._input_in, new_input_in, self._on_input_in)
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
        in_array = values[0]
        out = np.tan(in_array)
        self._output_out.dispatch([out])


class AsinNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise inverse sine (arcsin), returns angle in radians",
            category="Trigonometry",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    """
    Calculate arcsine (inverse sine) - angle from ratio.

    asin(x) → θ

    Inputs:
        in: f32/f64/c64/c128 - Sine value

    Outputs:
        out: f32/f64/c64/c128 - Angle in radians (same type as input)

    Properties:
        in_type: Input/output data type (default: "f32")
    """

    def __init__(self, name: str):
        super().__init__(name, "Asin")

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
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type not in _TRIG_SUPPORTED_TYPES:
                raise ValueError(
                    f"Unsupported data type: {in_type.data_type}. "
                    f"Supported types: f32, f64, c64, c128"
                )

        # 2. Create new ports if type changed
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_out = StaticTypeOutputPort("out", [in_type])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(self, self._input_in, new_input_in, self._on_input_in)
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
        in_array = values[0]
        out = np.asin(in_array)
        self._output_out.dispatch([out])


class AcosNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise inverse cosine (arccos), returns angle in radians",
            category="Trigonometry",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    """
    Calculate arccosine (inverse cosine) - angle from ratio.

    acos(x) → θ

    Inputs:
        in: f32/f64/c64/c128 - Cosine value

    Outputs:
        out: f32/f64/c64/c128 - Angle in radians (same type as input)

    Properties:
        in_type: Input/output data type (default: "f32")
    """

    def __init__(self, name: str):
        super().__init__(name, "Acos")

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
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type not in _TRIG_SUPPORTED_TYPES:
                raise ValueError(
                    f"Unsupported data type: {in_type.data_type}. "
                    f"Supported types: f32, f64, c64, c128"
                )

        # 2. Create new ports if type changed
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_out = StaticTypeOutputPort("out", [in_type])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(self, self._input_in, new_input_in, self._on_input_in)
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
        in_array = values[0]
        out = np.acos(in_array)
        self._output_out.dispatch([out])


class AtanNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise inverse tangent (arctan), returns angle in radians",
            category="Trigonometry",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    """
    Calculate arctangent (inverse tangent) - angle from ratio.

    atan(x) → θ

    Inputs:
        in: f32/f64/c64/c128 - Tangent value

    Outputs:
        out: f32/f64/c64/c128 - Angle in radians (same type as input)

    Properties:
        in_type: Input/output data type (default: "f32")
    """

    def __init__(self, name: str):
        super().__init__(name, "Atan")

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
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type not in _TRIG_SUPPORTED_TYPES:
                raise ValueError(
                    f"Unsupported data type: {in_type.data_type}. "
                    f"Supported types: f32, f64, c64, c128"
                )

        # 2. Create new ports if type changed
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_out = StaticTypeOutputPort("out", [in_type])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(self, self._input_in, new_input_in, self._on_input_in)
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
        in_array = values[0]
        out = np.atan(in_array)
        self._output_out.dispatch([out])


class Atan2Node(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Element-wise 2-argument arctangent of y/x, returns angle in radians",
            category="Trigonometry",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    """
    Calculate 2-argument arctangent - angle from y and x coordinates.

    atan2(y, x) → θ (handles all 4 quadrants)

    This is useful for converting Cartesian coordinates to polar coordinates,
    or calculating angles when you have opposite (a/y) and adjacent (b/x) sides.

    Inputs:
        in: f32/f64 [y, x] - Y and X coordinates

    Outputs:
        out: f32/f64 - Angle in radians (same type as input)

    Properties:
        in_type: Input/output data type (default: "f32")
    """

    def __init__(self, name: str):
        super().__init__(name, "Atan2")

        in_type = PortValueType(DataType.Float32)

        input_in = StaticTypeInputPort(
            "in",
            [in_type, in_type],
            ["y", "x"],
        )
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
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type not in _ATAN2_SUPPORTED_TYPES:
                raise ValueError(
                    f"Unsupported data type: {in_type.data_type}. "
                    f"Supported types: f32, f64"
                )

        # 2. Create new ports if type changed
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort(
                "in",
                [in_type, in_type],
                ["y", "x"],
            )
            new_output_out = StaticTypeOutputPort("out", [in_type])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(self, self._input_in, new_input_in, self._on_input_in)
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
        y_array = values[0]
        x_array = values[1]
        out = np.atan2(y_array, x_array)
        self._output_out.dispatch([out])


class Deg2RadNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Convert angles from degrees to radians",
            category="Trigonometry",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    """
    Convert degrees to radians.

    radians = degrees x (π / 180)

    Inputs:
        in: f32/f64 - Angle in degrees

    Outputs:
        out: f32/f64 - Angle in radians (same type as input)

    Properties:
        in_type: Input/output data type (default: "f32")
    """

    def __init__(self, name: str):
        super().__init__(name, "Deg2Rad")

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
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type not in _ATAN2_SUPPORTED_TYPES:
                raise ValueError(
                    f"Unsupported data type: {in_type.data_type}. "
                    f"Supported types: f32, f64"
                )

        # 2. Create new ports if type changed
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_out = StaticTypeOutputPort("out", [in_type])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(self, self._input_in, new_input_in, self._on_input_in)
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
        in_array = values[0]
        out = np.deg2rad(in_array)
        self._output_out.dispatch([out])


class Rad2DegNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Convert angles from radians to degrees",
            category="Trigonometry",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    """
    Convert radians to degrees.

    degrees = radians x (180 / π)

    Inputs:
        in: f32/f64 - Angle in radians

    Outputs:
        out: f32/f64 - Angle in degrees (same type as input)

    Properties:
        in_type: Input/output data type (default: "f32")
    """

    def __init__(self, name: str):
        super().__init__(name, "Rad2Deg")

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
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type not in _ATAN2_SUPPORTED_TYPES:
                raise ValueError(
                    f"Unsupported data type: {in_type.data_type}. "
                    f"Supported types: f32, f64"
                )

        # 2. Create new ports if type changed
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_out = StaticTypeOutputPort("out", [in_type])

        # 3. Replace ports atomically if changed
        if new_input_in != self._input_in:
            replace_node_input_port(self, self._input_in, new_input_in, self._on_input_in)
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
        in_array = values[0]
        out = np.rad2deg(in_array)
        self._output_out.dispatch([out])
