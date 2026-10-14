import numpy as np
from nonoha_core.nodes.arithmetic_operation_nodes import (
    ReciprocalNode,
    NegativeNode,
)


def test_reciprocal_node_array_inputs():
    """Test ReciprocalNode with array inputs"""
    test_node = ReciprocalNode("test")

    # Test with array values
    input_port = test_node.inputs["values"]

    # Send array value
    test_array = np.array([2.0, 4.0, 10.0], dtype=np.float32)
    input_port.dispatch([test_array])

    output_values = test_node.outputs["values"]

    # Check output
    assert output_values.current_values is not None
    result_values = output_values.current_values
    assert len(result_values) == 1
    expected = np.array([0.5, 0.25, 0.1], dtype=np.float32)
    np.testing.assert_array_almost_equal(result_values[0], expected)


def test_reciprocal_node_multiple_arrays():
    """Test ReciprocalNode with multiple array inputs"""
    test_node = ReciprocalNode("test")

    # Configure for multiple inputs
    test_node.set_properties({"in_types": "f32,f32"})

    input_port = test_node.inputs["values"]

    # Send multiple array values
    test_arrays = [
        np.array([2.0, 4.0], dtype=np.float32),
        np.array([5.0, 10.0], dtype=np.float32),
    ]
    input_port.dispatch(test_arrays)

    output_values = test_node.outputs["values"]

    # Check outputs - each array should be processed separately
    assert output_values.current_values is not None
    result_values = output_values.current_values

    assert len(result_values) == 2
    np.testing.assert_array_almost_equal(
        result_values[0], np.array([0.5, 0.25], dtype=np.float32)
    )
    np.testing.assert_array_almost_equal(
        result_values[1], np.array([0.2, 0.1], dtype=np.float32)
    )


def test_negative_node():
    """Test NegativeNode"""
    test_node = NegativeNode("test")

    input_port = test_node.inputs["values"]

    # Send array value
    test_array = np.array([1.0, -2.0, 3.0], dtype=np.float32)
    input_port.dispatch([test_array])

    output_values = test_node.outputs["values"]

    # Check output
    assert output_values.current_values is not None
    result_values = output_values.current_values
    assert len(result_values) == 1
    expected = np.array([-1.0, 2.0, -3.0], dtype=np.float32)
    np.testing.assert_array_almost_equal(result_values[0], expected)


def test_negative_node_multiple_arrays():
    """Test NegativeNode with multiple array inputs"""
    test_node = NegativeNode("test")

    # Configure for multiple inputs
    test_node.set_properties({"in_types": "i32,i32"})

    input_port = test_node.inputs["values"]

    # Send multiple array values
    test_arrays = [
        np.array([1.0, -2.0], dtype=np.int32),
        np.array([-5.0, 10.0], dtype=np.int32),
    ]
    input_port.dispatch(test_arrays)

    output_values = test_node.outputs["values"]

    # Check outputs - each array should be processed separately
    assert output_values.current_values is not None
    result_values = output_values.current_values

    assert len(result_values) == 2
    np.testing.assert_array_almost_equal(
        result_values[0], np.array([-1.0, 2.0], dtype=np.int32)
    )
    np.testing.assert_array_almost_equal(
        result_values[1], np.array([5.0, -10.0], dtype=np.int32)
    )
