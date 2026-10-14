from nonoha_core.nodes.statistics_nodes import IncrementalMeanNode, MeanNode

import numpy as np

from nonoha_core.data_type import DataType


def test_incremental_mean_node():
    node = IncrementalMeanNode("test")

    node.set_properties({"shape": ""})
    input_in = node.inputs["in"]
    output_out = node.outputs["out"]

    assert input_in.value_type_list[0].shape == tuple()
    assert input_in.value_type_list[0].data_type == DataType.Float32
    assert output_out.value_type_list[0].shape == tuple()
    assert output_out.value_type_list[0].data_type == DataType.Float32

    input_in.dispatch([np.array([1.0, 2.0], dtype=np.float32)])

    assert output_out.current_values is not None
    assert len(output_out.current_values) == 1
    result = output_out.current_values[0]

    assert np.allclose(result, np.array([1.5], dtype=np.float32))

    input_in.dispatch([np.array([3.0, 4.0], dtype=np.float32)])
    assert output_out.current_values is not None
    assert len(output_out.current_values) == 1
    result = output_out.current_values[0]

    # print(f"result: {result.dtype}")
    assert np.allclose(result, np.array([2.5], dtype=np.float32))


def test_mean_node():
    # result = np.mean(np.arange(6))
    # print(f"Mean result: {result}, {result.shape}")  # shape ()

    # result = np.mean(np.arange(6).reshape(3, 2), axis=0)
    # print(f"Mean result: {result}, {result.shape}")  # shape=(2,)

    # result = np.mean(np.arange(6).reshape(3, 2), axis=1)
    # print(f"Mean result: {result}, {result.shape}")  # shape=(3,)

    node = MeanNode("test")
    node.set_properties({"in_type": "f32", "axis": 0})
    input_in = node.inputs["in"]
    output_out = node.outputs["out"]

    assert input_in.value_type_list[0].shape == ()
    assert output_out.value_type_list[0].shape == ()

    input_in.dispatch([np.arange(6, dtype=np.float32)])
    assert output_out.current_values is not None
    result = output_out.current_values[0]
    assert np.allclose(result, np.array([2.5], dtype=np.float32))

    # ---

    node.set_properties({"in_type": "f32[2]", "axis": 0})
    input_in = node.inputs["in"]
    output_out = node.outputs["out"]
    assert input_in.value_type_list[0].shape == (2,)
    assert output_out.value_type_list[0].shape == (2,)

    input_in.dispatch([np.arange(6, dtype=np.float32).reshape(3, 2)])
    assert output_out.current_values is not None
    result = output_out.current_values[0]
    expected = np.mean(np.arange(6, dtype=np.float32).reshape(3, 2), axis=0)
    assert np.allclose(result, expected)

    # ---

    node.set_properties({"in_type": "f32[2]", "axis": 1})
    input_in = node.inputs["in"]
    output_out = node.outputs["out"]
    assert input_in.value_type_list[0].shape == (2,)
    assert output_out.value_type_list[0].shape == ()

    input_in.dispatch([np.arange(6, dtype=np.float32).reshape(3, 2)])
    assert output_out.current_values is not None
    result = output_out.current_values[0]
    expected = np.mean(np.arange(6, dtype=np.float32).reshape(3, 2), axis=1)
    assert np.allclose(result, expected)
