import numpy as np
import pytest

from nonoha_core.nodes.flow_control_nodes import (
    BoolBranchNode,
    BoolEdgeNode,
    OneShotGateNode,
    SequenceNode,
    SwitchBranchNode,
    TransitionNode,
    ValueChangedNode,
    ValuesBranchNode,
    ValuesDelayNode,
    ValuesGateNode,
    ValuesLatchNode,
    YieldNode,
)


def test_one_shot_gate_first_input_passes():
    node = OneShotGateNode("test")

    results = []
    node.outputs["out"].subscribe(0, lambda values: results.append(values))

    node.inputs["in"].dispatch([np.array([42.0], dtype=np.float32)])

    assert len(results) == 1
    assert np.array_equal(results[0][0], np.array([42.0], dtype=np.float32))


def test_one_shot_gate_locked_input_dropped():
    node = OneShotGateNode("test")

    results = []
    node.outputs["out"].subscribe(0, lambda values: results.append(values))

    node.inputs["in"].dispatch([np.array([1.0], dtype=np.float32)])
    node.inputs["in"].dispatch([np.array([2.0], dtype=np.float32)])
    node.inputs["in"].dispatch([np.array([3.0], dtype=np.float32)])

    assert len(results) == 1
    assert np.array_equal(results[0][0], np.array([1.0], dtype=np.float32))


def test_one_shot_gate_unlock_allows_next():
    node = OneShotGateNode("test")

    results = []
    node.outputs["out"].subscribe(0, lambda values: results.append(values))

    node.inputs["in"].dispatch([np.array([1.0], dtype=np.float32)])
    assert len(results) == 1

    node.inputs["unlock"].dispatch([np.array([0], dtype=np.int8)])

    node.inputs["in"].dispatch([np.array([2.0], dtype=np.float32)])
    assert len(results) == 2
    assert np.array_equal(results[1][0], np.array([2.0], dtype=np.float32))


def test_one_shot_gate_multiple_unlock_cycles():
    node = OneShotGateNode("test")

    results = []
    node.outputs["out"].subscribe(0, lambda values: results.append(values))

    for i in range(5):
        node.inputs["in"].dispatch([np.array([float(i)], dtype=np.float32)])
        node.inputs["in"].dispatch([np.array([float(i + 100)], dtype=np.float32)])
        node.inputs["unlock"].dispatch([np.array([0], dtype=np.int8)])

    assert len(results) == 5
    for i in range(5):
        assert np.array_equal(results[i][0], np.array([float(i)], dtype=np.float32))


def test_one_shot_gate_consecutive_unlocks():
    node = OneShotGateNode("test")

    results = []
    node.outputs["out"].subscribe(0, lambda values: results.append(values))

    node.inputs["in"].dispatch([np.array([1.0], dtype=np.float32)])
    node.inputs["unlock"].dispatch([np.array([0], dtype=np.int8)])
    node.inputs["unlock"].dispatch([np.array([0], dtype=np.int8)])
    node.inputs["unlock"].dispatch([np.array([0], dtype=np.int8)])

    node.inputs["in"].dispatch([np.array([2.0], dtype=np.float32)])
    assert len(results) == 2


def test_one_shot_gate_set_properties_value_type_list():
    node = OneShotGateNode("test")
    node.set_properties({"value_type_list": "i32"})

    results = []
    node.outputs["out"].subscribe(0, lambda values: results.append(values))

    node.inputs["in"].dispatch([np.array([99], dtype=np.int32)])

    assert len(results) == 1
    assert results[0][0].dtype == np.int32
    assert np.array_equal(results[0][0], np.array([99], dtype=np.int32))


# ---------------------------------------------------------------------------
# SequenceNode
# ---------------------------------------------------------------------------


def test_sequence_dispatches_to_all_outputs():
    node = SequenceNode("test")
    results_0 = []
    results_1 = []
    node.outputs["out_0"].subscribe(0, lambda v: results_0.append(v))
    node.outputs["out_1"].subscribe(0, lambda v: results_1.append(v))

    node.inputs["in"].dispatch([np.array([1.0], dtype=np.float32)])

    assert len(results_0) == 1
    assert len(results_1) == 1
    np.testing.assert_array_equal(results_0[0][0], np.array([1.0], dtype=np.float32))
    np.testing.assert_array_equal(results_1[0][0], np.array([1.0], dtype=np.float32))


def test_sequence_set_properties_count():
    node = SequenceNode("test")
    node.set_properties({"count": 4})

    assert len([k for k in node.outputs if k.startswith("out_")]) == 4

    results = {i: [] for i in range(4)}
    for i in range(4):
        node.outputs[f"out_{i}"].subscribe(0, lambda v, idx=i: results[idx].append(v))

    node.inputs["in"].dispatch([np.array([5.0], dtype=np.float32)])
    for i in range(4):
        assert len(results[i]) == 1


