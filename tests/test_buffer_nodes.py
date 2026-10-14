import numpy as np
import pytest
from nonoha_core.nodes.buffer_nodes import ValuesBufferNode, ValuesRingBufferNode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(size=8, value_types="f32,f32", reset_on_flush=True,
               flush_on_full=False, dispatch_empty=False):
    """Create a ValuesBufferNode with captured outputs."""
    node = ValuesBufferNode("test")
    node.set_properties({
        "size": size,
        "value_type_list": value_types,
        "reset_on_flush": reset_on_flush,
        "flush_on_full": flush_on_full,
        "dispatch_empty": dispatch_empty,
    })

    values_out = []
    node.outputs["values"].subscribe(1, lambda v: values_out.append([arr.copy() for arr in v]))

    return node, values_out


def _dispatch_values(node, *arrays):
    node.inputs["values"].dispatch(list(arrays))


def _flush(node):
    node.inputs["flush"].dispatch([np.array([1], dtype=np.int32)])


def _reset(node):
    node.inputs["reset"].dispatch([np.array([1], dtype=np.int32)])


# ---------------------------------------------------------------------------
# Basic buffering + flush
# ---------------------------------------------------------------------------

def test_basic_buffer_and_flush():
    """Input values are accumulated and output on flush."""
    node, values_out = _make_node(size=8)

    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )
    _dispatch_values(node,
        np.array([3.0], dtype=np.float32),
        np.array([30.0], dtype=np.float32),
    )

    # No output yet (no flush)
    assert len(values_out) == 0

    _flush(node)

    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0, 3.0])
    np.testing.assert_array_equal(values_out[0][1], [10.0, 20.0, 30.0])


def test_flush_empty_buffer():
    """Flushing an empty buffer outputs nothing (dispatch_empty=False)."""
    node, values_out = _make_node(size=8)

    _flush(node)

    assert len(values_out) == 0


# ---------------------------------------------------------------------------
# reset_on_flush
# ---------------------------------------------------------------------------

def test_reset_on_flush_true():
    """With reset_on_flush=True (default), buffer clears after flush."""
    node, values_out = _make_node(size=8, reset_on_flush=True)

    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )
    _flush(node)

    assert len(values_out) == 1

    # Second flush should be empty
    _flush(node)
    assert len(values_out) == 1  # no new dispatch


def test_reset_on_flush_false():
    """With reset_on_flush=False, buffer retains data after flush."""
    node, values_out = _make_node(size=8, reset_on_flush=False)

    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )
    _flush(node)

    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0])

    # Second flush outputs the same data
    _flush(node)
    assert len(values_out) == 2
    np.testing.assert_array_equal(values_out[1][0], [1.0, 2.0])


def test_reset_on_flush_false_accumulates():
    """With reset_on_flush=False, new data appends to existing buffer."""
    node, values_out = _make_node(size=8, reset_on_flush=False)

    _dispatch_values(node,
        np.array([1.0], dtype=np.float32),
        np.array([10.0], dtype=np.float32),
    )
    _flush(node)
    assert len(values_out) == 1

    _dispatch_values(node,
        np.array([2.0], dtype=np.float32),
        np.array([20.0], dtype=np.float32),
    )
    _flush(node)
    assert len(values_out) == 2
    np.testing.assert_array_equal(values_out[1][0], [1.0, 2.0])


# ---------------------------------------------------------------------------
# Reset input
# ---------------------------------------------------------------------------

def test_reset_clears_buffer():
    """Reset input clears the buffer."""
    node, values_out = _make_node(size=8)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )
    _reset(node)
    _flush(node)

    assert len(values_out) == 0


# ---------------------------------------------------------------------------
# flush_on_full
# ---------------------------------------------------------------------------

def test_flush_on_full_exact():
    """flush_on_full=True triggers auto-flush when buffer is exactly full."""
    node, values_out = _make_node(size=4, flush_on_full=True)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32),
    )

    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0, 3.0, 4.0])


def test_flush_on_full_incremental():
    """flush_on_full=True triggers when buffer fills over multiple dispatches."""
    node, values_out = _make_node(size=4, flush_on_full=True)

    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )
    assert len(values_out) == 0  # Not full yet

    _dispatch_values(node,
        np.array([3.0, 4.0], dtype=np.float32),
        np.array([30.0, 40.0], dtype=np.float32),
    )
    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0, 3.0, 4.0])


