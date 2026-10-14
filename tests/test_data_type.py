from nonoha_core.data_type import (
    DATA_TYPE_CAST_TABLE,
    PortValueType,
    DataType,
    name_to_port_value_type,
    broadcast_shapes,
)
import numpy as np


def test_port_value_type_name():
    value_type = PortValueType(DataType.Int8)
    assert value_type.data_type == DataType.Int8
    assert value_type.shape == ()
    assert value_type.name == "i8"

    value_type = PortValueType(DataType.Float32, (4,))
    assert value_type.data_type == DataType.Float32
    assert value_type.shape == (4,)
    assert value_type.name == "f32[4]"

    value_type = PortValueType(DataType.Float32, (4, 3))
    assert value_type.name == "f32[4x3]"


def test_name_to_port_value_type():
    value_type = name_to_port_value_type("i8")
    assert value_type.data_type == DataType.Int8
    assert value_type.shape == ()
    assert value_type.name == "i8"

    value_type = name_to_port_value_type("i8[2]")
    assert value_type.data_type == DataType.Int8
    assert value_type.shape == (2,)
    assert value_type.name == "i8[2]"

    value_type = name_to_port_value_type("f32[?]")
    assert value_type.data_type == DataType.Float32
    assert value_type.shape == (-1,)
    assert value_type.name == "f32[?]"
    assert value_type.shape_str == "[?]"

    value_type = name_to_port_value_type("f32[128x?]")
    assert value_type.data_type == DataType.Float32
    assert value_type.shape == (128, -1)
    assert value_type.name == "f32[128x?]"
    assert value_type.shape_str == "[128x?]"

    value_type = name_to_port_value_type("f32[?x?x?]")
    assert value_type.data_type == DataType.Float32
    assert value_type.shape == (-1, -1, -1)
    assert value_type.name == "f32[?x?x?]"
    assert value_type.shape_str == "[?x?x?]"


def test_broadcast_shapes():
    assert broadcast_shapes((2, 3), (2, 3)) == np.broadcast_shapes((2, 3), (2, 3))
    assert broadcast_shapes((3,), (2, 3)) == np.broadcast_shapes((3,), (2, 3))
    assert broadcast_shapes((2, 3), (3,)) == np.broadcast_shapes((2, 3), (3,))
    assert broadcast_shapes((-1, 2), (2, 2)) == (2, 2)
    assert broadcast_shapes((-1, -1), (-1, -1)) == (-1, -1)


# --- cast table self-verification ---

_NUMPY_DTYPES = {
    DataType.Bool: np.bool_,
    DataType.Int8: np.int8,
    DataType.Uint8: np.uint8,
    DataType.Int16: np.int16,
    DataType.Uint16: np.uint16,
    DataType.Int32: np.int32,
    DataType.Uint32: np.uint32,
    DataType.Int64: np.int64,
    DataType.Uint64: np.uint64,
    DataType.Float32: np.float32,
    DataType.Float64: np.float64,
    DataType.Complex64: np.complex64,
    DataType.Complex128: np.complex128,
}


def test_cast_table_matches_numpy_safe():
    """The numeric block of DATA_TYPE_CAST_TABLE must equal numpy's
    value-preserving ("safe") casting rules, cell by cell."""
    for src, src_np in _NUMPY_DTYPES.items():
        for dst, dst_np in _NUMPY_DTYPES.items():
            expected = 1 if np.can_cast(src_np, dst_np, casting="safe") else 0
            actual = DATA_TYPE_CAST_TABLE[src.value][dst.value]
            assert actual == expected, (
                f"{src.name} -> {dst.name}: table={actual}, "
                f"np.can_cast(safe)={expected}"
            )


def test_cast_table_string_any_invariants():
    """String casts only to String/Any; Any casts only to Any;
    every type casts to Any; nothing casts to String but String."""
    numeric = set(_NUMPY_DTYPES)
    for t in DataType:
        # String row
        expected = 1 if t in (DataType.String, DataType.Any) else 0
        assert DATA_TYPE_CAST_TABLE[DataType.String.value][t.value] == expected
        # Any row
        expected = 1 if t == DataType.Any else 0
        assert DATA_TYPE_CAST_TABLE[DataType.Any.value][t.value] == expected
    for s in numeric:
        assert DATA_TYPE_CAST_TABLE[s.value][DataType.Any.value] == 1
        assert DATA_TYPE_CAST_TABLE[s.value][DataType.String.value] == 0