def test_sequence_set_properties_value_type():
    node = SequenceNode("test")
    node.set_properties({"value_type_list": "i32"})

    results = []
    node.outputs["out_0"].subscribe(0, lambda v: results.append(v))

    node.inputs["in"].dispatch([np.array([7], dtype=np.int32)])
    assert len(results) == 1
    assert results[0][0].dtype == np.int32


def test_sequence_set_properties_count_less_than_one_raises():
    node = SequenceNode("test")
    with pytest.raises(ValueError):
        node.set_properties({"count": 0})


def test_sequence_multiple_dispatches():
    node = SequenceNode("test")
    results_0 = []
    node.outputs["out_0"].subscribe(0, lambda v: results_0.append(v))

    for i in range(3):
        node.inputs["in"].dispatch([np.array([float(i)], dtype=np.float32)])

    assert len(results_0) == 3


# ---------------------------------------------------------------------------
# YieldNode
# ---------------------------------------------------------------------------


def test_yield_port_structure():
    node = YieldNode("test")
    assert "in" in node.inputs
    assert "out" in node.outputs


def test_yield_no_dispatch_without_activate():
    """Without activate(), _main_loop is None so dispatch is silently dropped."""
    node = YieldNode("test")
    results = []
    node.outputs["out"].subscribe(0, lambda v: results.append(v))

    node.inputs["in"].dispatch([np.array([1.0], dtype=np.float32)])
    assert len(results) == 0


def test_yield_set_properties_in_types():
    node = YieldNode("test")
    node.set_properties({"in_types": "i32,f64"})

    assert node.properties["in_types"] == "i32,f64"
    assert "in" in node.inputs
    assert "out" in node.outputs


# ---------------------------------------------------------------------------
# ValuesLatchNode
# ---------------------------------------------------------------------------


def test_values_latch_dispatches_on_input_when_dispatch_if_input_true():
    node = ValuesLatchNode("test")
    results = []
    node.outputs["values"].subscribe(0, lambda v: results.append(v))

    node.inputs["values"].dispatch(
        [np.array([1.0], dtype=np.float32), np.array([2.0], dtype=np.float32)]
    )
    assert len(results) == 1
    np.testing.assert_array_equal(results[0][0], np.array([1.0], dtype=np.float32))


def test_values_latch_no_dispatch_on_input_when_dispatch_if_input_false():
    node = ValuesLatchNode("test")
    node.set_properties({"dispatch_if_input": False})

    results = []
    node.outputs["values"].subscribe(0, lambda v: results.append(v))

    node.inputs["values"].dispatch(
        [np.array([1.0], dtype=np.float32), np.array([2.0], dtype=np.float32)]
    )
    assert len(results) == 0


def test_values_latch_redispatches_on_trigger():
    node = ValuesLatchNode("test")
    results = []
    node.outputs["values"].subscribe(0, lambda v: results.append(v))

    node.inputs["values"].dispatch(
        [np.array([10.0], dtype=np.float32), np.array([20.0], dtype=np.float32)]
    )
    assert len(results) == 1

    # Trigger re-dispatch of latched values
    node.inputs["dispatch"].dispatch([np.array([0], dtype=np.int8)])
    assert len(results) == 2
    np.testing.assert_array_equal(results[1][0], np.array([10.0], dtype=np.float32))
    np.testing.assert_array_equal(results[1][1], np.array([20.0], dtype=np.float32))


def test_values_latch_trigger_before_any_input_no_dispatch():
    node = ValuesLatchNode("test")
    results = []
    node.outputs["values"].subscribe(0, lambda v: results.append(v))

    node.inputs["dispatch"].dispatch([np.array([0], dtype=np.int8)])
    assert len(results) == 0


def test_values_latch_set_properties_value_type():
    node = ValuesLatchNode("test")
    node.set_properties({"value_type_list": "i32"})

    results = []
    node.outputs["values"].subscribe(0, lambda v: results.append(v))

    node.inputs["values"].dispatch([np.array([42], dtype=np.int32)])
    assert len(results) == 1
    assert results[0][0].dtype == np.int32


# ---------------------------------------------------------------------------
# ValuesDelayNode
# ---------------------------------------------------------------------------


def test_values_delay_port_structure():
    node = ValuesDelayNode("test")
    assert "values" in node.inputs
    assert "reset" in node.inputs
    assert "values" in node.outputs


def test_values_delay_set_properties_delay():
    node = ValuesDelayNode("test")
    node.set_properties({"delay": 2.5})
    assert node.properties["delay"] == 2.5


