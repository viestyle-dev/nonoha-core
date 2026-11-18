"""The sample encoding of e29cf56, kept as a reference for tests.

reduce_values was rewritten (sizes decided on views, one copy straight to the
wire byte order). For every value that fitted before, the new code must put
the same bytes on the wire as this one did; tests compare the two.
"""

from __future__ import annotations

import math
import struct

import numpy as np

from nonoha_core.data_type import DataType, PortValueType
from nonoha_core.port import port_values_to_bytes

_DTYPES = {
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
_CASTS = {"f32": np.float32, "f64": np.float64}
_HEADER = struct.Struct(">BBHIIIdBB")

FLAG_REDUCED = 0x01
FLAG_BATCH_ALL = 0x02
FLAG_CAST = 0x04
FLAG_TRUNCATED = 0x08


def _type_of(array):
    kind = array.dtype.kind
    if kind in "USOT":
        data_type = DataType.String
    elif kind == "c":
        return None
    else:
        data_type = _DTYPES.get("b" if kind == "b" else f"{kind}{array.dtype.itemsize}")
        if data_type is None:
            return None
    return PortValueType(data_type, tuple(int(d) for d in array.shape[1:]))


def _nbytes(array):
    if array.dtype.kind in "USOT":
        return sum(len(str(s).encode("utf-8")) + 1 for s in array.ravel())
    return int(array.nbytes)


def reference_reduce(values, batch="last", slices=None, auto_stride=(), cast=None, max_bytes=262144):
    """(values, types, steps, flags) as e29cf56 reduced them."""
    out, types, steps = [], [], []
    flags = FLAG_BATCH_ALL if batch == "all" else 0
    for value in values:
        array = np.asarray(value)
        if array.ndim == 0:
            array = array.reshape(1)
        elif batch != "all":
            array = array[-(1 if batch == "last" else int(batch)):]
        if array.dtype.kind == "c":
            array = np.abs(array).astype(np.float32)
            flags |= FLAG_CAST
        if cast and array.dtype.kind in "biuf" and array.dtype != _CASTS[cast]:
            array = array.astype(_CASTS[cast])
            flags |= FLAG_CAST
        if slices:
            index = [slice(None)]
            for dim in range(1, array.ndim):
                s = slices[dim - 1] if dim - 1 < len(slices) else None
                index.append(slice(*s) if s else slice(None))
            array = array[tuple(index)]
            flags |= FLAG_REDUCED
        step = [1] * (array.ndim - 1)
        dims = [d for d in auto_stride if 0 <= d < array.ndim - 1 and array.shape[d + 1] > 1]
        size = _nbytes(array)
        if dims and size > max_bytes and array.dtype.kind not in "USOT":
            factor = math.ceil((size / max_bytes) ** (1.0 / len(dims)))
            index = [slice(None)] * array.ndim
            for d in dims:
                index[d + 1] = slice(None, None, factor)
                step[d] = factor
            array = array[tuple(index)]
            flags |= FLAG_REDUCED
        out.append(np.array(array, order="C", copy=True))
        steps.append(tuple(step))
        types.append(_type_of(array))
    if sum(_nbytes(a) for a in out) > max_bytes:
        flags |= FLAG_TRUNCATED
    return out, types, steps, flags


def reference_frame(watch_id, frame_seq, sample_seq, dispatch_count, t, values, types, steps, flags):
    """The frame e29cf56 sent for a sample that fitted."""
    out = bytearray(_HEADER.pack(0x21, 1, watch_id, frame_seq, sample_seq, dispatch_count, t, flags, len(steps)))
    for step in steps:
        out.append(len(step))
        out += struct.pack(f">{len(step)}H", *(min(s, 0xFFFF) for s in step))
    port_values_to_bytes(values, types, out)
    return bytes(out)
