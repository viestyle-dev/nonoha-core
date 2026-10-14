import numpy as np
import pytest

from nonoha_core.nodes.string_nodes import StringFormatNode
from nonoha_core.data_type import DataType, PortValueType


def test_string_format_node_basic():
    """Test basic string formatting with default format"""
    node = StringFormatNode("test")

    # Capture output
    output_values = []
    node._output_formatted.subscribe(999, lambda v: output_values.append(v))

    # Input: str, f32 - matching default in_types
    input_str = np.array(["label1"], dtype=np.dtypes.StringDType())  # type: ignore
    input_float = np.array([3.14159], dtype=np.float32)

    node._input_in.dispatch([input_str, input_float])

    assert len(output_values) == 1
    result = output_values[0][0]
    assert len(result) == 1
    assert result[0] == "record,label1,3.14"


def test_string_format_node_batch():
    """Test batch processing"""
    node = StringFormatNode("test")

    output_values = []
    node._output_formatted.subscribe(999, lambda v: output_values.append(v))

    # Batch of 3
    input_str = np.array(["a", "b", "c"], dtype=np.dtypes.StringDType())  # type: ignore
    input_float = np.array([1.0, 2.5, 3.333], dtype=np.float32)

    node._input_in.dispatch([input_str, input_float])

    assert len(output_values) == 1
    result = output_values[0][0]
    assert len(result) == 3
    assert result[0] == "record,a,1.00"
    assert result[1] == "record,b,2.50"
    assert result[2] == "record,c,3.33"


def test_string_format_node_set_format_str():
    """Test changing format_str property"""
    node = StringFormatNode("test")

    node.set_properties({"format_str": "value={}"})
    node.set_properties({"in_types": "f32"})

    output_values = []
    node._output_formatted.subscribe(999, lambda v: output_values.append(v))

    input_float = np.array([42.0], dtype=np.float32)
    node._input_in.dispatch([input_float])

    assert len(output_values) == 1
    result = output_values[0][0]
    assert result[0] == "value=42.0"


def test_string_format_node_set_in_types():
    """Test changing in_types property"""
    node = StringFormatNode("test")

    # Change to 3 integer inputs
    node.set_properties({"in_types": "i32, i32, i32"})
    node.set_properties({"format_str": "{}-{}-{}"})

    assert len(node._input_in.value_type_list) == 3
    assert all(t.data_type == DataType.Int32 for t in node._input_in.value_type_list)

    output_values = []
    node._output_formatted.subscribe(999, lambda v: output_values.append(v))

    node._input_in.dispatch([
        np.array([2024], dtype=np.int32),
        np.array([12], dtype=np.int32),
        np.array([25], dtype=np.int32),
    ])

    assert len(output_values) == 1
    result = output_values[0][0]
    assert result[0] == "2024-12-25"


def test_string_format_node_invalid_format():
    """Test that invalid format doesn't crash"""
    node = StringFormatNode("test")

    node.set_properties({"format_str": "{:.2f}"})  # Expects float, but...

    output_values = []
    node._output_formatted.subscribe(999, lambda v: output_values.append(v))

    # Send string which can't be formatted with {:.2f}
    input_str = np.array(["text"], dtype=np.dtypes.StringDType())  # type: ignore
    input_float = np.array([1.0], dtype=np.float32)

    # Should log warning but not crash
    node._input_in.dispatch([input_str, input_float])

    # No output due to format error
    assert len(output_values) == 0