def test_values_delay_set_properties_value_type():
    node = ValuesDelayNode("test")
    node.set_properties({"value_type_list": "f32"})
    assert node.properties["value_type_list"] == "f32"
    assert "values" in node.inputs
    assert "reset" in node.inputs
    assert "values" in node.outputs


def test_values_delay_reset_clears_task():
    """reset clears the internal task identity so a stale dispatch can be
    rejected by the task identity check inside _delay_dispatch.
    """
    import asyncio

    async def run():
        node = ValuesDelayNode("test")
        node.set_properties({"delay": 10.0, "value_type_list": "f32"})
        node.inputs["values"].dispatch([np.array([1.0], dtype=np.float32)])
        assert node._task is not None
        node.inputs["reset"].dispatch([np.array([1], dtype=np.int8)])
        assert node._task is None

    asyncio.run(run())


def test_values_delay_consecutive_input_replaces_task():
    """A new input cancels the previous task and installs a fresh one. The
    previous task's identity will no longer match self._task.
    """
    import asyncio

    async def run():
        node = ValuesDelayNode("test")
        node.set_properties({"delay": 10.0, "value_type_list": "f32"})
        node.inputs["values"].dispatch([np.array([1.0], dtype=np.float32)])
        first_task = node._task
        assert first_task is not None
        node.inputs["values"].dispatch([np.array([2.0], dtype=np.float32)])
        second_task = node._task
        assert second_task is not None
        assert first_task is not second_task

    asyncio.run(run())


# ---------------------------------------------------------------------------
# ValueChangedNode
# ---------------------------------------------------------------------------


def test_value_changed_first_value_always_dispatches():
    node = ValueChangedNode("test")
    results = []
    node.outputs["value"].subscribe(0, lambda v: results.append(v))

    node.inputs["value"].dispatch([np.array([5], dtype=np.int8)])
    assert len(results) == 1
    np.testing.assert_array_equal(results[0][0], np.array([5], dtype=np.int8))


def test_value_changed_same_value_no_dispatch():
    node = ValueChangedNode("test")
    results = []
    node.outputs["value"].subscribe(0, lambda v: results.append(v))

    node.inputs["value"].dispatch([np.array([3], dtype=np.int8)])
    node.inputs["value"].dispatch([np.array([3], dtype=np.int8)])
    node.inputs["value"].dispatch([np.array([3], dtype=np.int8)])
    assert len(results) == 1


def test_value_changed_different_value_dispatches():
    node = ValueChangedNode("test")
    results = []
    node.outputs["value"].subscribe(0, lambda v: results.append(v))

    node.inputs["value"].dispatch([np.array([1], dtype=np.int8)])
    node.inputs["value"].dispatch([np.array([2], dtype=np.int8)])
    node.inputs["value"].dispatch([np.array([2], dtype=np.int8)])
    node.inputs["value"].dispatch([np.array([3], dtype=np.int8)])

    assert len(results) == 3
    np.testing.assert_array_equal(results[0][0], np.array([1], dtype=np.int8))
    np.testing.assert_array_equal(results[1][0], np.array([2], dtype=np.int8))
    np.testing.assert_array_equal(results[2][0], np.array([3], dtype=np.int8))


def test_value_changed_different_length_dispatches():
    node = ValueChangedNode("test")
    results = []
    node.outputs["value"].subscribe(0, lambda v: results.append(v))

    node.inputs["value"].dispatch([np.array([1, 2], dtype=np.int8)])
    node.inputs["value"].dispatch([np.array([1], dtype=np.int8)])

    assert len(results) == 2


def test_value_changed_set_properties_value_type():
    node = ValueChangedNode("test")
    node.set_properties({"value_type": "f32"})

    results = []
    node.outputs["value"].subscribe(0, lambda v: results.append(v))

    node.inputs["value"].dispatch([np.array([1.5], dtype=np.float32)])
    assert len(results) == 1
    assert results[0][0].dtype == np.float32


# ---------------------------------------------------------------------------
# BoolBranchNode
# ---------------------------------------------------------------------------


def test_bool_branch_routes_true():
    node = BoolBranchNode("test")
    true_results = []
    false_results = []
    node.outputs["true"].subscribe(0, lambda v: true_results.append(v))
    node.outputs["false"].subscribe(0, lambda v: false_results.append(v))

    node.inputs["bool"].dispatch([np.array([True], dtype=bool)])

    assert len(true_results) == 1
    assert len(false_results) == 0
    assert true_results[0][0][0] == True


def test_bool_branch_routes_false():
    node = BoolBranchNode("test")
    true_results = []
    false_results = []
    node.outputs["true"].subscribe(0, lambda v: true_results.append(v))
    node.outputs["false"].subscribe(0, lambda v: false_results.append(v))

    node.inputs["bool"].dispatch([np.array([False], dtype=bool)])

    assert len(true_results) == 0
    assert len(false_results) == 1
    assert false_results[0][0][0] == False


