from nonoha_core.nodes.array_manipulation_nodes import (
    ColumnUnstackNode,
    ReshapeNode,
    StackNode,
    UnstackNode,
)

import numpy as np
import time


def test_column_split_node():
    node = ColumnUnstackNode("test")
    node.set_properties({"in_type": "f32[2]"})

    assert node.inputs["in"]
    assert node.outputs["out"]

    node.inputs["in"].dispatch([np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)])

    test_out = node.outputs["out"].current_values
    assert test_out is not None

    assert np.array_equal(test_out[0], np.array([1.0, 3.0], dtype=np.float32))
    assert np.array_equal(test_out[1], np.array([2.0, 4.0], dtype=np.float32))

    node.set_properties({"in_type": "f32[2x3]"})
    node.inputs["in"].dispatch(
        [
            np.array(
                [
                    [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
                    [[7.0, 8.0, 9.0], [10.0, 11.0, 12.0]],
                ],
                dtype=np.float32,
            )
        ]
    )


def test_stack_node():
    node = StackNode("test")


def test_unstack_node():
    node = UnstackNode("test")

    node.set_properties(
        {
            "in_type": "f32[2]",
            "axis": 1,
        }
    )

    input_in = node.inputs["in"]
    assert input_in.value_type_list[0].name == "f32[2]"

    output_out = node.outputs["out"]
    assert output_out.value_type_list[0].name == "f32"
    assert output_out.value_type_list[1].name == "f32"

    # start_time = time.perf_counter()

    input_in.dispatch([np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)])

    # end_time = time.perf_counter()
    # print(f"Dispatch time: {end_time - start_time:.6f} seconds")

    test_out = output_out.current_values
    assert test_out is not None
    assert isinstance(test_out, list)
    assert len(test_out) == 2
    assert np.array_equal(test_out[0], np.array([1.0, 3.0], dtype=np.float32))
    assert np.array_equal(test_out[1], np.array([2.0, 4.0], dtype=np.float32))

    # ---
    node.set_properties(
        {
            "in_type": "f32[3x4]",
            "axis": 2,
        }
    )
    input_in = node.inputs["in"]
    output_out = node.outputs["out"]
    assert input_in.value_type_list[0].name == "f32[3x4]"
    assert len(output_out.value_type_list) == 4
    assert output_out.value_type_list[0].name == "f32[3]"
    assert output_out.value_type_list[1].name == "f32[3]"
    assert output_out.value_type_list[2].name == "f32[3]"
    assert output_out.value_type_list[3].name == "f32[3]"

    # start_time = time.perf_counter()

    input_in.dispatch(
        [np.arange(12, dtype=np.float32).reshape(1, 3, 4)]  # Reshape to 3x4 array
    )

    # end_time = time.perf_counter()
    # print(f"Dispatch time: {end_time - start_time:.6f} seconds")

    test_out = output_out.current_values
    assert test_out is not None
    assert isinstance(test_out, list)
    assert len(test_out) == 4
    # print(test_out)
    assert np.array_equal(test_out[0], np.array([[0.0, 4.0, 8.0]], dtype=np.float32))
    assert np.array_equal(test_out[1], np.array([[1.0, 5.0, 9.0]], dtype=np.float32))
    assert np.array_equal(test_out[2], np.array([[2.0, 6.0, 10.0]], dtype=np.float32))
    assert np.array_equal(test_out[3], np.array([[3.0, 7.0, 11.0]], dtype=np.float32))
    # ---


def test_reshape_node_default():
    """Default config f32[128] -> [64x2]"""
    node = ReshapeNode("test")

    assert node.inputs["in"].value_type_list[0].name == "f32[128]"
    assert node.outputs["out"].value_type_list[0].name == "f32[64x2]"

    data = np.arange(128, dtype=np.float32).reshape(1, 128)
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    assert out[0].shape == (1, 64, 2)
    assert np.array_equal(out[0][0, 0], np.array([0.0, 1.0], dtype=np.float32))
    assert np.array_equal(out[0][0, 63], np.array([126.0, 127.0], dtype=np.float32))


def test_reshape_node_fixed_shape():
    """Fixed dimensions f32[6] -> [2x3]"""
    node = ReshapeNode("test")
    node.set_properties({"in_type": "f32[6]", "out_type_shape": "[2x3]"})

    assert node.inputs["in"].value_type_list[0].name == "f32[6]"
    assert node.outputs["out"].value_type_list[0].name == "f32[2x3]"

    data = np.arange(6, dtype=np.float32).reshape(1, 6)
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    # Fixed dims: batch=-1 -> (1, 2, 3)
    assert out[0].shape == (1, 2, 3)
    assert np.array_equal(
        out[0][0], np.array([[0, 1, 2], [3, 4, 5]], dtype=np.float32)
    )


def test_reshape_node_variable_dim():
    """Variable dimension f32[128] -> [Nx2], batch=1, N=64"""
    node = ReshapeNode("test")
    node.set_properties({"in_type": "f32[128]", "out_type_shape": "[Nx2]"})

    assert node.outputs["out"].value_type_list[0].name == "f32[?x2]"

    data = np.arange(128, dtype=np.float32).reshape(1, 128)
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    # Variable dim: batch=1, N resolved -> (1, 64, 2)
    assert out[0].shape == (1, 64, 2)
    assert np.array_equal(out[0][0, 0], np.array([0.0, 1.0], dtype=np.float32))


def test_reshape_node_rechunk():
    """Rechunk: u8[10] -> [2], output shape (B*5, 2)"""
    node = ReshapeNode("test")
    node.set_properties({"in_type": "u8[10]", "out_type_shape": "[2]"})

    assert node.inputs["in"].value_type_list[0].name == "u8[10]"
    assert node.outputs["out"].value_type_list[0].name == "u8[2]"

    data = np.arange(30, dtype=np.uint8).reshape(3, 10)
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    # (3, 10) -> (-1, 2) -> (15, 2)
    assert out[0].shape == (15, 2)
    assert np.array_equal(out[0][0], np.array([0, 1], dtype=np.uint8))
    assert np.array_equal(out[0][14], np.array([28, 29], dtype=np.uint8))


def test_reshape_node_scalar_to_scalar():
    """Scalar input/output f32 -> ()"""
    node = ReshapeNode("test")
    node.set_properties({"in_type": "f32", "out_type_shape": ""})

    assert node.inputs["in"].value_type_list[0].name == "f32"
    assert node.outputs["out"].value_type_list[0].name == "f32"

    data = np.array([5.0], dtype=np.float32)
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    assert out[0].shape == (1,)
    assert out[0][0] == 5.0


def test_reshape_node_vector_to_scalar_flatten():
    """Vector to scalar = flatten: f32[4] -> ()"""
    node = ReshapeNode("test")
    node.set_properties({"in_type": "f32[4]", "out_type_shape": ""})

    data = np.arange(8, dtype=np.float32).reshape(2, 4)
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    # Flatten: (2, 4) -> (8,)
    assert out[0].shape == (8,)
    assert np.array_equal(out[0], np.arange(8, dtype=np.float32))


def test_reshape_node_scalar_to_vector():
    """Scalar to 1-element vector: f32 -> [1]"""
    node = ReshapeNode("test")
    node.set_properties({"in_type": "f32", "out_type_shape": "[1]"})

    data = np.array([5.0], dtype=np.float32)
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    assert out[0].shape == (1, 1)
    assert out[0][0, 0] == 5.0
