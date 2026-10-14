import pytest
from nonoha_core.nodes.value_nodes import (
    RealNumberValueNode, ComplexNumberValueNode,
    StringValueNode, ArrayValueNode, EmptyValueNode, FullLikeNode, EnumerateNode,
    ValueAccumulatorNode,
)

import numpy as np

def test_string_value_node():
    node = StringValueNode("test")
    node._do_activate()

    node.set_properties({"default": "test"})

    output_value = node.outputs["value"]
    current_values = output_value.current_values

    assert current_values is not None
    assert isinstance(current_values[0], np.ndarray)
    assert current_values[0].dtype == np.dtypes.StringDType() # type: ignore
    assert current_values[0] == "test"
    

def test_array_value_node():
    node = ArrayValueNode("test")
    node._do_activate()

    # Check default output (f32[3] with [0.0, 0.0, 0.0])
    output_value = node.outputs["value"]
    current_values = output_value.current_values

    assert current_values is not None
    assert isinstance(current_values[0], np.ndarray)
    assert current_values[0].shape == (1, 3)  # Batch size 1, shape (3,)
    assert current_values[0].dtype == np.float32
    assert np.array_equal(current_values[0], np.array([[0.0, 0.0, 0.0]], dtype=np.float32))


def test_array_value_node_set_default():
    node = ArrayValueNode("test")
    node._do_activate()

    # Set new default value
    node.set_properties({"default": "[1.0, 2.0, 3.0]"})

    output_value = node.outputs["value"]
    current_values = output_value.current_values

    assert current_values is not None
    assert current_values[0].shape == (1, 3)
    assert np.array_equal(current_values[0], np.array([[1.0, 2.0, 3.0]], dtype=np.float32))


def test_array_value_node_change_shape():
    node = ArrayValueNode("test")
    node._do_activate()

    # Change to 2D array: f32[2x3]
    node.set_properties({
        "value_type": "f32[2x3]",
        "default": "[1, 2, 3, 4, 5, 6]"
    })

    output_value = node.outputs["value"]
    current_values = output_value.current_values

    assert current_values is not None
    assert current_values[0].shape == (1, 2, 3)  # Batch 1, shape (2, 3)
    expected = np.array([[[1, 2, 3], [4, 5, 6]]], dtype=np.float32)
    assert np.array_equal(current_values[0], expected)


def test_array_value_node_dtype():
    """Test that ArrayValueNode uses correct numpy dtype based on DataType."""
    node = ArrayValueNode("test")
    node._do_activate()

    # Test uint8
    node.set_properties({
        "value_type": "u8[3]",
        "default": "[255, 128, 0]"
    })
    output = node.outputs["value"]
    assert output.current_values is not None
    assert output.current_values[0].dtype == np.uint8
    assert np.array_equal(output.current_values[0], np.array([[255, 128, 0]], dtype=np.uint8))

    # Test int16 (note: get new output reference after value_type change)
    node.set_properties({
        "value_type": "i16[2]",
        "default": "[-32768, 32767]"
    })
    output = node.outputs["value"]
    assert output.current_values is not None
    assert output.current_values[0].dtype == np.int16
    assert np.array_equal(output.current_values[0], np.array([[-32768, 32767]], dtype=np.int16))

    # Test float64
    node.set_properties({
        "value_type": "f64[2]",
        "default": "[1.5, 2.5]"
    })
    output = node.outputs["value"]
    assert output.current_values is not None
    assert output.current_values[0].dtype == np.float64
    assert np.array_equal(output.current_values[0], np.array([[1.5, 2.5]], dtype=np.float64))

    # Test int32
    node.set_properties({
        "value_type": "i32[3]",
        "default": "[100, -200, 300]"
    })
    output = node.outputs["value"]
    assert output.current_values is not None
    assert output.current_values[0].dtype == np.int32
    assert np.array_equal(output.current_values[0], np.array([[100, -200, 300]], dtype=np.int32))