def test_bool_branch_multiple_elements():
    node = BoolBranchNode("test")
    true_results = []
    false_results = []
    node.outputs["true"].subscribe(0, lambda v: true_results.append(v))
    node.outputs["false"].subscribe(0, lambda v: false_results.append(v))

    node.inputs["bool"].dispatch([np.array([True, False, True, False, True], dtype=bool)])

    assert len(true_results) == 3
    assert len(false_results) == 2


def test_bool_branch_empty_array():
    node = BoolBranchNode("test")
    true_results = []
    false_results = []
    node.outputs["true"].subscribe(0, lambda v: true_results.append(v))
    node.outputs["false"].subscribe(0, lambda v: false_results.append(v))

    node.inputs["bool"].dispatch([np.array([], dtype=bool)])

    assert len(true_results) == 0
    assert len(false_results) == 0


# ---------------------------------------------------------------------------
# SwitchBranchNode
# ---------------------------------------------------------------------------


def test_switch_branch_routes_to_matching_case():
    node = SwitchBranchNode("test")
    case_0 = []
    case_1 = []
    case_2 = []
    else_results = []
    node.outputs["case_0"].subscribe(0, lambda v: case_0.append(v))
    node.outputs["case_1"].subscribe(0, lambda v: case_1.append(v))
    node.outputs["case_2"].subscribe(0, lambda v: case_2.append(v))
    node.outputs["else"].subscribe(0, lambda v: else_results.append(v))

    node.inputs["value"].dispatch([np.array([1], dtype=np.int32)])

    assert len(case_0) == 0
    assert len(case_1) == 1
    assert len(case_2) == 0
    assert len(else_results) == 0
    np.testing.assert_array_equal(case_1[0][0], np.array([1], dtype=np.int32))


def test_switch_branch_routes_to_else():
    node = SwitchBranchNode("test")
    else_results = []
    node.outputs["else"].subscribe(0, lambda v: else_results.append(v))

    node.inputs["value"].dispatch([np.array([99], dtype=np.int32)])

    assert len(else_results) == 1
    np.testing.assert_array_equal(else_results[0][0], np.array([99], dtype=np.int32))


def test_switch_branch_multiple_elements():
    node = SwitchBranchNode("test")
    case_0 = []
    case_1 = []
    else_results = []
    node.outputs["case_0"].subscribe(0, lambda v: case_0.append(v))
    node.outputs["case_1"].subscribe(0, lambda v: case_1.append(v))
    node.outputs["else"].subscribe(0, lambda v: else_results.append(v))

    node.inputs["value"].dispatch([np.array([0, 1, 5, 0], dtype=np.int32)])

    assert len(case_0) == 2
    assert len(case_1) == 1
    assert len(else_results) == 1


def test_switch_branch_set_properties_case_values():
    node = SwitchBranchNode("test")
    node.set_properties({"case_values": "10,20"})

    assert "case_10" in node.outputs
    assert "case_20" in node.outputs
    assert "case_0" not in node.outputs

    case_10 = []
    node.outputs["case_10"].subscribe(0, lambda v: case_10.append(v))

    node.inputs["value"].dispatch([np.array([10], dtype=np.int32)])
    assert len(case_10) == 1


def test_switch_branch_empty_array():
    node = SwitchBranchNode("test")
    case_0 = []
    else_results = []
    node.outputs["case_0"].subscribe(0, lambda v: case_0.append(v))
    node.outputs["else"].subscribe(0, lambda v: else_results.append(v))

    node.inputs["value"].dispatch([np.array([], dtype=np.int32)])

    assert len(case_0) == 0
    assert len(else_results) == 0


# ---------------------------------------------------------------------------
# ValuesBranchNode
# ---------------------------------------------------------------------------


def test_values_branch_routes_by_index():
    node = ValuesBranchNode("test")
    results_0 = []
    results_1 = []
    node.outputs["out_0"].subscribe(0, lambda v: results_0.append(v))
    node.outputs["out_1"].subscribe(0, lambda v: results_1.append(v))

    # Set index to 1
    node.inputs["index"].dispatch([np.array([1], dtype=np.int8)])
    # Dispatch values
    node.inputs["values"].dispatch([np.array([42.0], dtype=np.float32)])

    assert len(results_0) == 0
    assert len(results_1) == 1
    np.testing.assert_array_equal(results_1[0][0], np.array([42.0], dtype=np.float32))


def test_values_branch_no_dispatch_without_index():
    node = ValuesBranchNode("test")
    results_0 = []
    node.outputs["out_0"].subscribe(0, lambda v: results_0.append(v))

    node.inputs["values"].dispatch([np.array([1.0], dtype=np.float32)])
    assert len(results_0) == 0


