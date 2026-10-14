from nonoha_core.nodes.indexing_nodes import ExtractNode

import numpy as np

def test_extract_node():
    test_node = ExtractNode("test")

    test_node.set_properties(
        {"x_type": "f32[2]", "mask_shape": "[2]", "axis": 1}
    )

    test_node.inputs["in"].dispatch([
        np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        np.array([[True, False]], dtype=np.bool_),
    ])

    result_values = test_node.outputs["out"].current_values
    assert result_values is not None
    assert np.array_equal(result_values[0], np.array([[1.0], [3.0]], dtype=np.float32))