def test_flush_on_full_resets_buffer():
    """After flush_on_full auto-flush, buffer resets for new data."""
    node, values_out = _make_node(size=3, flush_on_full=True)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )
    assert len(values_out) == 1

    # Next batch goes into fresh buffer
    _dispatch_values(node,
        np.array([4.0, 5.0], dtype=np.float32),
        np.array([40.0, 50.0], dtype=np.float32),
    )
    _flush(node)

    assert len(values_out) == 2
    np.testing.assert_array_equal(values_out[1][0], [4.0, 5.0])


def test_flush_on_full_large_input():
    """Input larger than buffer size triggers multiple auto-flushes."""
    node, values_out = _make_node(size=3, flush_on_full=True)

    # 7 elements with buffer size 3: should produce 2 full flushes + 1 leftover
    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0], dtype=np.float32),
    )

    # 2 full flushes (3 + 3), remaining 1 element stays in buffer
    assert len(values_out) == 2
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0, 3.0])
    np.testing.assert_array_equal(values_out[1][0], [4.0, 5.0, 6.0])

    # Manual flush to get the remaining element
    _flush(node)
    assert len(values_out) == 3
    np.testing.assert_array_equal(values_out[2][0], [7.0])


def test_flush_on_full_large_input_exact_multiple():
    """Input exactly N*buffer_size triggers N flushes with empty remainder."""
    node, values_out = _make_node(size=3, flush_on_full=True)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0], dtype=np.float32),
    )

    assert len(values_out) == 2
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0, 3.0])
    np.testing.assert_array_equal(values_out[1][0], [4.0, 5.0, 6.0])

    # No leftover
    _flush(node)
    assert len(values_out) == 2  # no new dispatch


# ---------------------------------------------------------------------------
# Overflow without flush_on_full (sliding window behavior)
# ---------------------------------------------------------------------------

def test_overflow_keeps_latest():
    """Without flush_on_full, overflow retains latest `size` elements."""
    node, values_out = _make_node(size=4, flush_on_full=False)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0], dtype=np.float32),
    )
    _flush(node)

    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [3.0, 4.0, 5.0, 6.0])
    np.testing.assert_array_equal(values_out[0][1], [30.0, 40.0, 50.0, 60.0])


def test_overflow_incremental():
    """Incremental overflow slides buffer to keep latest elements."""
    node, values_out = _make_node(size=4, flush_on_full=False)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )
    _dispatch_values(node,
        np.array([4.0, 5.0, 6.0], dtype=np.float32),
        np.array([40.0, 50.0, 60.0], dtype=np.float32),
    )
    _flush(node)

    assert len(values_out[0][0]) == 4
    np.testing.assert_array_equal(values_out[0][0], [3.0, 4.0, 5.0, 6.0])


def test_overflow_massive_input():
    """Input much larger than buffer keeps only last `size` elements."""
    node, values_out = _make_node(size=3, flush_on_full=False)

    data = np.arange(100, dtype=np.float32)
    _dispatch_values(node, data, data * 10)
    _flush(node)

    assert len(values_out[0][0]) == 3
    np.testing.assert_array_equal(values_out[0][0], [97.0, 98.0, 99.0])


# ---------------------------------------------------------------------------
# Lazy buffer initialization (dtype / shape)
# ---------------------------------------------------------------------------

def test_lazy_init_int32():
    """Buffer dtype is initialized from first input."""
    node, values_out = _make_node(size=8, value_types="i32,i32")

    _dispatch_values(node,
        np.array([100, 200], dtype=np.int32),
        np.array([1, 2], dtype=np.int32),
    )
    _flush(node)

    assert values_out[0][0].dtype == np.int32
    np.testing.assert_array_equal(values_out[0][0], [100, 200])


def test_lazy_init_uint8():
    """Buffer dtype u8."""
    node, values_out = _make_node(size=8, value_types="u8")

    _dispatch_values(node, np.array([255, 0, 128], dtype=np.uint8))
    _flush(node)

    assert values_out[0][0].dtype == np.uint8
    np.testing.assert_array_equal(values_out[0][0], [255, 0, 128])


# ---------------------------------------------------------------------------
# Multi-value (multiple slots)
# ---------------------------------------------------------------------------