def test_values_branch_out_of_range_index_no_dispatch():
    node = ValuesBranchNode("test")
    results_0 = []
    results_1 = []
    node.outputs["out_0"].subscribe(0, lambda v: results_0.append(v))
    node.outputs["out_1"].subscribe(0, lambda v: results_1.append(v))

    node.inputs["index"].dispatch([np.array([5], dtype=np.int8)])
    node.inputs["values"].dispatch([np.array([1.0], dtype=np.float32)])

    assert len(results_0) == 0
    assert len(results_1) == 0


def test_values_branch_negative_index_no_dispatch():
    node = ValuesBranchNode("test")
    results_0 = []
    node.outputs["out_0"].subscribe(0, lambda v: results_0.append(v))

    node.inputs["index"].dispatch([np.array([-1], dtype=np.int8)])
    node.inputs["values"].dispatch([np.array([1.0], dtype=np.float32)])

    assert len(results_0) == 0


def test_values_branch_set_properties_output_count():
    node = ValuesBranchNode("test")
    node.set_properties({"output_count": 4})

    assert len([k for k in node.outputs if k.startswith("out_")]) == 4

    results_3 = []
    node.outputs["out_3"].subscribe(0, lambda v: results_3.append(v))
    node.inputs["index"].dispatch([np.array([3], dtype=np.int8)])
    node.inputs["values"].dispatch([np.array([9.0], dtype=np.float32)])

    assert len(results_3) == 1


def test_values_branch_set_properties_value_type():
    node = ValuesBranchNode("test")
    node.set_properties({"value_type_list": "i32"})

    results = []
    node.outputs["out_0"].subscribe(0, lambda v: results.append(v))
    node.inputs["index"].dispatch([np.array([0], dtype=np.int8)])
    node.inputs["values"].dispatch([np.array([7], dtype=np.int32)])

    assert len(results) == 1
    assert results[0][0].dtype == np.int32


def test_values_branch_set_properties_output_count_less_than_one_raises():
    node = ValuesBranchNode("test")
    with pytest.raises(ValueError):
        node.set_properties({"output_count": 0})


def test_values_branch_empty_index_array_no_dispatch():
    node = ValuesBranchNode("test")
    results_0 = []
    node.outputs["out_0"].subscribe(0, lambda v: results_0.append(v))

    node.inputs["index"].dispatch([np.array([], dtype=np.int8)])
    node.inputs["values"].dispatch([np.array([1.0], dtype=np.float32)])

    assert len(results_0) == 0


# ---------------------------------------------------------------------------
# ValuesGateNode
# ---------------------------------------------------------------------------


def test_values_gate_forwards_selected_input():
    node = ValuesGateNode("test")
    results = []
    node.outputs["out"].subscribe(0, lambda v: results.append(v))

    # Select input 1
    node.inputs["index"].dispatch([np.array([1], dtype=np.int8)])

    # Dispatch to in_0 (should be ignored)
    node.inputs["in_0"].dispatch([np.array([10.0], dtype=np.float32)])
    assert len(results) == 0

    # Dispatch to in_1 (should pass through)
    node.inputs["in_1"].dispatch([np.array([20.0], dtype=np.float32)])
    assert len(results) == 1
    np.testing.assert_array_equal(results[0][0], np.array([20.0], dtype=np.float32))


def test_values_gate_no_dispatch_without_index():
    node = ValuesGateNode("test")
    results = []
    node.outputs["out"].subscribe(0, lambda v: results.append(v))

    node.inputs["in_0"].dispatch([np.array([1.0], dtype=np.float32)])
    assert len(results) == 0


def test_values_gate_switch_index():
    node = ValuesGateNode("test")
    results = []
    node.outputs["out"].subscribe(0, lambda v: results.append(v))

    # Start with input 0
    node.inputs["index"].dispatch([np.array([0], dtype=np.int8)])
    node.inputs["in_0"].dispatch([np.array([1.0], dtype=np.float32)])
    assert len(results) == 1

    # Switch to input 1
    node.inputs["index"].dispatch([np.array([1], dtype=np.int8)])
    node.inputs["in_0"].dispatch([np.array([2.0], dtype=np.float32)])
    assert len(results) == 1  # in_0 ignored now

    node.inputs["in_1"].dispatch([np.array([3.0], dtype=np.float32)])
    assert len(results) == 2
    np.testing.assert_array_equal(results[1][0], np.array([3.0], dtype=np.float32))


def test_values_gate_set_properties_input_count():
    node = ValuesGateNode("test")
    node.set_properties({"input_count": 4})

    assert len([k for k in node.inputs if k.startswith("in_")]) == 4

    results = []
    node.outputs["out"].subscribe(0, lambda v: results.append(v))
    node.inputs["index"].dispatch([np.array([3], dtype=np.int8)])
    node.inputs["in_3"].dispatch([np.array([99.0], dtype=np.float32)])

    assert len(results) == 1


