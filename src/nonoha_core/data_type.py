from enum import Enum
from typing import TypeAlias
import numpy as np


# + number
#   + real-number
#   + complex-number
# + bool
# + number-vector
#   + real-vector
#   + complex-vector
# https://numpy.org/doc/2.1/reference/arrays.scalars.html
# https://numpy.org/doc/2.1/user/basics.types.html
# https://numpy.org/doc/2.1/reference/generated/numpy.can_cast.html

# TODO: Re-arrange the order of the data types.
# fmt: off
class DataType(Enum):
    Bool   = 0
    
    Int8   = 1
    Uint8  = 2
    Int16  = 3
    Uint16 = 4
    Int32  = 5
    Uint32 = 6
    Int64  = 7
    Uint64 = 8

    Float32 = 9
    Float64 = 10

    Complex64 = 11
    Complex128 = 12

    String = 13
    Any = 14
# fmt: on

_name_to_data_type = {
    "bool": DataType.Bool,
    "i8": DataType.Int8,
    "u8": DataType.Uint8,
    "i16": DataType.Int16,
    "u16": DataType.Uint16,
    "i32": DataType.Int32,
    "u32": DataType.Uint32,
    "i64": DataType.Int64,
    "u64": DataType.Uint64,
    "f32": DataType.Float32,
    "f64": DataType.Float64,
    "c64": DataType.Complex64,
    "c128": DataType.Complex128,
    "str": DataType.String,
    "any": DataType.Any,
}

_data_type_to_name = {v: k for k, v in _name_to_data_type.items()}

# fmt: off
_DATA_TYPE_TO_NUMPY_DTYPE: dict[DataType, np.dtype] = {
    DataType.Bool:       np.dtype(np.bool_),
    DataType.Int8:       np.dtype(np.int8),
    DataType.Uint8:      np.dtype(np.uint8),
    DataType.Int16:      np.dtype(np.int16),
    DataType.Uint16:     np.dtype(np.uint16),
    DataType.Int32:      np.dtype(np.int32),
    DataType.Uint32:     np.dtype(np.uint32),
    DataType.Int64:      np.dtype(np.int64),
    DataType.Uint64:     np.dtype(np.uint64),
    DataType.Float32:    np.dtype(np.float32),
    DataType.Float64:    np.dtype(np.float64),
    DataType.Complex64:  np.dtype(np.complex64),
    DataType.Complex128: np.dtype(np.complex128),
    DataType.String:     np.dtypes.StringDType(), # type: ignore
}
# fmt: on


def data_type_to_numpy_dtype(data_type: DataType) -> np.dtype | None:
    return _DATA_TYPE_TO_NUMPY_DTYPE.get(data_type)


NUMBER_DATA_TYPES = {
    DataType.Int8,
    DataType.Uint8,
    DataType.Int16,
    DataType.Uint16,
    DataType.Int32,
    DataType.Uint32,
    DataType.Int64,
    DataType.Uint64,
    DataType.Float32,
    DataType.Float64,
    DataType.Complex64,
    DataType.Complex128,
}


def name_to_data_type(name: str) -> DataType:
    return _name_to_data_type[name]


def data_type_to_name(data_type: DataType) -> str:
    return _data_type_to_name[data_type]


def data_type_is_number(data_type: DataType) -> bool:
    return data_type in {
        DataType.Int8,
        DataType.Uint8,
        DataType.Int16,
        DataType.Uint16,
        DataType.Int32,
        DataType.Uint32,
        DataType.Int64,
        DataType.Uint64,
        DataType.Float32,
        DataType.Float64,
        DataType.Complex64,
        DataType.Complex128,
    }