def test_multi_value_three_slots():
    """Three-slot multi-value buffer."""
    node, values_out = _make_node(size=4, value_types="f32,i32,u8")

    _dispatch_values(node,
        np.array([1.5, 2.5], dtype=np.float32),
        np.array([10, 20], dtype=np.int32),
        np.array([0, 255], dtype=np.uint8),
    )
    _flush(node)

    assert len(values_out[0]) == 3
    np.testing.assert_array_equal(values_out[0][0], [1.5, 2.5])
    np.testing.assert_array_equal(values_out[0][1], [10, 20])
    np.testing.assert_array_equal(values_out[0][2], [0, 255])


def test_multi_value_length_mismatch():
    """Arrays with mismatched lengths are rejected (no buffering)."""
    node, values_out = _make_node(size=8)

    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0], dtype=np.float32),  # length mismatch
    )
    _flush(node)

    assert len(values_out) == 0


# ---------------------------------------------------------------------------
# Single-value type
# ---------------------------------------------------------------------------

def test_single_value_type():
    """Node works with a single value type."""
    node, values_out = _make_node(size=4, value_types="f64")

    _dispatch_values(node, np.array([1.1, 2.2, 3.3], dtype=np.float64))
    _flush(node)

    assert values_out[0][0].dtype == np.float64
    np.testing.assert_array_almost_equal(values_out[0][0], [1.1, 2.2, 3.3])


# ---------------------------------------------------------------------------
# Property: size change resets buffer
# ---------------------------------------------------------------------------

def test_size_change_resets_buffer():
    """Changing size via set_properties clears the buffer."""
    node, values_out = _make_node(size=8)

    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )

    node.set_properties({"size": 16})

    _flush(node)
    assert len(values_out) == 0


def test_size_validation():
    """Size must be >= 1."""
    node, _ = _make_node(size=8)
    with pytest.raises(ValueError, match="size must be greater than 0"):
        node.set_properties({"size": 0})


# ---------------------------------------------------------------------------
# Property: value_type_list change resets buffer
# ---------------------------------------------------------------------------

def test_value_type_change_resets_buffer():
    """Changing value_type_list resets internal buffer."""
    node, values_out = _make_node(size=8, value_types="f32,f32")

    _dispatch_values(node,
        np.array([1.0], dtype=np.float32),
        np.array([2.0], dtype=np.float32),
    )

    node.set_properties({"value_type_list": "i32,i32"})

    # Need to re-subscribe since output port is replaced
    values_out.clear()
    node.outputs["values"].subscribe(1, lambda v: values_out.append([a.copy() for a in v]))

    _flush(node)
    assert len(values_out) == 0


# ---------------------------------------------------------------------------
# Flush + reset interaction
# ---------------------------------------------------------------------------

def test_flush_then_reset_then_flush():
    """Reset after flush clears everything."""
    node, values_out = _make_node(size=8, reset_on_flush=False)

    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )
    _flush(node)
    assert len(values_out) == 1

    _reset(node)
    _flush(node)
    assert len(values_out) == 1  # no new dispatch


# ---------------------------------------------------------------------------
# flush_on_full with reset_on_flush=False
# ---------------------------------------------------------------------------

def test_flush_on_full_no_reset():
    """flush_on_full=True with reset_on_flush=False: auto-flush does NOT reset."""
    node, values_out = _make_node(
        size=4, flush_on_full=True, reset_on_flush=False,
    )

    # Batch fills buffer exactly → auto-flush
    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32),
    )

    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0, 3.0, 4.0])
    np.testing.assert_array_equal(values_out[0][1], [10.0, 20.0, 30.0, 40.0])

    # Buffer NOT reset → overflow causes sliding window + auto-flush
    _dispatch_values(node,
        np.array([5.0, 6.0], dtype=np.float32),
        np.array([50.0, 60.0], dtype=np.float32),
    )

    # Post-shift dispatch: [3,4,5,6]
    assert len(values_out) == 2
    np.testing.assert_array_equal(values_out[1][0], [3.0, 4.0, 5.0, 6.0])
    np.testing.assert_array_equal(values_out[1][1], [30.0, 40.0, 50.0, 60.0])

    # Manual flush returns same buffer (no new data since last dispatch)
    _flush(node)
    assert len(values_out) == 3
    np.testing.assert_array_equal(values_out[2][0], [3.0, 4.0, 5.0, 6.0])


