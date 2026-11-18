"""Semantics-free reduction of port values for inspection.

The inspector never interprets values (it does not know what an image or a
sound is). A client asks for generic array operations and decides itself how
to show the result. The first axis of a value is its batch: a dispatch
carries one item (an image, ``(1, H, W, 3)``) or many (an audio block,
``(512, channels)``).

- ``batch``: which items: the last one, all of them, or the last N (for
  ``since`` the hub gathers the items of every dispatch since the last
  sample and passes them as ``all``)
- ``slices``: per non-batch dimension, ``[start, stop, step]``
- ``cast``: numbers sent as f32 or f64 (complex values are always sent as
  their magnitude, f32)
- ``auto_stride``: the non-batch dimensions that may be strided to fit
- ``max_bytes``: the budget of one sample, every slot together (the data,
  not the frame's header)

A sample is fitted to ``max_bytes`` on views, before anything is copied:

1. too many items: the newest that fit are kept (the same number per slot);
2. still too large: the ``auto_stride`` dimensions of every slot are strided
   by one common step, the smallest with which the total fits and no
   dimension exceeds 65535 (a frame holds dimensions as u16);
3. still too large: nothing is sent (``values`` is None, ``too_large`` says
   why).

Then each slot is copied once, straight into the wire's byte order: the copy
that makes a sample the inspector's own (it is taken during a dispatch and
sent later) is the conversion the frame needs anyway.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..data_type import DataType, PortValueType, data_type_to_name
from ..port import WIRE_DTYPES

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
_CASTS = {"f32": DataType.Float32, "f64": DataType.Float64}
_DIM_MAX = 0xFFFF

# Every numeric dtype a value can have, in both byte orders -> (its DataType,
# the dtype it travels as). Built once: one dict lookup per slot per sample.
_SENDABLE: dict[np.dtype, tuple[DataType, np.dtype]] = {}
for _key, _data_type in _DTYPES.items():
    _native = np.dtype(np.bool_) if _key == "b" else np.dtype(_key)
    for _dtype in (_native, _native.newbyteorder()):
        _SENDABLE[_dtype] = (_data_type, WIRE_DTYPES[_data_type])

FLAG_REDUCED = 0x01  # cut by the request (slices) or to fit: fewer items, strides (see steps)
FLAG_BATCH_ALL = 0x02  # every item of the dispatch ("all"), or of every dispatch since the last sample ("since")
FLAG_CAST = 0x04  # numbers converted: cast, or complex magnitudes
FLAG_GAP = 0x10  # "since": items were lost before this sample (set by the hub)


def data_type_of(array: np.ndarray) -> DataType | None:
    """DataType for an array's dtype, or None if it cannot be sent."""
    kind = array.dtype.kind
    if kind in "USOT":
        return DataType.String
    if kind == "c":
        return None
    key = "b" if kind == "b" else f"{kind}{array.dtype.itemsize}"
    return _DTYPES.get(key)


def type_name_of(array: np.ndarray) -> str | None:
    """The type name ports use ("f32", "str", "c64"), without the shape."""
    kind = array.dtype.kind
    if kind == "c":
        return "c64" if array.dtype.itemsize == 8 else "c128"
    data_type = data_type_of(array)
    return data_type_to_name(data_type) if data_type is not None else None


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
    batch: str | int = "last"  # "last", "all" or a number of trailing items
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
    values: list[np.ndarray] | None  # None: too large to send (see too_large)
    types: list[PortValueType]
    steps: list[tuple[int, ...]]  # per slot: the stride of each non-batch dim
    flags: int
    nbytes: int  # the data the frame will carry (its header adds a few dozen bytes)
    too_large: str | None = None


