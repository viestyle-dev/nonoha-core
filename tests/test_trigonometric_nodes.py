"""Tests for trigonometric function nodes."""

import numpy as np

from nonoha_core.data_type import DataType
from nonoha_core.nodes.trigonometric_nodes import (
    SinNode,
    CosNode,
    TanNode,
    AsinNode,
    AcosNode,
    AtanNode,
    Atan2Node,
    Deg2RadNode,
    Rad2DegNode,
)


class TestSinNode:
    def test_sin(self):
        node = SinNode("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float32
        assert output_out.value_type_list[0].data_type == DataType.Float32

        # sin(0) = 0, sin(π/2) = 1, sin(π) = 0
        angles = np.array([0, np.pi / 2, np.pi], dtype=np.float32)
        input_in.dispatch([angles])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([0, 1, 0], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-6)

    def test_sin_complex(self):
        node = SinNode("test")
        node.set_properties({"in_type": "c64"})

        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Complex64
        assert output_out.value_type_list[0].data_type == DataType.Complex64

        # sin(1+2j) ≈ 3.1658 + 1.9596j
        angles = np.array([1 + 2j], dtype=np.complex64)
        input_in.dispatch([angles])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.sin(angles)
        assert np.allclose(result, expected, atol=1e-5)


class TestCosNode:
    def test_cos(self):
        node = CosNode("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float32
        assert output_out.value_type_list[0].data_type == DataType.Float32

        # cos(0) = 1, cos(π/2) = 0, cos(π) = -1
        angles = np.array([0, np.pi / 2, np.pi], dtype=np.float32)
        input_in.dispatch([angles])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([1, 0, -1], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-6)

    def test_cos_complex(self):
        node = CosNode("test")
        node.set_properties({"in_type": "c64"})

        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Complex64
        assert output_out.value_type_list[0].data_type == DataType.Complex64

        # cos(1+2j) ≈ 2.0327 - 3.0519j
        angles = np.array([1 + 2j], dtype=np.complex64)
        input_in.dispatch([angles])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.cos(angles)
        assert np.allclose(result, expected, atol=1e-5)


class TestTanNode:
    def test_tan(self):
        node = TanNode("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float32
        assert output_out.value_type_list[0].data_type == DataType.Float32

        # tan(0) = 0, tan(π/4) = 1
        angles = np.array([0, np.pi / 4], dtype=np.float32)
        input_in.dispatch([angles])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([0, 1], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-6)

    def test_tan_complex(self):
        node = TanNode("test")
        node.set_properties({"in_type": "c64"})

        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Complex64
        assert output_out.value_type_list[0].data_type == DataType.Complex64

        # tan(1+2j) ≈ 0.0338 + 1.0148j
        angles = np.array([1 + 2j], dtype=np.complex64)
        input_in.dispatch([angles])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.tan(angles)
        assert np.allclose(result, expected, atol=1e-5)


class TestAsinNode:
    def test_asin(self):
        node = AsinNode("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float32
        assert output_out.value_type_list[0].data_type == DataType.Float32

        # asin(0) = 0, asin(1) = π/2, asin(-1) = -π/2
        values = np.array([0, 1, -1], dtype=np.float32)
        input_in.dispatch([values])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([0, np.pi / 2, -np.pi / 2], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-6)

    def test_asin_complex(self):
        node = AsinNode("test")
        node.set_properties({"in_type": "c64"})

        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Complex64
        assert output_out.value_type_list[0].data_type == DataType.Complex64

        # asin works on complex values including outside [-1, 1]
        values = np.array([1 + 2j], dtype=np.complex64)
        input_in.dispatch([values])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.arcsin(values)
        assert np.allclose(result, expected, atol=1e-5)


class TestAcosNode:
    def test_acos(self):
        node = AcosNode("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float32
        assert output_out.value_type_list[0].data_type == DataType.Float32

        # acos(1) = 0, acos(0) = π/2, acos(-1) = π
        values = np.array([1, 0, -1], dtype=np.float32)
        input_in.dispatch([values])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([0, np.pi / 2, np.pi], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-6)

    def test_acos_complex(self):
        node = AcosNode("test")
        node.set_properties({"in_type": "c64"})

        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Complex64
        assert output_out.value_type_list[0].data_type == DataType.Complex64

        # acos works on complex values including outside [-1, 1]
        values = np.array([1 + 2j], dtype=np.complex64)
        input_in.dispatch([values])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.arccos(values)
        assert np.allclose(result, expected, atol=1e-5)


class TestAtanNode:
    def test_atan(self):
        node = AtanNode("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float32
        assert output_out.value_type_list[0].data_type == DataType.Float32

        # atan(0) = 0, atan(1) = π/4, atan(-1) = -π/4
        values = np.array([0, 1, -1], dtype=np.float32)
        input_in.dispatch([values])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([0, np.pi / 4, -np.pi / 4], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-6)

    def test_atan_complex(self):
        node = AtanNode("test")
        node.set_properties({"in_type": "c64"})

        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Complex64
        assert output_out.value_type_list[0].data_type == DataType.Complex64

        values = np.array([1 + 2j], dtype=np.complex64)
        input_in.dispatch([values])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.arctan(values)
        assert np.allclose(result, expected, atol=1e-5)

    def test_atan_large_values(self):
        """atan should handle large values approaching ±π/2."""
        node = AtanNode("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        values = np.array([1000, -1000], dtype=np.float32)
        input_in.dispatch([values])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        # Should approach ±π/2
        assert np.allclose(result, [np.pi / 2, -np.pi / 2], atol=1e-3)


class TestAtan2Node:
    def test_atan2(self):
        node = Atan2Node("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float32
        assert output_out.value_type_list[0].data_type == DataType.Float32

        # atan2(1, 1) = π/4, atan2(1, -1) = 3π/4, atan2(-1, -1) = -3π/4
        y_values = np.array([1, 1, -1], dtype=np.float32)
        x_values = np.array([1, -1, -1], dtype=np.float32)
        input_in.dispatch([y_values, x_values])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([np.pi / 4, 3 * np.pi / 4, -3 * np.pi / 4], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-6)

    def test_atan2_float64(self):
        node = Atan2Node("test")
        node.set_properties({"in_type": "f64"})

        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float64
        assert output_out.value_type_list[0].data_type == DataType.Float64

        y_values = np.array([1, 1, -1], dtype=np.float64)
        x_values = np.array([1, -1, -1], dtype=np.float64)
        input_in.dispatch([y_values, x_values])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([np.pi / 4, 3 * np.pi / 4, -3 * np.pi / 4], dtype=np.float64)
        assert np.allclose(result, expected, atol=1e-10)

    def test_atan2_quadrants(self):
        """Test all four quadrants."""
        node = Atan2Node("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        # Q1: (1,1), Q2: (1,-1), Q3: (-1,-1), Q4: (-1,1)
        y_values = np.array([1, 1, -1, -1], dtype=np.float32)
        x_values = np.array([1, -1, -1, 1], dtype=np.float32)
        input_in.dispatch([y_values, x_values])

        assert output_out.current_values is not None
        result = output_out.current_values[0]

        # Q1: π/4, Q2: 3π/4, Q3: -3π/4, Q4: -π/4
        expected = np.array(
            [np.pi / 4, 3 * np.pi / 4, -3 * np.pi / 4, -np.pi / 4], dtype=np.float32
        )
        assert np.allclose(result, expected, atol=1e-6)

    def test_atan2_axes(self):
        """Test points on axes."""
        node = Atan2Node("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        # (0,1)=0, (1,0)=π/2, (0,-1)=π, (-1,0)=-π/2
        y_values = np.array([0, 1, 0, -1], dtype=np.float32)
        x_values = np.array([1, 0, -1, 0], dtype=np.float32)
        input_in.dispatch([y_values, x_values])

        assert output_out.current_values is not None
        result = output_out.current_values[0]

        expected = np.array([0, np.pi / 2, np.pi, -np.pi / 2], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-6)


class TestDeg2RadNode:
    def test_deg2rad(self):
        node = Deg2RadNode("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float32
        assert output_out.value_type_list[0].data_type == DataType.Float32

        # 0° = 0, 90° = π/2, 180° = π, 360° = 2π
        degrees = np.array([0, 90, 180, 360], dtype=np.float32)
        input_in.dispatch([degrees])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([0, np.pi / 2, np.pi, 2 * np.pi], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-6)

    def test_deg2rad_float64(self):
        node = Deg2RadNode("test")
        node.set_properties({"in_type": "f64"})

        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float64
        assert output_out.value_type_list[0].data_type == DataType.Float64

        degrees = np.array([0, 90, 180, 360], dtype=np.float64)
        input_in.dispatch([degrees])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([0, np.pi / 2, np.pi, 2 * np.pi], dtype=np.float64)
        assert np.allclose(result, expected, atol=1e-10)

    def test_deg2rad_negative(self):
        """Test negative degrees."""
        node = Deg2RadNode("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        degrees = np.array([-90, -180, -360], dtype=np.float32)
        input_in.dispatch([degrees])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([-np.pi / 2, -np.pi, -2 * np.pi], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-6)


class TestRad2DegNode:
    def test_rad2deg(self):
        node = Rad2DegNode("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float32
        assert output_out.value_type_list[0].data_type == DataType.Float32

        # 0 = 0°, π/2 = 90°, π = 180°, 2π = 360°
        radians = np.array([0, np.pi / 2, np.pi, 2 * np.pi], dtype=np.float32)
        input_in.dispatch([radians])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([0, 90, 180, 360], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-4)

    def test_rad2deg_float64(self):
        node = Rad2DegNode("test")
        node.set_properties({"in_type": "f64"})

        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        assert input_in.value_type_list[0].data_type == DataType.Float64
        assert output_out.value_type_list[0].data_type == DataType.Float64

        radians = np.array([0, np.pi / 2, np.pi, 2 * np.pi], dtype=np.float64)
        input_in.dispatch([radians])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([0, 90, 180, 360], dtype=np.float64)
        assert np.allclose(result, expected, atol=1e-10)

    def test_rad2deg_negative(self):
        """Test negative radians."""
        node = Rad2DegNode("test")
        input_in = node.inputs["in"]
        output_out = node.outputs["out"]

        radians = np.array([-np.pi / 2, -np.pi, -2 * np.pi], dtype=np.float32)
        input_in.dispatch([radians])

        assert output_out.current_values is not None
        result = output_out.current_values[0]
        expected = np.array([-90, -180, -360], dtype=np.float32)
        assert np.allclose(result, expected, atol=1e-4)
