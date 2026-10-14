from nonoha_core.nodes.mathematical_function_nodes import SumNode, MinNode, MaxNode, InterpolateNode

import numpy as np

from nonoha_core.data_type import DataType


def test_sum_node():
    node = SumNode("test")
    node.set_properties(
        {
            "in_type": "f32",
            "axis": 0,
        }
    )

    input_value = node.inputs["value"]
    output_value = node.outputs["value"]

    assert output_value.value_type_list[0].data_type == DataType.Float32
    assert output_value.value_type_list[0].shape == tuple()

    input_value.dispatch([np.arange(10)])

    assert output_value.current_values is not None
    result = output_value.current_values[0]

    assert type(result) == np.ndarray
    assert result.shape == (1,)
    assert result[0] == np.arange(10).sum()

    # print(f"result: {type(result)}")

    # ---

    node.set_properties(
        {
            "in_type": "f32[2]",
            "axis": 0,
        }
    )
    input_value = node.inputs["value"]
    output_value = node.outputs["value"]

    assert output_value.value_type_list[0].data_type == DataType.Float32
    assert output_value.value_type_list[0].shape == (2,)

    input_value.dispatch([np.arange(10).reshape(5, 2)])
    assert output_value.current_values is not None
    result = output_value.current_values[0]
    assert type(result) == np.ndarray
    assert result.shape == (1, 2)

    # print(f"{result=}")


def test_min_node_axis1():
    """Default: axis=1, in_type=f32[2] — min along data axis"""
    node = MinNode("test")

    input_in = node.inputs["in"]
    output_out = node.outputs["out"]

    assert output_out.value_type_list[0].data_type == DataType.Float32
    assert output_out.value_type_list[0].shape == ()

    # batch=3, each with 2 elements -> min of each row
    data = np.array([[3.0, 1.0], [5.0, 2.0], [4.0, 7.0]])  # shape (3, 2)
    input_in.dispatch([data])

    assert output_out.current_values is not None
    result = output_out.current_values[0]
    assert result.shape == (3,)
    np.testing.assert_array_equal(result, [1.0, 2.0, 4.0])


def test_min_node_axis0():
    """axis=0 — min along batch axis, expand_dims restores batch dim"""
    node = MinNode("test")
    node.set_properties({"in_type": "f32", "axis": 0})

    input_in = node.inputs["in"]
    output_out = node.outputs["out"]

    assert output_out.value_type_list[0].shape == ()

    data = np.array([5.0, 2.0, 8.0, 1.0])  # shape (4,) = 4 scalars in batch
    input_in.dispatch([data])

    assert output_out.current_values is not None
    result = output_out.current_values[0]
    assert result.shape == (1,)  # batch dim restored by expand_dims
    assert result[0] == 1.0


def test_min_node_axis_none():
    """axis=None — min of all elements, expand_dims restores batch dim"""
    node = MinNode("test")
    node.set_properties({"in_type": "f32[3]", "axis": ""})

    input_in = node.inputs["in"]
    output_out = node.outputs["out"]

    assert output_out.value_type_list[0].shape == ()

    data = np.array([[9.0, 3.0, 7.0], [2.0, 5.0, 1.0]])  # shape (2, 3)
    input_in.dispatch([data])

    assert output_out.current_values is not None
    result = output_out.current_values[0]
    assert result.shape == (1,)  # batch dim restored by expand_dims
    assert result[0] == 1.0


def test_min_node_set_properties_changes_ports():
    """set_properties should replace ports when in_type changes"""
    node = MinNode("test")

    old_input = node.inputs["in"]
    old_output = node.outputs["out"]

    node.set_properties({"in_type": "f64[4]"})

    new_input = node.inputs["in"]
    new_output = node.outputs["out"]

    # Ports should be replaced
    assert new_input is not old_input
    assert new_output is not old_output
    assert new_input.value_type_list[0].data_type == DataType.Float64
    assert new_input.value_type_list[0].shape == (4,)