def test_flush_on_full_no_reset_incremental():
    """flush_on_full=True, reset_on_flush=False: single-element sequential input
    produces correct sliding-window dispatches (no 1-sample delay)."""
    node, values_out = _make_node(
        size=4, value_types="f32", flush_on_full=True, reset_on_flush=False,
    )

    # Fill buffer: 1, 2, 3 — no dispatch yet
    for v in [1.0, 2.0, 3.0]:
        _dispatch_values(node, np.array([v], dtype=np.float32))
    assert len(values_out) == 0

    # 4th element fills buffer → dispatch [1,2,3,4]
    _dispatch_values(node, np.array([4.0], dtype=np.float32))
    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0, 3.0, 4.0])

    # 5th element: buffer full → shift+write → dispatch [2,3,4,5]
    _dispatch_values(node, np.array([5.0], dtype=np.float32))
    assert len(values_out) == 2
    np.testing.assert_array_equal(values_out[1][0], [2.0, 3.0, 4.0, 5.0])

    # 6th element: shift+write → dispatch [3,4,5,6]
    _dispatch_values(node, np.array([6.0], dtype=np.float32))
    assert len(values_out) == 3
    np.testing.assert_array_equal(values_out[2][0], [3.0, 4.0, 5.0, 6.0])


# ---------------------------------------------------------------------------
# In-place update
# ---------------------------------------------------------------------------

def _inplace_update(node, positions, *arrays):
    """Scatter write. positions and each value array must have same length."""
    node.inputs["inplace_update"].dispatch(
        [np.asarray(positions, dtype=np.int32), *list(arrays)]
    )


def test_inplace_update_basic():
    """Scatter write at specific positions."""
    node, values_out = _make_node(size=8)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32),
    )

    # Scatter: buffer[1]=99, buffer[2]=88
    _inplace_update(node, [1, 2],
        np.array([99.0, 88.0], dtype=np.float32),
        np.array([990.0, 880.0], dtype=np.float32),
    )

    _flush(node)

    np.testing.assert_array_equal(values_out[0][0], [1.0, 99.0, 88.0, 4.0])
    np.testing.assert_array_equal(values_out[0][1], [10.0, 990.0, 880.0, 40.0])


def test_inplace_update_partial_out_of_range():
    """Some positions out of range are skipped, valid ones still written."""
    node, values_out = _make_node(size=4)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32),
    )

    # positions: 1 (valid), 4 (out of range), -1 (negative)
    _inplace_update(node, [1, 4, -1],
        np.array([99.0, 88.0, 77.0], dtype=np.float32),
        np.array([990.0, 880.0, 770.0], dtype=np.float32),
    )

    _flush(node)

    # Only position 1 was written
    np.testing.assert_array_equal(values_out[0][0], [1.0, 99.0, 3.0, 4.0])
    np.testing.assert_array_equal(values_out[0][1], [10.0, 990.0, 30.0, 40.0])


def test_inplace_update_position_out_of_range():
    """All positions out of range → no writes."""
    node, values_out = _make_node(size=4)

    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )

    _inplace_update(node, [4, -1],
        np.array([99.0, 88.0], dtype=np.float32),
        np.array([990.0, 880.0], dtype=np.float32),
    )

    _flush(node)

    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0])
    np.testing.assert_array_equal(values_out[0][1], [10.0, 20.0])


def test_inplace_update_no_buffer_index_change():
    """Scatter write beyond buffer_index does not extend flush output."""
    node, values_out = _make_node(size=8)

    # Buffer 2 values → buffer_index = 2
    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )

    # Write at position 5 (beyond buffer_index=2) → buffer_index stays 2
    _inplace_update(node, [5],
        np.array([99.0], dtype=np.float32),
        np.array([990.0], dtype=np.float32),
    )

    _flush(node)

    assert len(values_out[0][0]) == 2
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0])


def test_inplace_update_duplicate_positions():
    """Duplicate positions → last value wins (numpy fancy indexing behavior)."""
    node, values_out = _make_node(size=4)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32),
    )

    # Position 1 appears twice → last value (88.0) wins
    _inplace_update(node, [1, 1],
        np.array([99.0, 88.0], dtype=np.float32),
        np.array([990.0, 880.0], dtype=np.float32),
    )

    _flush(node)

    np.testing.assert_array_equal(values_out[0][0], [1.0, 88.0, 3.0, 4.0])
    np.testing.assert_array_equal(values_out[0][1], [10.0, 880.0, 30.0, 40.0])


def test_inplace_update_skip_none_buffer():
    """Inplace update on uninitialized buffer (None) is silently skipped."""
    node, values_out = _make_node(size=8)

    # No _on_values dispatch yet → buffer is [None, None]
    _inplace_update(node, [0, 1],
        np.array([5.0, 6.0], dtype=np.float32),
        np.array([50.0, 60.0], dtype=np.float32),
    )

    # buffer_index is 0, flush outputs nothing
    _flush(node)
    assert len(values_out) == 0