def test_values_gate_set_properties_value_type():
    node = ValuesGateNode("test")
    node.set_properties({"value_type_list": "i32"})

    results = []
    node.outputs["out"].subscribe(0, lambda v: results.append(v))
    node.inputs["index"].dispatch([np.array([0], dtype=np.int8)])
    node.inputs["in_0"].dispatch([np.array([7], dtype=np.int32)])

    assert len(results) == 1
    assert results[0][0].dtype == np.int32


def test_values_gate_set_properties_input_count_less_than_one_raises():
    node = ValuesGateNode("test")
    with pytest.raises(ValueError):
        node.set_properties({"input_count": 0})


# ---------------------------------------------------------------------------
# TransitionNode
# ---------------------------------------------------------------------------


def _make_transition(target: str) -> TransitionNode:
    node = TransitionNode("test")
    node.set_properties({"target": target})
    return node


def _str_array(values):
    return np.array(values, dtype=np.dtypes.StringDType())  # type: ignore[call-arg]


def test_transition_port_structure():
    node = TransitionNode("test")
    assert "current" in node.inputs
    assert "enter" in node.outputs
    assert "exit" in node.outputs


def test_transition_set_properties_target():
    node = TransitionNode("test")
    node.set_properties({"target": "session_active"})
    assert node.properties["target"] == "session_active"


def test_transition_set_properties_target_non_string_raises():
    node = TransitionNode("test")
    with pytest.raises(ValueError):
        node.set_properties({"target": 42})


def test_transition_enter_fires_when_current_becomes_target():
    node = _make_transition("waiting")
    enter_results = []
    exit_results = []
    node.outputs["enter"].subscribe(0, lambda v: enter_results.append(v))
    node.outputs["exit"].subscribe(0, lambda v: exit_results.append(v))

    node.inputs["current"].dispatch([_str_array(["waiting"])])

    assert len(enter_results) == 1
    assert enter_results[0][0][0] == True  # noqa: E712
    assert len(exit_results) == 0


def test_transition_exit_fires_when_current_leaves_target():
    node = _make_transition("waiting")
    enter_results = []
    exit_results = []
    node.outputs["enter"].subscribe(0, lambda v: enter_results.append(v))
    node.outputs["exit"].subscribe(0, lambda v: exit_results.append(v))

    node.inputs["current"].dispatch([_str_array(["waiting"])])
    node.inputs["current"].dispatch([_str_array(["briefing"])])

    assert len(enter_results) == 1
    assert len(exit_results) == 1


def test_transition_no_pulse_when_state_unchanged_off_target():
    node = _make_transition("waiting")
    enter_results = []
    exit_results = []
    node.outputs["enter"].subscribe(0, lambda v: enter_results.append(v))
    node.outputs["exit"].subscribe(0, lambda v: exit_results.append(v))

    node.inputs["current"].dispatch([_str_array(["briefing"])])
    node.inputs["current"].dispatch([_str_array(["briefing"])])

    assert len(enter_results) == 0
    assert len(exit_results) == 0


def test_transition_no_pulse_when_state_unchanged_on_target():
    node = _make_transition("waiting")
    enter_results = []
    exit_results = []
    node.outputs["enter"].subscribe(0, lambda v: enter_results.append(v))
    node.outputs["exit"].subscribe(0, lambda v: exit_results.append(v))

    node.inputs["current"].dispatch([_str_array(["waiting"])])
    node.inputs["current"].dispatch([_str_array(["waiting"])])

    assert len(enter_results) == 1
    assert len(exit_results) == 0


def test_transition_initial_non_target_input_emits_nothing():
    node = _make_transition("waiting")
    enter_results = []
    exit_results = []
    node.outputs["enter"].subscribe(0, lambda v: enter_results.append(v))
    node.outputs["exit"].subscribe(0, lambda v: exit_results.append(v))

    node.inputs["current"].dispatch([_str_array(["briefing"])])

    assert len(enter_results) == 0
    assert len(exit_results) == 0


def test_transition_batch_traces_each_intermediate_transition():
    """A batched input array carrying [waiting, briefing, waiting] must emit
    enter, exit, enter in that order. Reading only the latest element would
    miss the intermediate exit (cleanup) and the second enter (re-start).
    """
    node = _make_transition("waiting")
    enter_results = []
    exit_results = []
    node.outputs["enter"].subscribe(0, lambda v: enter_results.append(v))
    node.outputs["exit"].subscribe(0, lambda v: exit_results.append(v))

    node.inputs["current"].dispatch(
        [_str_array(["waiting", "briefing", "waiting"])]
    )

    assert len(enter_results) == 2
    assert len(exit_results) == 1