def reduce_values(values: list[np.ndarray], spec: ReduceSpec, owned: bool = False) -> Reduced:
    """Fit ``values`` to ``spec`` (see the module docstring).

    ``owned``: the values are the inspector's own and are encoded before
    anything can change them (an accumulator's items): they are not copied,
    and the encoder converts them.
    """
    batch = spec.batch
    slices = spec.slices
    cast = spec.cast
    max_bytes = spec.max_bytes
    flags = FLAG_BATCH_ALL if batch == "all" else 0

    # Pass 1, views only. Per slot: [array, DataType, wire dtype (None: strings),
    # items, bytes per item, bytes per element]
    slots: list[list[Any]] = []
    total = 0
    most = 0
    wide = False
    for value in values:
        array = np.asarray(value)
        if array.ndim == 0:
            array = array.reshape(1)
        elif batch != "all":
            array = array[-(1 if batch == "last" else batch):]
        if slices:
            index: list[slice] = [slice(None)]
            for dim in range(1, array.ndim):
                s = slices[dim - 1] if dim - 1 < len(slices) else None
                index.append(slice(*s) if s else slice(None))
            array = array[tuple(index)]
            flags |= FLAG_REDUCED
        items = array.shape[0]
        kind = array.dtype.kind
        if kind in "USOT":
            data_type = DataType.String
            wire = None
            itemsize = 0
            item_bytes = nbytes_of(array) / items if items else 0  # strings vary: their mean
        else:
            if kind == "c":
                data_type = _CASTS[cast] if cast else DataType.Float32  # magnitudes
                flags |= FLAG_CAST
            else:
                sendable = _SENDABLE.get(array.dtype)
                if sendable is None:
                    raise ValueError(f"cannot send dtype {array.dtype}")
                data_type = sendable[0]
                if cast and kind in "biuf" and _CASTS[cast] is not data_type:
                    data_type = _CASTS[cast]
                    flags |= FLAG_CAST
            wire = WIRE_DTYPES[data_type]
            itemsize = wire.itemsize
            item_bytes = itemsize * math.prod(array.shape[1:])
        for d in array.shape[1:]:
            if d > _DIM_MAX:
                wide = True
        slots.append([array, data_type, wire, items, item_bytes, itemsize])
        total += items * item_bytes
        if items > most:
            most = items

    # 1. too many items: keep the newest that fit
    if total > max_bytes and most > 1:
        per_item = sum(slot[4] for slot in slots)
        keep = max(1, int(max_bytes // per_item)) if per_item else most
        if keep < most:
            total = 0
            for slot in slots:
                if slot[3] > keep:
                    slot[0] = slot[0][-keep:]
                    slot[3] = keep
                total += slot[3] * slot[4]
            flags |= FLAG_REDUCED

    # 2. still too large, or a dimension a frame cannot hold: one common stride
    factor = 1
    stridable: list[list[int]] = []
    if total > max_bytes or wide:
        kmax = 0
        lo = 1
        hi = 1
        for slot in slots:
            array = slot[0]
            dims = [] if slot[2] is None else [
                d for d in spec.auto_stride if 0 <= d < array.ndim - 1 and array.shape[d + 1] > 1
            ]
            stridable.append(dims)
            if len(dims) > kmax:
                kmax = len(dims)
            for d in dims:
                size = array.shape[d + 1]
                if size > hi:
                    hi = size
                if size > _DIM_MAX:
                    lo = max(lo, -(-size // _DIM_MAX))
        if total > max_bytes and kmax:
            lo = max(lo, math.ceil((total / max_bytes) ** (1.0 / kmax)))
        lo = min(lo, hi)
        # The estimate is a lower bound and usually the answer: one check
        size, widest = _strided_size(slots, stridable, lo) if kmax else (total, _DIM_MAX + 1)
        if size > max_bytes or widest > _DIM_MAX:
            size, widest = _strided_size(slots, stridable, hi) if kmax else (size, widest)
            if not kmax or size > max_bytes or widest > _DIM_MAX:
                # 3. nothing fits: say why, with the shapes as they were dispatched
                shapes = " + ".join(
                    f"{type_name_of(np.asarray(v)) or np.asarray(v).dtype}[{'x'.join(str(d) for d in np.shape(v))}]"
                    for v in values
                )
                reason = (
                    f"{shapes}: {int(total)} bytes, more than max_bytes {max_bytes} even reduced"
                    if total > max_bytes
                    else f"{shapes}: a dimension over 65535 that may not be strided"
                )
                return Reduced(None, [], [], flags, int(total), reason)
            lo += 1
            while lo < hi:  # the smallest stride that fits (sizes fall as it grows)
                mid = (lo + hi) // 2
                mid_size, mid_widest = _strided_size(slots, stridable, mid)
                if mid_size <= max_bytes and mid_widest <= _DIM_MAX:
                    hi, size = mid, mid_size
                else:
                    lo = mid + 1
        factor = lo
        if factor > 1:
            total = size
            flags |= FLAG_REDUCED

    # Pass 2: one copy per slot, the sample's own, in the wire's byte order
    out: list[np.ndarray] = []
    types: list[PortValueType] = []
    steps: list[tuple[int, ...]] = []
    for i, slot in enumerate(slots):
        array = slot[0]
        step = [1] * (array.ndim - 1)
        if factor > 1 and stridable[i]:
            index = [slice(None)] * array.ndim
            for d in stridable[i]:
                index[d + 1] = slice(None, None, factor)
                step[d] = factor
            array = array[tuple(index)]
        wire = slot[2]
        if wire is None:
            if not owned:
                array = np.array(array, copy=True)
        elif array.dtype.kind == "c":
            magnitude = np.empty(array.shape, wire)
            np.abs(array, out=magnitude)
            array = magnitude
        elif not owned or _SENDABLE[array.dtype][0] is not slot[1]:
            array = array.astype(wire, order="C")
        out.append(array)
        steps.append(tuple(step))
        types.append(PortValueType(slot[1], tuple(array.shape[1:])))
    return Reduced(out, types, steps, flags, int(total))


def _strided_size(slots: list[list[Any]], stridable: list[list[int]], factor: int) -> tuple[float, int]:
    """(total bytes, widest non-batch dimension) of ``slots`` strided by ``factor``."""
    total = 0
    widest = 0
    for slot, dims in zip(slots, stridable):
        shape = slot[0].shape
        if not dims:
            total += slot[3] * slot[4]
            for d in shape[1:]:
                if d > widest:
                    widest = d
            continue
        n = slot[3] * slot[5]
        for axis in range(1, len(shape)):
            d = shape[axis]
            if axis - 1 in dims:
                d = -(-d // factor)
            n *= d
            if d > widest:
                widest = d
        total += n
    return total, widest


def summarize(array: np.ndarray, max_elements: int = 65536) -> tuple[list[float] | None, Any]:
    """([min, max, mean] for numeric arrays, last scalar or None).

    Computed on the array itself (at most ``max_elements`` of it, strided):
    no float64 copy and no mask unless a value is NaN or infinite.
    """
    array = np.asarray(array)
    if array.size == 0:
        return None, None
    kind = array.dtype.kind
    if kind in "USOT":
        return None, str(array.ravel()[-1])[:120]
    if kind not in "biuf":
        return None, None
    # The last batch item, when it holds one element (0-d arrays included)
    row = array[-1] if array.ndim else array
    last = None
    if row.size == 1:
        last = float(row.item())
        if not math.isfinite(last):
            last = None
    flat = array.ravel()
    if flat.size > max_elements:
        flat = flat[:: math.ceil(flat.size / max_elements)]
    low = float(flat.min())
    high = float(flat.max())
    if math.isfinite(low) and math.isfinite(high):
        # NaN propagates into min and max, and infinities show there: both
        # finite means every value is
        return [low, high, float(flat.mean(dtype=np.float64))], last
    data = flat.astype(np.float64)
    finite = data[np.isfinite(data)]
    if finite.size == 0:
        return None, last
    return [float(finite.min()), float(finite.max()), float(finite.mean())], last