def test_empty_value_node_default():
    """Test EmptyValueNode outputs empty array with default f32 type."""
    node = EmptyValueNode("test")

    output = node.outputs["value"]
    current_values = output.current_values

    assert current_values is not None
    assert len(current_values) == 1
    assert current_values[0].shape == (0,)
    assert current_values[0].dtype == np.float32


def test_empty_value_node_change_type():
    """Test EmptyValueNode can change value_type."""
    node = EmptyValueNode("test")

    # Change to int16
    node.set_properties({"value_type": "i16"})

    output = node.outputs["value"]
    current_values = output.current_values

    assert current_values is not None
    assert current_values[0].shape == (0,)
    assert current_values[0].dtype == np.int16
    assert node.properties["value_type"] == "i16"


def test_empty_value_node_multiple_types():
    """Test EmptyValueNode works with various data types."""
    node = EmptyValueNode("test")

    test_cases = [
        ("u8", np.uint8),
        ("i32", np.int32),
        ("f64", np.float64),
        ("c64", np.complex64),
    ]

    for type_name, expected_dtype in test_cases:
        node.set_properties({"value_type": type_name})
        output = node.outputs["value"]
        assert output.current_values is not None
        assert output.current_values[0].dtype == expected_dtype, f"Failed for {type_name}"
        assert output.current_values[0].shape == (0,)


def test_empty_value_node_with_shape():
    """Test EmptyValueNode considers shape - empty batch with correct trailing dims."""
    node = EmptyValueNode("test")

    # f32[3] -> shape (0, 3)
    node.set_properties({"value_type": "f32[3]"})
    output = node.outputs["value"]
    assert output.current_values is not None
    assert output.current_values[0].shape == (0, 3)
    assert output.current_values[0].dtype == np.float32

    # i16[2x4] -> shape (0, 2, 4)
    node.set_properties({"value_type": "i16[2x4]"})
    output = node.outputs["value"]
    assert output.current_values is not None
    assert output.current_values[0].shape == (0, 2, 4)
    assert output.current_values[0].dtype == np.int16


def test_empty_value_node_unsupported_type():
    """Test EmptyValueNode raises error for unsupported types like String."""
    import pytest

    node = EmptyValueNode("test")

    with pytest.raises(ValueError, match="Unsupported data type"):
        node.set_properties({"value_type": "str"})

    with pytest.raises(ValueError, match="Unsupported data type"):
        node.set_properties({"value_type": "any"})


# ---- FullLikeNode tests ----


def _capture_output(node, port_name="out"):
    """Subscribe to a node output and return a list that collects dispatched values."""
    captured = []
    node.outputs[port_name].subscribe("test", lambda vals: captured.append(vals))
    return captured


def test_full_like_scalar_fill():
    """fill=[5.0] (scalar), in=[[1,2,3]] → out=[[5,5,5]]"""
    node = FullLikeNode("test")
    captured = _capture_output(node)

    node.inputs["fill_value"].dispatch([np.array([5.0], dtype=np.float32)])
    node.inputs["in"].dispatch([np.array([[1.0, 2.0, 3.0]], dtype=np.float32)])

    assert len(captured) == 1
    expected = np.array([[5.0, 5.0, 5.0]], dtype=np.float32)
    np.testing.assert_array_equal(captured[0][0], expected)


def test_full_like_default_zero():
    """fill not set, in=[[1,2,3]] → out=[[0,0,0]]"""
    node = FullLikeNode("test")
    captured = _capture_output(node)

    node.inputs["in"].dispatch([np.array([[1.0, 2.0, 3.0]], dtype=np.float32)])

    assert len(captured) == 1
    expected = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
    np.testing.assert_array_equal(captured[0][0], expected)