def test_transition_batch_starting_off_target_then_entering():
    """[briefing, waiting] should emit one enter and no exit."""
    node = _make_transition("waiting")
    enter_results = []
    exit_results = []
    node.outputs["enter"].subscribe(0, lambda v: enter_results.append(v))
    node.outputs["exit"].subscribe(0, lambda v: exit_results.append(v))

    node.inputs["current"].dispatch([_str_array(["briefing", "waiting"])])

    assert len(enter_results) == 1
    assert len(exit_results) == 0


def test_transition_batch_collapses_duplicate_states():
    """[waiting, waiting, briefing] should emit one enter and one exit (not
    two enters from the duplicate sample).
    """
    node = _make_transition("waiting")
    enter_results = []
    exit_results = []
    node.outputs["enter"].subscribe(0, lambda v: enter_results.append(v))
    node.outputs["exit"].subscribe(0, lambda v: exit_results.append(v))

    node.inputs["current"].dispatch(
        [_str_array(["waiting", "waiting", "briefing"])]
    )

    assert len(enter_results) == 1
    assert len(exit_results) == 1


def test_transition_reentrancy_safe():
    """If a subscriber on `enter` synchronously dispatches a new value into
    `current`, the outer call's view of _prev_state must not be corrupted.
    The 3-phase pattern (compute -> commit -> dispatch) guarantees that
    reentrant calls see the post-batch state, not an in-flight intermediate.
    """
    node = _make_transition("waiting")
    enter_results = []
    exit_results = []
    reentry_done = [False]

    def reentrant_subscriber(v):
        enter_results.append(v)
        # On the first enter pulse, recursively feed a new state into the
        # same node. This is the feedback scenario the 3-phase pattern
        # must tolerate.
        if not reentry_done[0]:
            reentry_done[0] = True
            node.inputs["current"].dispatch([_str_array(["briefing"])])

    node.outputs["enter"].subscribe(0, reentrant_subscriber)
    node.outputs["exit"].subscribe(0, lambda v: exit_results.append(v))

    # Outer call dispatches waiting → enter fires → reentry dispatches
    # briefing → exit fires (because _prev_state was committed to "waiting"
    # before the dispatch, so briefing now counts as a real exit).
    node.inputs["current"].dispatch([_str_array(["waiting"])])

    assert len(enter_results) == 1
    assert len(exit_results) == 1
    # Final state should reflect the reentrant dispatch's value.
    assert node._prev_state == "briefing"


# ---------------------------------------------------------------------------
# BoolEdgeNode
# ---------------------------------------------------------------------------


def _bool_array(values):
    return np.array(values, dtype=np.bool_)


def test_bool_edge_port_structure():
    node = BoolEdgeNode("test")
    assert "value" in node.inputs
    assert "rising" in node.outputs
    assert "falling" in node.outputs


def test_bool_edge_first_true_sample_no_emit():
    """Cold-boot with first sample = True: registers state, no edge."""
    node = BoolEdgeNode("test")
    rising = []
    falling = []
    node.outputs["rising"].subscribe(0, lambda v: rising.append(v))
    node.outputs["falling"].subscribe(0, lambda v: falling.append(v))

    node.inputs["value"].dispatch([_bool_array([True])])

    assert len(rising) == 0
    assert len(falling) == 0
    assert node._prev is True


def test_bool_edge_first_false_sample_no_emit():
    """Cold-boot with first sample = False: registers state, no edge."""
    node = BoolEdgeNode("test")
    rising = []
    falling = []
    node.outputs["rising"].subscribe(0, lambda v: rising.append(v))
    node.outputs["falling"].subscribe(0, lambda v: falling.append(v))

    node.inputs["value"].dispatch([_bool_array([False])])

    assert len(rising) == 0
    assert len(falling) == 0
    assert node._prev is False


def test_bool_edge_rising_only_on_false_to_true():
    node = BoolEdgeNode("test")
    rising = []
    falling = []
    node.outputs["rising"].subscribe(0, lambda v: rising.append(v))
    node.outputs["falling"].subscribe(0, lambda v: falling.append(v))

    node.inputs["value"].dispatch([_bool_array([False])])
    node.inputs["value"].dispatch([_bool_array([True])])

    assert len(rising) == 1
    assert rising[0][0][0] == True  # noqa: E712
    assert len(falling) == 0


def test_bool_edge_falling_only_on_true_to_false():
    node = BoolEdgeNode("test")
    rising = []
    falling = []
    node.outputs["rising"].subscribe(0, lambda v: rising.append(v))
    node.outputs["falling"].subscribe(0, lambda v: falling.append(v))

    node.inputs["value"].dispatch([_bool_array([True])])
    node.inputs["value"].dispatch([_bool_array([False])])

    assert len(rising) == 0
    assert len(falling) == 1
    assert falling[0][0][0] == True  # noqa: E712