def test_inplace_update_empty_slot_skip():
    """Empty value array skips that slot, only updates non-empty slots."""
    node, values_out = _make_node(size=4, value_types="f32,f32,f32")

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32),
        np.array([100.0, 200.0, 300.0, 400.0], dtype=np.float32),
    )

    # Update only slot 2 (positions 0,1), skip slots 0 and 1 with empty arrays
    _inplace_update(node, [0, 1],
        np.array([], dtype=np.float32),
        np.array([], dtype=np.float32),
        np.array([999.0, 888.0], dtype=np.float32),
    )

    _flush(node)

    # Slot 0 and 1 unchanged
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0, 3.0, 4.0])
    np.testing.assert_array_equal(values_out[0][1], [10.0, 20.0, 30.0, 40.0])
    # Slot 2 updated at positions 0,1
    np.testing.assert_array_equal(values_out[0][2], [999.0, 888.0, 300.0, 400.0])


# ---------------------------------------------------------------------------
# Shift
# ---------------------------------------------------------------------------

def _shift(node, counts):
    node.inputs["shift"].dispatch([np.asarray(counts, dtype=np.int32)])


def test_shift_basic():
    """Shift N samples from the front of the buffer."""
    node, values_out = _make_node(size=8)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0, 50.0], dtype=np.float32),
    )

    _shift(node, [3])

    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0, 3.0])
    np.testing.assert_array_equal(values_out[0][1], [10.0, 20.0, 30.0])

    # Remaining [4,5] should be in buffer
    _flush(node)
    assert len(values_out) == 2
    np.testing.assert_array_equal(values_out[1][0], [4.0, 5.0])
    np.testing.assert_array_equal(values_out[1][1], [40.0, 50.0])


def test_shift_more_than_available():
    """Shift request larger than buffer → clamped to available."""
    node, values_out = _make_node(size=8)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )

    _shift(node, [5])

    assert len(values_out) == 1
    assert len(values_out[0][0]) == 3  # clamped
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0, 3.0])

    # Buffer should be empty
    _flush(node)
    assert len(values_out) == 1  # no new dispatch


def test_shift_empty_buffer():
    """Shift on empty buffer → no dispatch (dispatch_empty=False)."""
    node, values_out = _make_node(size=8)

    _shift(node, [3])

    assert len(values_out) == 0


def test_shift_zero_count():
    """Shift of 0 → no dispatch (dispatch_empty=False)."""
    node, values_out = _make_node(size=8)

    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )

    _shift(node, [0])

    assert len(values_out) == 0

    # Buffer unchanged
    _flush(node)
    assert len(values_out) == 1
    assert len(values_out[0][0]) == 2


def test_shift_batch():
    """Batch shift [2,3] → two dispatches."""
    node, values_out = _make_node(size=8)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0], dtype=np.float32),
    )

    _shift(node, [2, 3])

    assert len(values_out) == 2

    # First shift: 2 samples
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0])

    # Second shift: 3 samples
    np.testing.assert_array_equal(values_out[1][0], [3.0, 4.0, 5.0])

    # Remaining [6,7]
    _flush(node)
    assert len(values_out) == 3
    np.testing.assert_array_equal(values_out[2][0], [6.0, 7.0])


def test_shift_exhausts_buffer():
    """Shift exactly all samples → buffer empty, then add more."""
    node, values_out = _make_node(size=8)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )

    _shift(node, [3])
    assert len(values_out) == 1

    # Buffer is now empty
    _flush(node)
    assert len(values_out) == 1  # no new dispatch

    # Can still add new data
    _dispatch_values(node,
        np.array([4.0, 5.0], dtype=np.float32),
        np.array([40.0, 50.0], dtype=np.float32),
    )
    _flush(node)
    assert len(values_out) == 2
    np.testing.assert_array_equal(values_out[1][0], [4.0, 5.0])


def test_shift_then_values_then_flush():
    """Shift partial, add more values, flush → correct state."""
    node, values_out = _make_node(size=8)

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32),
    )

    _shift(node, [2])  # Remove [1,2], keep [3,4]

    _dispatch_values(node,
        np.array([5.0, 6.0], dtype=np.float32),
        np.array([50.0, 60.0], dtype=np.float32),
    )

    _flush(node)

    # shift output
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0])

    # flush output: remaining [3,4] + new [5,6]
    np.testing.assert_array_equal(values_out[1][0], [3.0, 4.0, 5.0, 6.0])