def test_full_like_pattern_fill():
    """fill_value_shape="[3]", fill=[[1,0,0]], in 2 batches → every row [1,0,0]"""
    node = FullLikeNode("test")
    node.set_properties({"fill_value_shape": "[3]"})
    captured = _capture_output(node)

    node.inputs["fill_value"].dispatch(
        [np.array([[1.0, 0.0, 0.0]], dtype=np.float32)]
    )
    in_array = np.array([[9.0, 8.0, 7.0], [6.0, 5.0, 4.0]], dtype=np.float32)
    node.inputs["in"].dispatch([in_array])

    assert len(captured) == 1
    expected = np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=np.float32)
    np.testing.assert_array_equal(captured[0][0], expected)


def test_full_like_per_batch_scalar():
    """fill=[3,7] (2 batch scalars), in 2batch shape(2,3) → [[3,3,3],[7,7,7]]"""
    node = FullLikeNode("test")
    captured = _capture_output(node)

    node.inputs["fill_value"].dispatch([np.array([3.0, 7.0], dtype=np.float32)])
    in_array = np.ones((2, 3), dtype=np.float32)
    node.inputs["in"].dispatch([in_array])

    assert len(captured) == 1
    expected = np.array([[3.0, 3.0, 3.0], [7.0, 7.0, 7.0]], dtype=np.float32)
    np.testing.assert_array_equal(captured[0][0], expected)


def test_full_like_empty_input():
    """in=(0,3) → out=(0,3)"""
    node = FullLikeNode("test")
    captured = _capture_output(node)

    in_array = np.empty((0, 3), dtype=np.float32)
    node.inputs["in"].dispatch([in_array])

    assert len(captured) == 1
    assert captured[0][0].shape == (0, 3)
    assert captured[0][0].dtype == np.float32


def test_full_like_scalar_value_type():
    """value_type="i32", fill=[7], in=[1] → out=[7]"""
    node = FullLikeNode("test")
    node.set_properties({"value_type": "i32"})
    captured = _capture_output(node)

    node.inputs["fill_value"].dispatch([np.array([7], dtype=np.int32)])
    node.inputs["in"].dispatch([np.array([1], dtype=np.int32)])

    assert len(captured) == 1
    expected = np.array([7], dtype=np.int32)
    np.testing.assert_array_equal(captured[0][0], expected)


def test_full_like_fill_value_update():
    """fill=3→in→fill=9→in → the second output uses 9"""
    node = FullLikeNode("test")
    captured = _capture_output(node)

    node.inputs["fill_value"].dispatch([np.array([3.0], dtype=np.float32)])
    node.inputs["in"].dispatch([np.array([[1.0, 2.0, 3.0]], dtype=np.float32)])

    node.inputs["fill_value"].dispatch([np.array([9.0], dtype=np.float32)])
    node.inputs["in"].dispatch([np.array([[4.0, 5.0, 6.0]], dtype=np.float32)])

    assert len(captured) == 2
    np.testing.assert_array_equal(
        captured[0][0], np.array([[3.0, 3.0, 3.0]], dtype=np.float32)
    )
    np.testing.assert_array_equal(
        captured[1][0], np.array([[9.0, 9.0, 9.0]], dtype=np.float32)
    )


def test_full_like_value_type_change():
    """f32[3]→i16[2], the port type is updated"""
    node = FullLikeNode("test")

    assert node.inputs["in"].value_type_list[0].name == "f32[3]"
    assert node.outputs["out"].value_type_list[0].name == "f32[3]"
    assert node.inputs["fill_value"].value_type_list[0].name == "f32"

    node.set_properties({"value_type": "i16[2]"})

    assert node.inputs["in"].value_type_list[0].name == "i16[2]"
    assert node.outputs["out"].value_type_list[0].name == "i16[2]"
    assert node.inputs["fill_value"].value_type_list[0].name == "i16"
    assert node.properties["value_type"] == "i16[2]"