# fmt: off
# Numeric 13x13 block matches numpy's value-preserving casting exactly:
#   np.can_cast(src, dst, casting="safe")
# An allowed entry means the value survives the conversion unchanged
# (bool -> 0/1, integer widening, exact float/complex embedding).
# Truthiness (number -> bool), signed -> unsigned, and precision-losing
# casts (e.g. i64 -> f32, f64 -> c64) are rejected; use an explicit
# AsType node for intentional lossy conversion.
# The actual conversion is materialized on the edge at connect time
# (see make_edge_converter in port.py) — allowed here means "will be cast",
# not "will be passed through as-is".
# Consistency with numpy is enforced by a test (tests/test_data_type.py).
DATA_TYPE_CAST_TABLE: list[list[int]] = [

# bool i8 u8 i16 u16 i32 u32 i64 u64 f32 f64 c64 c128 str any
[1,    1, 1, 1,  1,  1,  1,  1,  1,  1,  1,  1,  1,   0, 1], # Bool
[0,    1, 0, 1,  0,  1,  0,  1,  0,  1,  1,  1,  1,   0, 1], # Int8
[0,    0, 1, 1,  1,  1,  1,  1,  1,  1,  1,  1,  1,   0, 1], # Uint8
[0,    0, 0, 1,  0,  1,  0,  1,  0,  1,  1,  1,  1,   0, 1], # Int16
[0,    0, 0, 0,  1,  1,  1,  1,  1,  1,  1,  1,  1,   0, 1], # Uint16
[0,    0, 0, 0,  0,  1,  0,  1,  0,  0,  1,  0,  1,   0, 1], # Int32
[0,    0, 0, 0,  0,  0,  1,  1,  1,  0,  1,  0,  1,   0, 1], # Uint32
[0,    0, 0, 0,  0,  0,  0,  1,  0,  0,  1,  0,  1,   0, 1], # Int64
[0,    0, 0, 0,  0,  0,  0,  0,  1,  0,  1,  0,  1,   0, 1], # Uint64
[0,    0, 0, 0,  0,  0,  0,  0,  0,  1,  1,  1,  1,   0, 1], # Float32
[0,    0, 0, 0,  0,  0,  0,  0,  0,  0,  1,  0,  1,   0, 1], # Float64
[0,    0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  1,  1,   0, 1], # Complex64
[0,    0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  0,  1,   0, 1], # Complex128
[0,    0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,   1, 1], # String
[0,    0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,   0, 1], # Any
]

# fmt: on


def data_type_can_cast(from_type: DataType, to_type: DataType) -> bool:
    return DATA_TYPE_CAST_TABLE[from_type.value][to_type.value] == 1


class PortValueType:
    def __init__(
        self,
        data_type: DataType,
        shape: tuple[int, ...] = (),
    ):
        self.data_type = data_type
        self.shape = shape
        self.ndim = len(shape)

        # shape_str = f"[{'x'.join(map(str, shape))}]" if shape else ""
        shape_str = (
            f"[{'x'.join(map(lambda x: str(x) if x != -1 else '?', shape))}]"
            if shape
            else ""
        )

        self.name = f"{data_type_to_name(data_type)}{shape_str}"
        self.shape_str = shape_str

    def __eq__(self, other):
        if not isinstance(other, PortValueType):
            return False
        return self.data_type == other.data_type and self.shape == other.shape


def name_to_port_value_type(name: str) -> PortValueType:
    # Split the type name and the shape
    if "[" in name and name.endswith("]"):
        data_type_name, shape_part = name.split("[", 1)
        shape_str = shape_part.rstrip("]")

        # Parse each dimension of the shape
        shape = tuple(-1 if dim in ("N", "?") else int(dim) for dim in shape_str.split("x"))
    else:
        data_type_name = name
        shape = ()

    # Look up the DataType from the type name
    data_type = name_to_data_type(data_type_name)

    # Create and return the PortValueType instance
    return PortValueType(data_type, shape)


def str_to_shape(shape_str: str) -> tuple[int, ...]:
    if shape_str == "":
        return tuple()

    if shape_str.startswith("[") and shape_str.endswith("]"):
        shape_str = shape_str[1:-1]
    shape = tuple(int(dim) if dim not in ("N", "?") else -1 for dim in shape_str.split("x"))
    return shape


def port_value_type_can_cast(
    from_type: PortValueType,
    to_type: PortValueType,
):
    if to_type.data_type == DataType.Any:
        return True

    if from_type.ndim != to_type.ndim:
        return False

    if any(
        from_dim != to_dim and to_dim != -1
        for from_dim, to_dim in zip(from_type.shape, to_type.shape)
    ):
        return False

    return DATA_TYPE_CAST_TABLE[from_type.data_type.value][to_type.data_type.value] == 1


PropertyDataType: TypeAlias = int | float | str | bool


def broadcast_shapes(*shapes: tuple[int, ...]) -> tuple[int, ...]:
    if not shapes:
        return tuple()

    # Align all shapes to the same rank (prepend 1s)
    max_dim = max(len(shape) for shape in shapes)
    aligned_shapes = [(1,) * (max_dim - len(shape)) + shape for shape in shapes]

    result = []

    # Process dimension by dimension
    for dims in zip(*aligned_shapes):
        # Adopt a concrete size (other than 1) when present
        concrete_values = [d for d in dims if d > 1 or d == 0]

        if concrete_values:
            # Different concrete sizes in the same dimension cannot broadcast
            if len(set(concrete_values)) > 1:
                raise ValueError(f"Incompatible shapes for broadcasting: {shapes}")
            result.append(concrete_values[0])
            continue

        # A symbolic size is present
        symbolic_dims = [d for d in dims if d < 0]
        if symbolic_dims:
            symbolic_value = symbolic_dims[0]
            result.append(symbolic_value)
            continue

        # Every candidate is 1, so the result is 1
        result.append(1)

    return tuple(result)