def test_shift_multi_slot():
    """Shift with multiple value types (f32, i32)."""
    node, values_out = _make_node(size=8, value_types="f32,i32")

    _dispatch_values(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10, 20, 30], dtype=np.int32),
    )

    _shift(node, [2])

    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [1.0, 2.0])
    np.testing.assert_array_equal(values_out[0][1], [10, 20])
    assert values_out[0][0].dtype == np.float32
    assert values_out[0][1].dtype == np.int32

    # Remaining
    _flush(node)
    np.testing.assert_array_equal(values_out[1][0], [3.0])
    np.testing.assert_array_equal(values_out[1][1], [30])


# ---------------------------------------------------------------------------
# dispatch_empty
# ---------------------------------------------------------------------------

def test_dispatch_empty_flush():
    """dispatch_empty=True, empty flush → values dispatched with empty arrays."""
    node, values_out = _make_node(size=8, dispatch_empty=True)

    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )
    _flush(node)  # has data
    assert len(values_out) == 1
    assert len(values_out[0][0]) == 2

    _flush(node)  # empty (reset_on_flush=True)
    assert len(values_out) == 2
    assert len(values_out[1][0]) == 0
    assert values_out[1][0].dtype == np.float32


def test_dispatch_empty_flush_no_data():
    """dispatch_empty=True, flush without any data received → empty arrays with correct dtype."""
    node, values_out = _make_node(size=8, value_types="f32,i32", dispatch_empty=True)

    _flush(node)

    assert len(values_out) == 1
    assert len(values_out[0][0]) == 0
    assert len(values_out[0][1]) == 0
    assert values_out[0][0].dtype == np.float32
    assert values_out[0][1].dtype == np.int32


def test_dispatch_empty_shift():
    """dispatch_empty=True, shift on empty → values dispatched with empty arrays."""
    node, values_out = _make_node(size=8, dispatch_empty=True)

    _dispatch_values(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )

    # Shift all, then shift again (empty)
    _shift(node, [2])
    assert len(values_out) == 1

    _shift(node, [1])
    assert len(values_out) == 2
    assert len(values_out[1][0]) == 0


def test_dispatch_empty_default_no_fire():
    """dispatch_empty=False (default), empty flush → no dispatch."""
    node, values_out = _make_node(size=8)

    _flush(node)

    assert len(values_out) == 0


# ---------------------------------------------------------------------------
# value_type_list validation
# ---------------------------------------------------------------------------

def test_value_type_any_rejected():
    """DataType.Any is not allowed for buffer value types."""
    node, _ = _make_node(size=8)
    with pytest.raises(ValueError, match="DataType.Any"):
        node.set_properties({"value_type_list": "any"})


def test_value_type_variable_shape_rejected():
    """Variable dimensions (-1) are not allowed for buffer value types."""
    node, _ = _make_node(size=8)
    with pytest.raises(ValueError, match="Variable dimensions"):
        node.set_properties({"value_type_list": "f32[N]"})


def test_dispatch_empty_shape_preserved():
    """dispatch_empty=True with shaped type → empty arrays have correct shape."""
    node, values_out = _make_node(size=4, value_types="f32[3]", dispatch_empty=True)

    _flush(node)

    assert len(values_out) == 1
    assert values_out[0][0].shape == (0, 3)
    assert values_out[0][0].dtype == np.float32


# ===========================================================================
# ValuesRingBufferNode tests
# ===========================================================================

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ring_node(size=4, value_types="f32,f32"):
    """Create a ValuesRingBufferNode with captured outputs."""
    node = ValuesRingBufferNode("test_ring")
    node.set_properties({"size": size, "value_type_list": value_types})

    values_out = []
    count_out = []
    index_out = []
    node.outputs["values"].subscribe(
        1, lambda v: values_out.append([a.copy() for a in v])
    )
    node.outputs["count"].subscribe(
        1, lambda v: count_out.append(v[0].copy())
    )
    node.outputs["index"].subscribe(
        1, lambda v: index_out.append(v[0].copy())
    )
    return node, values_out, count_out, index_out


def _ring_dispatch(node, *arrays):
    node.inputs["values"].dispatch(list(arrays))


def _ring_index(node, indices):
    node.inputs["index"].dispatch([np.asarray(indices, dtype=np.int32)])