def test_full_like_dtype_inherited():
    """value_type="i32[3]" → the fill_value port becomes i32"""
    node = FullLikeNode("test")
    node.set_properties({"value_type": "i32[3]"})

    assert node.inputs["fill_value"].value_type_list[0].name == "i32"

    captured = _capture_output(node)
    node.inputs["fill_value"].dispatch([np.array([42], dtype=np.int32)])
    node.inputs["in"].dispatch([np.array([[1, 2, 3]], dtype=np.int32)])

    assert len(captured) == 1
    assert captured[0][0].dtype == np.int32
    np.testing.assert_array_equal(
        captured[0][0], np.array([[42, 42, 42]], dtype=np.int32)
    )


def test_full_like_any_rejected():
    """value_type="any" → ValueError"""
    import pytest

    node = FullLikeNode("test")
    with pytest.raises(ValueError, match="DataType.Any is not supported"):
        node.set_properties({"value_type": "any"})


def test_full_like_variable_shape_rejected():
    """value_type="f32[N]" → ValueError"""
    import pytest

    node = FullLikeNode("test")
    with pytest.raises(ValueError, match="Variable dimensions not supported"):
        node.set_properties({"value_type": "f32[N]"})


# ---- EnumerateNode tests ----


def test_enumerate_creation():
    node = EnumerateNode("test")
    assert "value" in node.inputs
    assert "start" in node.inputs
    assert "index" in node.outputs


def test_enumerate_single_dispatch():
    node = EnumerateNode("test")
    captured = _capture_output(node, "index")

    node.inputs["value"].dispatch([np.arange(5, dtype=np.float32)])

    assert len(captured) == 1
    np.testing.assert_array_equal(captured[0][0], np.array([0, 1, 2, 3, 4], dtype=np.int32))


def test_enumerate_cumulative():
    node = EnumerateNode("test")
    captured = _capture_output(node, "index")

    node.inputs["value"].dispatch([np.zeros(3, dtype=np.float32)])
    node.inputs["value"].dispatch([np.zeros(2, dtype=np.float32)])

    assert len(captured) == 2
    np.testing.assert_array_equal(captured[0][0], np.array([0, 1, 2], dtype=np.int32))
    np.testing.assert_array_equal(captured[1][0], np.array([3, 4], dtype=np.int32))


def test_enumerate_start_reset():
    node = EnumerateNode("test")
    captured = _capture_output(node, "index")

    node.inputs["start"].dispatch([np.array([10], dtype=np.int32)])
    node.inputs["value"].dispatch([np.zeros(3, dtype=np.float32)])

    assert len(captured) == 1
    np.testing.assert_array_equal(captured[0][0], np.array([10, 11, 12], dtype=np.int32))


def test_enumerate_start_mid_sequence():
    node = EnumerateNode("test")
    captured = _capture_output(node, "index")

    node.inputs["value"].dispatch([np.zeros(3, dtype=np.float32)])
    node.inputs["start"].dispatch([np.array([100], dtype=np.int32)])
    node.inputs["value"].dispatch([np.zeros(2, dtype=np.float32)])

    assert len(captured) == 2
    np.testing.assert_array_equal(captured[0][0], np.array([0, 1, 2], dtype=np.int32))
    np.testing.assert_array_equal(captured[1][0], np.array([100, 101], dtype=np.int32))


def test_enumerate_single_element():
    node = EnumerateNode("test")
    captured = _capture_output(node, "index")

    node.inputs["value"].dispatch([np.array([42.0], dtype=np.float32)])

    assert len(captured) == 1
    np.testing.assert_array_equal(captured[0][0], np.array([0], dtype=np.int32))


# ---------------------------------------------------------------------------
# ValueAccumulatorNode tests
# ---------------------------------------------------------------------------


def _make_acc_node(value_type="i32", clamp_min=None, clamp_max=None):
    """Create a ValueAccumulatorNode with optional clamp bounds."""
    node = ValueAccumulatorNode("test")
    props = {"value_type": value_type}
    if clamp_min is not None:
        props["initial_clamp_min"] = clamp_min
    if clamp_max is not None:
        props["initial_clamp_max"] = clamp_max
    node.set_properties(props)
    return node