def test_max_node_axis1():
    """Default: axis=1, in_type=f32[2] — max along data axis"""
    node = MaxNode("test")

    input_in = node.inputs["in"]
    output_out = node.outputs["out"]

    assert output_out.value_type_list[0].data_type == DataType.Float32
    assert output_out.value_type_list[0].shape == ()

    # batch=3, each with 2 elements -> max of each row
    data = np.array([[3.0, 1.0], [5.0, 2.0], [4.0, 7.0]])  # shape (3, 2)
    input_in.dispatch([data])

    assert output_out.current_values is not None
    result = output_out.current_values[0]
    assert result.shape == (3,)
    np.testing.assert_array_equal(result, [3.0, 5.0, 7.0])


def test_max_node_axis0():
    """axis=0 — max along batch axis, expand_dims restores batch dim"""
    node = MaxNode("test")
    node.set_properties({"in_type": "f32", "axis": 0})

    input_in = node.inputs["in"]
    output_out = node.outputs["out"]

    assert output_out.value_type_list[0].shape == ()

    data = np.array([5.0, 2.0, 8.0, 1.0])  # shape (4,) = 4 scalars in batch
    input_in.dispatch([data])

    assert output_out.current_values is not None
    result = output_out.current_values[0]
    assert result.shape == (1,)  # batch dim restored by expand_dims
    assert result[0] == 8.0


def test_max_node_axis_none():
    """axis=None — max of all elements, expand_dims restores batch dim"""
    node = MaxNode("test")
    node.set_properties({"in_type": "f32[3]", "axis": ""})

    input_in = node.inputs["in"]
    output_out = node.outputs["out"]

    assert output_out.value_type_list[0].shape == ()

    data = np.array([[9.0, 3.0, 7.0], [2.0, 5.0, 1.0]])  # shape (2, 3)
    input_in.dispatch([data])

    assert output_out.current_values is not None
    result = output_out.current_values[0]
    assert result.shape == (1,)  # batch dim restored by expand_dims
    assert result[0] == 9.0


def test_max_node_set_properties_changes_ports():
    """set_properties should replace ports when in_type changes"""
    node = MaxNode("test")

    old_input = node.inputs["in"]
    old_output = node.outputs["out"]

    node.set_properties({"in_type": "f64[4]"})

    new_input = node.inputs["in"]
    new_output = node.outputs["out"]

    # Ports should be replaced
    assert new_input is not old_input
    assert new_output is not old_output
    assert new_input.value_type_list[0].data_type == DataType.Float64
    assert new_input.value_type_list[0].shape == (4,)


def test_interpolate_node():
    node = InterpolateNode("test")

    # Test default configuration (f32, 2 points)
    input_in = node.inputs["in"]
    output_y = node.outputs["y"]

    # Check initial port types
    assert len(input_in.value_type_list) == 3
    assert input_in.value_type_list[0].data_type == DataType.Float32
    assert input_in.value_type_list[0].shape == ()  # x: scalar
    assert input_in.value_type_list[1].shape == (2,)  # xp: 2 points
    assert input_in.value_type_list[2].shape == (2,)  # fp: 2 points

    # Test basic interpolation: remap -1~1 to 0~1
    x = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    xp = np.array([[-1.0, 1.0]])  # input range
    fp = np.array([[0.0, 1.0]])  # output range

    input_in.dispatch([x, xp, fp])

    assert output_y.current_values is not None
    result = output_y.current_values[0]

    expected = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    assert np.allclose(result, expected)


def test_interpolate_node_complex():
    node = InterpolateNode("test")

    # Change to complex64
    node.set_properties({"data_type": "c64"})

    input_in = node.inputs["in"]
    output_y = node.outputs["y"]

    # Test complex interpolation
    x = np.array([1.5, 4.0])
    xp = np.array([[2.0, 3.0, 5.0]])  # 3 points
    fp = np.array([[1.0j, 0.0, 2.0 + 3.0j]])

    # Update n_points to 3
    node.set_properties({"n_points": 3})
    input_in = node.inputs["in"]

    input_in.dispatch([x, xp, fp])

    assert output_y.current_values is not None

    result = output_y.current_values[0]
    expected = np.array([0.0 + 1.0j, 1.0 + 1.5j])
    assert np.allclose(result, expected)