def _ring_reset(node):
    node.inputs["reset"].dispatch([np.array([1], dtype=np.int32)])


# ---------------------------------------------------------------------------
# Basic write + count output
# ---------------------------------------------------------------------------

def test_ring_basic_write_count():
    """Writing values dispatches correct count."""
    node, _, count_out, _ = _make_ring_node(size=8)

    _ring_dispatch(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )

    assert len(count_out) == 1
    np.testing.assert_array_equal(count_out[0], [3])


def test_ring_incremental_count():
    """Multiple writes accumulate count."""
    node, _, count_out, _ = _make_ring_node(size=8)

    _ring_dispatch(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )
    _ring_dispatch(node,
        np.array([3.0, 4.0], dtype=np.float32),
        np.array([30.0, 40.0], dtype=np.float32),
    )

    assert len(count_out) == 2
    np.testing.assert_array_equal(count_out[0], [2])
    np.testing.assert_array_equal(count_out[1], [4])


# ---------------------------------------------------------------------------
# Index access (no wrap)
# ---------------------------------------------------------------------------

def test_ring_index_newest():
    """index=0 returns the most recently written value."""
    node, values_out, _, _ = _make_ring_node(size=8)

    _ring_dispatch(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )
    _ring_index(node, [0])

    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [3.0])
    np.testing.assert_array_equal(values_out[0][1], [30.0])


def test_ring_index_previous():
    """index=-1 returns the value before the newest."""
    node, values_out, _, _ = _make_ring_node(size=8)

    _ring_dispatch(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )
    _ring_index(node, [-1])

    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [2.0])
    np.testing.assert_array_equal(values_out[0][1], [20.0])


def test_ring_index_batch():
    """Batch index access returns multiple values at once."""
    node, values_out, _, _ = _make_ring_node(size=8)

    _ring_dispatch(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )
    _ring_index(node, [0, -1, -2])

    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [3.0, 2.0, 1.0])
    np.testing.assert_array_equal(values_out[0][1], [30.0, 20.0, 10.0])


# ---------------------------------------------------------------------------
# Wraparound
# ---------------------------------------------------------------------------

def test_ring_wraparound():
    """When buffer wraps, oldest values are overwritten."""
    node, values_out, count_out, _ = _make_ring_node(size=4)

    # Write 5 values into size-4 buffer → value 1.0 is overwritten
    _ring_dispatch(node,
        np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0, 40.0, 50.0], dtype=np.float32),
    )

    # Count capped at size
    np.testing.assert_array_equal(count_out[-1], [4])

    # Newest = 5.0, oldest = 2.0
    _ring_index(node, [0])
    np.testing.assert_array_equal(values_out[0][0], [5.0])

    _ring_index(node, [-3])
    np.testing.assert_array_equal(values_out[1][0], [2.0])


def test_ring_wraparound_large():
    """Large input overwrites buffer multiple times; only last `size` values remain."""
    node, values_out, _, _ = _make_ring_node(size=3)

    data = np.arange(1.0, 11.0, dtype=np.float32)  # [1..10]
    _ring_dispatch(node, data, data * 10)

    # Should contain [8, 9, 10]
    _ring_index(node, [0, -1, -2])

    np.testing.assert_array_equal(values_out[0][0], [10.0, 9.0, 8.0])
    np.testing.assert_array_equal(values_out[0][1], [100.0, 90.0, 80.0])


# ---------------------------------------------------------------------------
# Index clamping
# ---------------------------------------------------------------------------

def test_ring_index_clamp():
    """Out-of-range indices are clamped to valid range."""
    node, values_out, _, _ = _make_ring_node(size=8)

    _ring_dispatch(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )

    # count=3 → valid range [-(3-1), 0] = [-2, 0]
    # index=-5 → clamped to -2 → value 1.0
    # index=1 → clamped to 0 → value 3.0
    _ring_index(node, [-5, 1])

    np.testing.assert_array_equal(values_out[0][0], [1.0, 3.0])


def test_ring_index_output():
    """Output 'index' port dispatches clamped index values."""
    node, _, _, index_out = _make_ring_node(size=8)

    _ring_dispatch(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )

    _ring_index(node, [-5, 0, 1])

    assert len(index_out) == 1
    np.testing.assert_array_equal(index_out[0], [-2, 0, 0])


# ---------------------------------------------------------------------------
# Empty buffer
# ---------------------------------------------------------------------------