def test_acc_basic_sum():
    """Basic accumulation: [1,2,3]->6, [4]->10."""
    node = _make_acc_node()
    captured = _capture_output(node, "value")

    node.inputs["in"].dispatch([np.array([1, 2, 3], dtype=np.int32)])
    assert len(captured) == 1
    assert captured[0][0].item() == 6

    node.inputs["in"].dispatch([np.array([4], dtype=np.int32)])
    assert len(captured) == 2
    assert captured[1][0].item() == 10


def test_acc_reset():
    """Reset sets sum back to 0."""
    node = _make_acc_node()
    captured = _capture_output(node, "value")

    node.inputs["in"].dispatch([np.array([5], dtype=np.int32)])
    assert captured[-1][0].item() == 5

    node.inputs["reset"].dispatch([np.array([0], dtype=np.int32)])
    assert captured[-1][0].item() == 0

    node.inputs["in"].dispatch([np.array([3], dtype=np.int32)])
    assert captured[-1][0].item() == 3


def test_acc_clamp_max_overflow():
    """Overflow dispatched when sum exceeds clamp_max."""
    node = _make_acc_node(clamp_max=10)
    value_out = _capture_output(node, "value")
    overflow_out = _capture_output(node, "overflow")

    node.inputs["in"].dispatch([np.array([7], dtype=np.int32)])
    assert value_out[-1][0].item() == 7
    assert len(overflow_out) == 0

    node.inputs["in"].dispatch([np.array([5], dtype=np.int32)])
    assert value_out[-1][0].item() == 10
    assert len(overflow_out) == 1
    assert overflow_out[0][0].item() == 2


def test_acc_clamp_min_underflow():
    """Underflow dispatched when sum goes below clamp_min."""
    node = _make_acc_node(clamp_min=0)
    value_out = _capture_output(node, "value")
    underflow_out = _capture_output(node, "underflow")

    node.inputs["in"].dispatch([np.array([-3], dtype=np.int32)])
    assert value_out[-1][0].item() == 0
    assert len(underflow_out) == 1
    assert underflow_out[0][0].item() == -3


def test_acc_no_overflow_underflow_within_range():
    """No overflow/underflow when within clamp range."""
    node = _make_acc_node(clamp_min=-10, clamp_max=10)
    overflow_out = _capture_output(node, "overflow")
    underflow_out = _capture_output(node, "underflow")

    node.inputs["in"].dispatch([np.array([5], dtype=np.int32)])
    node.inputs["in"].dispatch([np.array([-3], dtype=np.int32)])

    assert len(overflow_out) == 0
    assert len(underflow_out) == 0


def test_acc_float32_precision():
    """Float32 accumulation preserves fractional parts (bug: int() truncates)."""
    node = _make_acc_node(value_type="f32")
    captured = _capture_output(node, "value")

    node.inputs["in"].dispatch([np.array([0.5], dtype=np.float32)])
    assert captured[-1][0].item() == pytest.approx(0.5, abs=1e-6)

    node.inputs["in"].dispatch([np.array([0.3], dtype=np.float32)])
    assert captured[-1][0].item() == pytest.approx(0.8, abs=1e-6)


def test_acc_float64_precision():
    """Float64 accumulation preserves fractional parts."""
    node = _make_acc_node(value_type="f64")
    captured = _capture_output(node, "value")

    node.inputs["in"].dispatch([np.array([0.1], dtype=np.float64)])
    node.inputs["in"].dispatch([np.array([0.2], dtype=np.float64)])

    assert captured[-1][0].item() == pytest.approx(0.3, abs=1e-12)


def test_acc_float_clamp():
    """Float clamp_max with overflow preserves fractional overflow."""
    node = _make_acc_node(value_type="f32", clamp_max=1.5)
    value_out = _capture_output(node, "value")
    overflow_out = _capture_output(node, "overflow")

    node.inputs["in"].dispatch([np.array([1.8], dtype=np.float32)])
    assert value_out[-1][0].item() == pytest.approx(1.5, abs=1e-6)
    assert len(overflow_out) == 1
    assert overflow_out[0][0].item() == pytest.approx(0.3, abs=1e-5)


