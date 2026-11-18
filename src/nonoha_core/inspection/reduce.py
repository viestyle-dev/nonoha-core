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


class _Slot:
    """One value of a sample while it is fitted: a view of the sender's array
    (the items chosen, sliced), what it travels as, and its sizes. Nothing is
    copied until the sample is known to fit. ``stridable`` is decided only
    when the sample has to be strided (``_common_stride``)."""

    __slots__ = ("array", "items", "data_type", "wire", "itemsize", "item_bytes", "stridable", "widest", "converted")

    def __init__(self, value: np.ndarray, spec: ReduceSpec):
        array = np.asarray(value)
        batch = spec.batch
        if array.ndim == 0:
            array = array.reshape(1)
        elif batch != "all":
            array = array[-(1 if batch == "last" else batch):]
        slices = spec.slices
        if slices:
            index: list[slice] = [slice(None)]
            for dim in range(1, array.ndim):
                s = slices[dim - 1] if dim - 1 < len(slices) else None
                index.append(slice(*s) if s else slice(None))
            array = array[tuple(index)]
        self.array = array
        self.items = array.shape[0]
        self.widest = max(array.shape[1:], default=0)
        self.converted = False
        self.stridable: tuple[int, ...] = ()
        kind = array.dtype.kind
        if kind in "USOT":  # strings: copied as they are, never strided
            self.data_type = DataType.String
            self.wire = None
            self.itemsize = 0
            self.item_bytes = nbytes_of(array) / self.items if self.items else 0  # strings vary: their mean
            return
        if kind == "c":  # sent as magnitudes
            data_type = _CASTS[spec.cast] if spec.cast else DataType.Float32
            self.converted = True
        else:
            sendable = _SENDABLE.get(array.dtype)
            if sendable is None:
                raise ValueError(f"cannot send dtype {array.dtype}")
            data_type = sendable[0]
            if spec.cast and kind in "biuf" and _CASTS[spec.cast] is not data_type:
                data_type = _CASTS[spec.cast]
                self.converted = True
        self.data_type = data_type
        self.wire = WIRE_DTYPES[data_type]
        self.itemsize = self.wire.itemsize
        self.item_bytes = self.itemsize * math.prod(array.shape[1:])


def reduce_values(values: list[np.ndarray], spec: ReduceSpec, owned: bool = False) -> Reduced:
    """Fit ``values`` to ``spec`` (see the module docstring).

    ``owned``: the values are the inspector's own and are encoded before
    anything can change them (an accumulator's items): they are not copied,
    and the encoder converts them.
    """
    max_bytes = spec.max_bytes
    slots = [_Slot(value, spec) for value in values]
    flags = FLAG_BATCH_ALL if spec.batch == "all" else 0
    if spec.slices:
        flags |= FLAG_REDUCED
    total = 0
    most = 0
    widest = 0
    for slot in slots:
        total += slot.items * slot.item_bytes
        most = max(most, slot.items)
        widest = max(widest, slot.widest)
        if slot.converted:
            flags |= FLAG_CAST

    # 1. Too many items: the newest that fit, the same number in every slot
    if total > max_bytes and most > 1:
        keep = max(1, int(max_bytes // sum(slot.item_bytes for slot in slots)))
        total = 0
        for slot in slots:
            if slot.items > keep:
                slot.array = slot.array[-keep:]
                slot.items = keep
            total += slot.items * slot.item_bytes
        flags |= FLAG_REDUCED

    # 2. One item too large, or a dimension a frame cannot hold: one stride for every slot
    factor = 1
    if total > max_bytes or widest > _DIM_MAX:
        factor, total = _common_stride(slots, spec.auto_stride, total, max_bytes)
        if not factor:
            return Reduced(None, [], [], flags, int(total), _too_large(values, total, max_bytes))
        if factor > 1:
            flags |= FLAG_REDUCED

    # 3. One copy per slot, the sample's own, straight into the wire's byte order
    out: list[np.ndarray] = []
    types: list[PortValueType] = []
    steps: list[tuple[int, ...]] = []
    for slot in slots:
        array = slot.array
        step = [1] * (array.ndim - 1)
        if factor > 1 and slot.stridable:
            index = [slice(None)] * array.ndim
            for d in slot.stridable:
                index[d + 1] = slice(None, None, factor)
                step[d] = factor
            array = array[tuple(index)]
        if slot.wire is None:
            if not owned:
                array = np.array(array, copy=True)
        elif array.dtype.kind == "c":
            magnitude = np.empty(array.shape, slot.wire)
            np.abs(array, out=magnitude)
            array = magnitude
        elif not owned or slot.converted:
            array = array.astype(slot.wire, order="C")
        out.append(array)
        steps.append(tuple(step))
        types.append(PortValueType(slot.data_type, tuple(array.shape[1:])))
    return Reduced(out, types, steps, flags, int(total))


def _common_stride(slots: list[_Slot], auto_stride: list[int], total: float, max_bytes: int) -> tuple[int, float]:
    """(step, bytes): the smallest step, the same for the ``auto_stride``
    dimensions of every slot, with which the total fits and no dimension
    exceeds 65535; step 0 when none does. The estimate from the total is a
    lower bound and usually the answer (one check); otherwise the sizes,
    which fall as the step grows, are searched."""
    kmax = 0
    for slot in slots:
        shape = slot.array.shape
        if slot.wire is not None:  # strings are never strided
            slot.stridable = tuple(d for d in auto_stride if 0 <= d < len(shape) - 1 and shape[d + 1] > 1)
        kmax = max(kmax, len(slot.stridable))
    if not kmax:
        return 0, total
    lo = 1
    hi = 1
    for slot in slots:
        for d in slot.stridable:
            size = slot.array.shape[d + 1]
            hi = max(hi, size)
            lo = max(lo, -(-size // _DIM_MAX))
    if total > max_bytes:
        lo = max(lo, math.ceil((total / max_bytes) ** (1.0 / kmax)))
    lo = min(lo, hi)
    size, widest = _strided_size(slots, lo)
    if size <= max_bytes and widest <= _DIM_MAX:
        return lo, size
    size, widest = _strided_size(slots, hi)
    if size > max_bytes or widest > _DIM_MAX:
        return 0, total
    lo += 1
    while lo < hi:
        mid = (lo + hi) // 2
        mid_size, mid_widest = _strided_size(slots, mid)
        if mid_size <= max_bytes and mid_widest <= _DIM_MAX:
            hi, size = mid, mid_size
        else:
            lo = mid + 1
    return hi, size


def _strided_size(slots: list[_Slot], factor: int) -> tuple[float, int]:
    """(total bytes, widest non-batch dimension) of ``slots`` strided by ``factor``."""
    total = 0
    widest = 0
    for slot in slots:
        if not slot.stridable:
            total += slot.items * slot.item_bytes
            widest = max(widest, slot.widest)
            continue
        n = slot.items * slot.itemsize
        for axis, d in enumerate(slot.array.shape[1:]):
            if axis in slot.stridable:
                d = -(-d // factor)
            n *= d
            widest = max(widest, d)
        total += n
    return total, widest


def _too_large(values: list[np.ndarray], total: float, max_bytes: int) -> str:
    """Why a sample cannot be sent, with the shapes as they were dispatched."""
    shapes = " + ".join(
        f"{type_name_of(a) or a.dtype}[{'x'.join(str(d) for d in a.shape)}]" for a in map(np.asarray, values)
    )
    if total > max_bytes:
        return f"{shapes}: {int(total)} bytes, more than max_bytes {max_bytes} even reduced"
    return f"{shapes}: a dimension over 65535 that may not be strided"


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