def test_bool_edge_alternating_transitions_preserve_order():
    """true → false → true should emit falling then rising in source order."""
    node = BoolEdgeNode("test")
    events = []  # list of ("rising" | "falling", index)
    node.outputs["rising"].subscribe(0, lambda v: events.append("rising"))
    node.outputs["falling"].subscribe(0, lambda v: events.append("falling"))

    node.inputs["value"].dispatch([_bool_array([True])])    # init prev=True
    node.inputs["value"].dispatch([_bool_array([False])])   # falling
    node.inputs["value"].dispatch([_bool_array([True])])    # rising

    assert events == ["falling", "rising"]


def test_bool_edge_batch_alternating_preserves_order():
    """Single dispatch [F, T, F, T] from prev=T emits falling, rising,
    falling, rising in source order."""
    node = BoolEdgeNode("test")
    events = []
    node.outputs["rising"].subscribe(0, lambda v: events.append("rising"))
    node.outputs["falling"].subscribe(0, lambda v: events.append("falling"))

    # Initialize prev to True with a single-sample batch.
    node.inputs["value"].dispatch([_bool_array([True])])
    assert events == []

    node.inputs["value"].dispatch(
        [_bool_array([False, True, False, True])]
    )

    assert events == ["falling", "rising", "falling", "rising"]


def test_bool_edge_batch_cold_boot_no_transitions_in_constant_batch():
    """Cold-boot dispatch of [T, T] registers prev=True but emits nothing."""
    node = BoolEdgeNode("test")
    rising = []
    falling = []
    node.outputs["rising"].subscribe(0, lambda v: rising.append(v))
    node.outputs["falling"].subscribe(0, lambda v: falling.append(v))

    node.inputs["value"].dispatch([_bool_array([True, True])])

    assert len(rising) == 0
    assert len(falling) == 0
    assert node._prev is True


def test_bool_edge_batch_cold_boot_rising_within_batch():
    """Cold-boot dispatch of [F, F, T] emits a single rising for F → T."""
    node = BoolEdgeNode("test")
    rising = []
    falling = []
    node.outputs["rising"].subscribe(0, lambda v: rising.append(v))
    node.outputs["falling"].subscribe(0, lambda v: falling.append(v))

    node.inputs["value"].dispatch([_bool_array([False, False, True])])

    assert len(rising) == 1
    assert len(falling) == 0
    assert node._prev is True


def test_bool_edge_constant_sequence_no_pulses():
    """Multiple consecutive equal values must not emit any pulse."""
    node = BoolEdgeNode("test")
    rising = []
    falling = []
    node.outputs["rising"].subscribe(0, lambda v: rising.append(v))
    node.outputs["falling"].subscribe(0, lambda v: falling.append(v))

    for _ in range(3):
        node.inputs["value"].dispatch([_bool_array([True])])

    assert len(rising) == 0
    assert len(falling) == 0


def test_bool_edge_empty_batch_no_emit():
    """An empty bool array should be a no-op (no state change, no emit)."""
    node = BoolEdgeNode("test")
    rising = []
    falling = []
    node.outputs["rising"].subscribe(0, lambda v: rising.append(v))
    node.outputs["falling"].subscribe(0, lambda v: falling.append(v))

    node.inputs["value"].dispatch([_bool_array([])])

    assert len(rising) == 0
    assert len(falling) == 0
    assert node._prev is None


def test_bool_edge_reentrancy_safe():
    """If a subscriber on `rising` synchronously dispatches a new value
    into `value`, the outer call's _prev must not be corrupted. The
    3-phase pattern guarantees reentrant calls see the post-batch
    state.
    """
    node = BoolEdgeNode("test")
    rising = []
    falling = []
    reentry_done = [False]

    def reentrant_rising(v):
        rising.append(v)
        if not reentry_done[0]:
            reentry_done[0] = True
            # During the dispatch of the first rising pulse, feed a
            # new value back into this node's input. With the 3-phase
            # pattern, self._prev is already committed to True before
            # this dispatch fires, so the new False value will produce
            # a proper falling pulse.
            node.inputs["value"].dispatch([_bool_array([False])])

    node.outputs["rising"].subscribe(0, reentrant_rising)
    node.outputs["falling"].subscribe(0, lambda v: falling.append(v))

    # Initialize prev to False with a single-sample batch (cold-boot).
    node.inputs["value"].dispatch([_bool_array([False])])

    # Now dispatch True → rising fires → reentry dispatches False
    # → falling fires.
    node.inputs["value"].dispatch([_bool_array([True])])

    assert len(rising) == 1
    assert len(falling) == 1
    # _prev should reflect the reentrant dispatch's final value.
    assert node._prev is False