def test_acc_dynamic_clamp_update():
    """Dynamic clamp update via input ports."""
    node = _make_acc_node()
    value_out = _capture_output(node, "value")
    overflow_out = _capture_output(node, "overflow")

    node.inputs["in"].dispatch([np.array([100], dtype=np.int32)])
    assert value_out[-1][0].item() == 100

    # Set clamp_max dynamically — doesn't retroactively clamp existing sum
    node.inputs["clamp_max"].dispatch([np.array([50], dtype=np.int32)])

    # Next input should trigger clamp
    node.inputs["in"].dispatch([np.array([1], dtype=np.int32)])
    assert value_out[-1][0].item() == 50


def test_acc_dynamic_clamp_reset():
    """Empty array on clamp port resets clamp to None."""
    node = _make_acc_node(clamp_max=10)
    value_out = _capture_output(node, "value")

    # Remove clamp
    node.inputs["clamp_max"].dispatch([np.array([], dtype=np.int32)])

    # Should now accumulate beyond 10
    node.inputs["in"].dispatch([np.array([15], dtype=np.int32)])
    assert value_out[-1][0].item() == 15


def test_acc_value_type_change():
    """Changing value_type updates port types and resets sum."""
    node = _make_acc_node(value_type="i32")

    assert node.inputs["in"].value_type_list[0].name == "i32"
    assert node.outputs["value"].value_type_list[0].name == "i32"

    node.set_properties({"value_type": "f32"})

    assert node.inputs["in"].value_type_list[0].name == "f32"
    assert node.outputs["value"].value_type_list[0].name == "f32"


def test_acc_batch_sum():
    """Batch input sums all elements at once."""
    node = _make_acc_node()
    captured = _capture_output(node, "value")

    node.inputs["in"].dispatch([np.array([1, 2, 3, 4, 5], dtype=np.int32)])
    assert captured[-1][0].item() == 15


# =============================================================================
# dispatch_on_init property
#
# Each Value node (RealNumberValue, ComplexNumberValue, StringValue, ArrayValue)
# supports a `dispatch_on_init` property (default true). When set to false, the
# node skips its automatic init dispatch — useful when multiple Value nodes
# share a destination port and order-dependent latched values must be avoided.
# =============================================================================


def _capture(node, port_name):
    captured = []
    node.outputs[port_name].subscribe(id(captured), lambda values: captured.append(values))
    return captured


# ---------- RealNumberValueNode ----------

def test_real_number_value_dispatch_on_init_default_true():
    """dispatch_on_init=true (default): no emit at __init__; activate emits default."""
    node = RealNumberValueNode("test")
    assert node.outputs["value"].current_values is None  # side-effect-free __init__
    node._do_activate()
    cv = node.outputs["value"].current_values
    assert cv is not None
    assert cv[0][0] == 0


def test_real_number_value_dispatch_on_init_false_no_init_dispatch():
    """dispatch_on_init=false → activate does not emit; current_values stays None."""
    node = RealNumberValueNode("test")
    node.set_properties({"dispatch_on_init": False, "default": 5.0})
    node._do_activate()
    assert node.outputs["value"].current_values is None


def test_real_number_value_set_properties_before_activation_no_dispatch():
    """Before activation (is_active False), set_properties does not auto-dispatch."""
    node = RealNumberValueNode("test")
    captured = _capture(node, "value")
    node.set_properties({"default": 7.5})
    assert captured == []


def test_real_number_value_runtime_default_change_emits():
    """After activation, changing default re-emits (runtime edit path)."""
    node = RealNumberValueNode("test")
    node._do_activate()
    captured = _capture(node, "value")
    node.set_properties({"default": 9.0})
    assert len(captured) == 1
    assert captured[0][0][0] == 9.0


