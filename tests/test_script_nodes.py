import numpy as np

from nonoha_core.nodes.script_nodes import PureScriptNode
from nonoha_core.data_type import DataType, PortValueType


def _make_node(
    source: str = "",
    in_types: str = "f32,f32",
    out_types: str = "f32",
) -> tuple[PureScriptNode, list]:
    """Create a PureScriptNode and capture output dispatches."""
    node = PureScriptNode("test")
    props: dict = {}
    if in_types != "f32,f32":
        props["in_value_type_list"] = in_types
    if out_types != "f32":
        props["out_value_type_list"] = out_types
    if source:
        props["source"] = source
    if props:
        node.set_properties(props)

    captured: list = []
    node.outputs["out"].subscribe(999, lambda values: captured.append(values))
    return node, captured


def _dispatch(node: PureScriptNode, *arrays: np.ndarray):
    node.inputs["values"].dispatch(list(arrays))


# ---------------------------------------------------------------------------
# Basic execution
# ---------------------------------------------------------------------------

def test_basic_execution():
    node, captured = _make_node(source="out = [v[0] + v[1]]")
    _dispatch(node, np.array([1.0], dtype=np.float32), np.array([2.0], dtype=np.float32))

    assert len(captured) == 1
    np.testing.assert_array_equal(captured[0][0], np.array([3.0], dtype=np.float32))


def test_dtype_correct_passthrough():
    """f32 output on f32 port → dispatched."""
    node, captured = _make_node(source="out = [v[0]]")
    _dispatch(node, np.array([5.0], dtype=np.float32), np.array([0.0], dtype=np.float32))

    assert len(captured) == 1
    assert captured[0][0].dtype == np.float32


# ---------------------------------------------------------------------------
# dtype mismatch → rejected
# ---------------------------------------------------------------------------

def test_dtype_mismatch_rejected():
    """f64 output on f32 port → warning, no dispatch."""
    node, captured = _make_node(source="out = [v[0].astype(np.float64)]")
    _dispatch(node, np.array([1.0], dtype=np.float32), np.array([0.0], dtype=np.float32))

    assert len(captured) == 0


def test_dtype_non_array_rejected():
    """Python list element → warning, no dispatch."""
    node, captured = _make_node(source="out = [[1.0]]")
    _dispatch(node, np.array([1.0], dtype=np.float32), np.array([0.0], dtype=np.float32))

    assert len(captured) == 0


def test_dtype_multiple_outputs_partial_mismatch():
    """Two outputs, second has wrong dtype → whole output rejected."""
    node, captured = _make_node(
        source="out = [v[0], v[0].astype(np.float64)]",
        out_types="f32,f32",
    )
    _dispatch(node, np.array([1.0], dtype=np.float32), np.array([0.0], dtype=np.float32))

    assert len(captured) == 0


# ---------------------------------------------------------------------------
# Any type → skip validation
# ---------------------------------------------------------------------------

def test_dtype_skip_for_any_type():
    """out_type=any → dtype validation skipped, dispatch succeeds."""
    node, captured = _make_node(
        source="out = [v[0].astype(np.float64)]",
        out_types="any",
    )
    _dispatch(node, np.array([1.0], dtype=np.float32), np.array([0.0], dtype=np.float32))

    assert len(captured) == 1


# ---------------------------------------------------------------------------
# String type
# ---------------------------------------------------------------------------

def test_dtype_string_type():
    """String output on str port → accepted."""
    node, captured = _make_node(
        source="out = [np.array(['hello'], dtype=np.dtypes.StringDType())]",
        in_types="f32",
        out_types="str",
    )
    _dispatch(node, np.array([0.0], dtype=np.float32))

    assert len(captured) == 1


def test_dtype_string_type_mismatch():
    """Non-string output on str port → rejected."""
    node, captured = _make_node(
        source="out = [np.array([1.0], dtype=np.float32)]",
        in_types="f32",
        out_types="str",
    )
    _dispatch(node, np.array([0.0], dtype=np.float32))

    assert len(captured) == 0


# ---------------------------------------------------------------------------
# env isolation
# ---------------------------------------------------------------------------

def test_env_isolation():
    """Variables defined in one call don't leak to the next."""
    node, captured = _make_node(source="temp = 42\nout = [v[0]]")
    _dispatch(node, np.array([1.0], dtype=np.float32), np.array([0.0], dtype=np.float32))
    assert len(captured) == 1

    # Second script that references temp (should fail, not leak from previous call)
    node.set_properties({"source": "out = [np.array([temp], dtype=np.float32)]"})
    _dispatch(node, np.array([1.0], dtype=np.float32), np.array([0.0], dtype=np.float32))

    # Script error → no dispatch
    assert len(captured) == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_source():
    """Empty source → no dispatch."""
    node, captured = _make_node(source="")
    _dispatch(node, np.array([1.0], dtype=np.float32), np.array([0.0], dtype=np.float32))

    assert len(captured) == 0


def test_script_error():
    """Runtime error in script → warning, no dispatch."""
    node, captured = _make_node(source="1/0")
    _dispatch(node, np.array([1.0], dtype=np.float32), np.array([0.0], dtype=np.float32))

    assert len(captured) == 0