def test_ring_index_empty():
    """Index on empty buffer (count=0) produces no output."""
    node, values_out, _, index_out = _make_ring_node(size=4)

    _ring_index(node, [0])

    assert len(values_out) == 0
    assert len(index_out) == 0


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_ring_reset():
    """Reset clears count and prevents index access."""
    node, values_out, count_out, _ = _make_ring_node(size=8)

    _ring_dispatch(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )
    assert count_out[-1][0] == 3

    _ring_reset(node)

    # Reset dispatches count=0
    assert count_out[-1][0] == 0

    # Index on empty → no dispatch
    _ring_index(node, [0])
    assert len(values_out) == 0


def test_ring_reset_then_write():
    """After reset, new writes work correctly and old data is inaccessible."""
    node, values_out, count_out, _ = _make_ring_node(size=4)

    _ring_dispatch(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )
    _ring_reset(node)

    _ring_dispatch(node,
        np.array([7.0, 8.0], dtype=np.float32),
        np.array([70.0, 80.0], dtype=np.float32),
    )

    np.testing.assert_array_equal(count_out[-1], [2])

    _ring_index(node, [0, -1])
    np.testing.assert_array_equal(values_out[0][0], [8.0, 7.0])


# ---------------------------------------------------------------------------
# Multiple channels / dtypes
# ---------------------------------------------------------------------------

def test_ring_multi_channel():
    """Ring buffer works with mixed dtypes (f32, i32)."""
    node, values_out, _, _ = _make_ring_node(size=4, value_types="f32,i32")

    _ring_dispatch(node,
        np.array([1.5, 2.5, 3.5], dtype=np.float32),
        np.array([10, 20, 30], dtype=np.int32),
    )

    _ring_index(node, [0, -2])

    assert len(values_out) == 1
    np.testing.assert_array_equal(values_out[0][0], [3.5, 1.5])
    np.testing.assert_array_equal(values_out[0][1], [30, 10])
    assert values_out[0][0].dtype == np.float32
    assert values_out[0][1].dtype == np.int32


# ---------------------------------------------------------------------------
# Property changes
# ---------------------------------------------------------------------------

def test_ring_size_change_resets():
    """Changing size resets write_pos and count."""
    node, values_out, count_out, _ = _make_ring_node(size=8)

    _ring_dispatch(node,
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([10.0, 20.0, 30.0], dtype=np.float32),
    )

    node.set_properties({"size": 16})

    # count_out should still have old dispatches, but buffer is reset
    # Index on empty → no dispatch
    _ring_index(node, [0])
    assert len(values_out) == 0


def test_ring_size_validation():
    """size=0 raises ValueError."""
    node, _, _, _ = _make_ring_node(size=4)
    with pytest.raises(ValueError, match="size must be greater than 0"):
        node.set_properties({"size": 0})


def test_ring_value_type_change_resets():
    """Changing value_type_list resets buffer."""
    node, values_out, _, _ = _make_ring_node(size=4, value_types="f32,f32")

    _ring_dispatch(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0, 20.0], dtype=np.float32),
    )

    node.set_properties({"value_type_list": "i32,i32"})

    # Re-subscribe since output port is replaced
    values_out.clear()
    node.outputs["values"].subscribe(
        1, lambda v: values_out.append([a.copy() for a in v])
    )

    _ring_index(node, [0])
    assert len(values_out) == 0


# ---------------------------------------------------------------------------
# Length mismatch
# ---------------------------------------------------------------------------

def test_ring_length_mismatch():
    """Mismatched channel lengths are rejected."""
    node, _, count_out, _ = _make_ring_node(size=8)

    _ring_dispatch(node,
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([10.0], dtype=np.float32),  # length mismatch
    )

    # No count dispatched (input rejected)
    assert len(count_out) == 0


# ---------------------------------------------------------------------------
# Benchmark: ValuesRingBufferNode _on_values
# ---------------------------------------------------------------------------

def test_bench_ring_on_values():
    """Benchmark _on_values: before/after comparison."""
    import timeit

    node, _, _, _ = _make_ring_node(size=120, value_types="f32,f32")
    a = np.random.randn(500).astype(np.float32)
    b = np.random.randn(500).astype(np.float32)

    def run():
        _ring_dispatch(node, a, b)

    t = timeit.timeit(run, number=10000)
    print(f"\n_on_values 10000 calls: {t:.3f}s ({t / 10000 * 1e6:.1f} µs/call)")
