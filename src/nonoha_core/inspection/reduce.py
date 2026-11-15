"""Semantics-free reduction of port values for inspection.

The inspector never interprets values (it does not know what an image or a
sound is). The client asks for generic array operations — which batch rows,
which slice of each dimension, which dimensions may be strided to fit a byte
budget, an optional cast — and decides itself how to display the result.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..data_type import DataType, PortValueType

_DTYPES: dict[str, DataType] = {
    "b": DataType.Bool,
    "i1": DataType.Int8,
    "u1": DataType.Uint8,
    "i2": DataType.Int16,
    "u2": DataType.Uint16,
    "i4": DataType.Int32,
    "u4": DataType.Uint32,
    "i8": DataType.Int64,
    "u8": DataType.Uint64,
    "f4": DataType.Float32,
    "f8": DataType.Float64,
}
_CASTS = {"f32": (np.float32, DataType.Float32), "f64": (np.float64, DataType.Float64)}

FLAG_REDUCED = 0x01
FLAG_BATCH_ALL = 0x02
FLAG_CAST = 0x04
FLAG_TRUNCATED = 0x08


def data_type_of(array: np.ndarray) -> DataType | None:
    """DataType for an array's dtype, or None if it cannot be sent."""
    kind = array.dtype.kind
    if kind in "USOT":
        return DataType.String
    if kind == "c":
        return None
    key = "b" if kind == "b" else f"{kind}{array.dtype.itemsize}"
    return _DTYPES.get(key)


def effective_type(array: np.ndarray) -> PortValueType | None:
    """PortValueType matching the array actually dispatched (shape without batch)."""
    data_type = data_type_of(array)
    if data_type is None:
        return None
    return PortValueType(data_type, tuple(int(d) for d in array.shape[1:]))


def nbytes_of(array: np.ndarray) -> int:
    if array.dtype.kind in "USOT":
        return sum(len(str(s).encode("utf-8")) + 1 for s in array.ravel())
    return int(array.nbytes)


@dataclass
class ReduceSpec:
    batch: str | int = "last"  # "last", "all" or a number of trailing rows
    slices: list[list[int | None] | None] | None = None  # per non-batch dim: [start, stop, step]
    auto_stride: list[int] = field(default_factory=list)  # non-batch dims that may be strided
    cast: str | None = None  # "f32" / "f64"
    max_bytes: int = 262144

    @classmethod
    def from_op(cls, op: dict[str, Any], max_bytes: int) -> "ReduceSpec":
        batch = op.get("batch", "last")
        if not (batch in ("last", "all") or (isinstance(batch, int) and batch > 0)):
            raise ValueError("batch must be 'last', 'all' or a positive integer")
        cast = op.get("cast")
        if cast is not None and cast not in _CASTS:
            raise ValueError(f"cast must be one of {sorted(_CASTS)} or null")
        slices = op.get("slice")
        if slices is not None and not isinstance(slices, list):
            raise ValueError("slice must be a list")
        dims = [int(d) for d in op.get("auto_stride", [])]
        return cls(batch=batch, slices=slices, auto_stride=dims, cast=cast, max_bytes=max_bytes)


@dataclass
class Reduced:
    values: list[np.ndarray]
    types: list[PortValueType]
    steps: list[tuple[int, ...]]  # per slot: stride applied to each non-batch dim
    flags: int
    original_shapes: list[tuple[int, ...]]


def _select_batch(array: np.ndarray, batch: str | int) -> np.ndarray:
    if array.ndim == 0:
        return array.reshape(1)
    if batch == "all":
        return array
    rows = 1 if batch == "last" else int(batch)
    return array[-rows:]


def reduce_values(values: list[np.ndarray], spec: ReduceSpec) -> Reduced:
    out: list[np.ndarray] = []
    types: list[PortValueType] = []
    steps: list[tuple[int, ...]] = []
    shapes: list[tuple[int, ...]] = []
    flags = FLAG_BATCH_ALL if spec.batch == "all" else 0

    for value in values:
        array = np.asarray(value)
        shapes.append(tuple(int(d) for d in array.shape))
        array = _select_batch(array, spec.batch)
        if array.dtype.kind == "c":
            array = np.abs(array).astype(np.float32)
            flags |= FLAG_CAST
        if spec.cast and array.dtype.kind in "biuf":
            np_type, _ = _CASTS[spec.cast]
            if array.dtype != np_type:
                array = array.astype(np_type)
                flags |= FLAG_CAST

        if spec.slices:
            index: list[slice] = [slice(None)]
            for dim in range(1, array.ndim):
                s = spec.slices[dim - 1] if dim - 1 < len(spec.slices) else None
                index.append(slice(*s) if s else slice(None))
            array = array[tuple(index)]
            flags |= FLAG_REDUCED

        step = [1] * (array.ndim - 1)
        dims = [d for d in spec.auto_stride if 0 <= d < array.ndim - 1 and array.shape[d + 1] > 1]
        size = nbytes_of(array)
        if dims and size > spec.max_bytes and array.dtype.kind not in "USOT":
            factor = math.ceil((size / spec.max_bytes) ** (1.0 / len(dims)))
            index = [slice(None)] * array.ndim
            for d in dims:
                index[d + 1] = slice(None, None, factor)
                step[d] = factor
            array = array[tuple(index)]
            flags |= FLAG_REDUCED

        out.append(np.ascontiguousarray(array))
        steps.append(tuple(step))
        vtype = effective_type(array)
        if vtype is None:
            raise ValueError(f"cannot send dtype {array.dtype}")
        types.append(vtype)

    if sum(nbytes_of(a) for a in out) > spec.max_bytes:
        flags |= FLAG_TRUNCATED
    return Reduced(out, types, steps, flags, shapes)


def summarize(array: np.ndarray, max_elements: int = 65536) -> tuple[list[float] | None, Any]:
    """([min, max, mean] for numeric arrays, last scalar or None)."""
    array = np.asarray(array)
    last = None
    if array.size == 0:
        return None, None
    if array.dtype.kind in "USOT":
        flat = array.ravel()
        return None, str(flat[-1])[:120]
    if array.dtype.kind not in "biuf":
        return None, None
    flat = array.ravel()
    if flat.size > max_elements:
        flat = flat[:: math.ceil(flat.size / max_elements)]
    data = flat.astype(np.float64)
    finite = data[np.isfinite(data)]
    if array.size == 1 or (array.ndim >= 1 and array[-1].size == 1):
        last = float(np.asarray(array[-1]).ravel()[0])
        if not math.isfinite(last):
            last = None
    if finite.size == 0:
        return None, last
    return [float(finite.min()), float(finite.max()), float(finite.mean())], last