def test_real_number_value_dispatch_trigger_emits_default():
    """The `dispatch` input emits the configured `default`, independent of dispatch_on_init."""
    node = RealNumberValueNode("test")
    node.set_properties({"dispatch_on_init": False, "default": 7.5})
    captured = _capture(node, "value")
    node.inputs["dispatch"].dispatch([np.array([True])])
    assert len(captured) == 1
    assert captured[0][0][0] == 7.5


def test_real_number_value_activate_skips_when_already_emitted():
    """If `dispatch` already populated current_values, activate does not re-emit."""
    node = RealNumberValueNode("test")
    node.set_properties({"default": 5.0})  # dispatch_on_init=true
    node.inputs["dispatch"].dispatch([np.array([True])])  # sets current_values
    captured = _capture(node, "value")
    node._do_activate()
    assert captured == []  # guard skips the duplicate emit


# ---------- ComplexNumberValueNode ----------

def test_complex_number_value_dispatch_on_init_default_true():
    node = ComplexNumberValueNode("test")
    assert node.outputs["value"].current_values is None
    node._do_activate()
    cv = node.outputs["value"].current_values
    assert cv is not None
    assert cv[0][0] == complex(0)


def test_complex_number_value_dispatch_on_init_false_no_init_dispatch():
    node = ComplexNumberValueNode("test")
    node.set_properties({"dispatch_on_init": False, "default": "1.0+2.0j"})
    node._do_activate()
    assert node.outputs["value"].current_values is None


def test_complex_number_value_dispatch_trigger_emits_default():
    node = ComplexNumberValueNode("test")
    node.set_properties({"dispatch_on_init": False, "default": "4.5-2.5j"})
    captured = _capture(node, "value")
    node.inputs["dispatch"].dispatch([np.array([True])])
    assert len(captured) == 1
    assert captured[0][0][0] == complex(4.5, -2.5)


# ---------- StringValueNode ----------

def test_string_value_dispatch_on_init_default_true():
    node = StringValueNode("test")
    assert node.outputs["value"].current_values is None
    node._do_activate()
    cv = node.outputs["value"].current_values
    assert cv is not None
    assert cv[0][0] == "hello_world!"


def test_string_value_dispatch_on_init_false_no_init_dispatch():
    node = StringValueNode("test")
    node.set_properties({"dispatch_on_init": False, "default": "abc"})
    node._do_activate()
    assert node.outputs["value"].current_values is None


def test_string_value_dispatch_trigger_emits_default():
    node = StringValueNode("test")
    node.set_properties({"dispatch_on_init": False, "default": "fixed_string"})
    captured = _capture(node, "value")
    node.inputs["dispatch"].dispatch([np.array([True])])
    assert len(captured) == 1
    assert captured[0][0][0] == "fixed_string"


# ---------- ArrayValueNode ----------

def test_array_value_dispatch_on_init_default_true():
    node = ArrayValueNode("test")
    assert node.outputs["value"].current_values is None
    node._do_activate()
    cv = node.outputs["value"].current_values
    assert cv is not None
    assert np.array_equal(cv[0], np.array([[0, 0, 0]], dtype=np.float32))


def test_array_value_dispatch_on_init_false_no_init_dispatch():
    node = ArrayValueNode("test")
    node.set_properties({"dispatch_on_init": False, "default": "[1, 2, 3]"})
    node._do_activate()
    assert node.outputs["value"].current_values is None


def test_array_value_dispatch_trigger_emits_default():
    node = ArrayValueNode("test")
    node.set_properties({"dispatch_on_init": False, "default": "[42, 43, 44]"})
    captured = _capture(node, "value")
    node.inputs["dispatch"].dispatch([np.array([True])])
    assert len(captured) == 1
    assert np.array_equal(
        captured[0][0], np.array([[42.0, 43.0, 44.0]], dtype=np.float32)
    )
