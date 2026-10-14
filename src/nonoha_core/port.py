from enum import Enum
from typing import Callable, TypeAlias
import numpy as np
import struct

from .data_type import (
    DataType,
    PortValueType,
    data_type_to_numpy_dtype,
    port_value_type_can_cast,
)


class PortDirection(Enum):
    INPUT = 0
    OUTPUT = 1


PortValue: TypeAlias = np.ndarray
"""A single port value (numpy array).

.. warning::
    PortValue arrays received in callbacks may be **views into shared
    buffers** (e.g. ValuesBuffer dispatches slices of its internal
    buffer). The sender may overwrite the underlying memory on the
    next dispatch. If you need to keep the data beyond the callback
    scope, you **must** call ``.copy()`` before storing it::

        # BAD — reference may be overwritten later
        self._chunks.append(values[0])

        # GOOD — safe independent copy
        self._chunks.append(values[0].copy())
"""

PortCallback: TypeAlias = Callable[[list[PortValue]], None]


class StaticTypePort:
    # Ports are the most numerous runtime objects (several per node), so
    # their attribute set is fixed with __slots__: no per-instance __dict__
    # (smaller objects) and accidental new attributes fail loudly.
    __slots__ = (
        "_direction",
        "_value_type_list",
        "_name",
        "_callback_keys",
        "_callback_funcs",
        "_current_values",
        "value_name_list",
    )

    def __init__(
        self,
        name: str,
        direction: PortDirection,
        value_type_list: list[PortValueType],
        value_name_list: list[str] | None = None,
    ):
        self._direction = direction
        self._value_type_list = value_type_list
        self._name = name

        # Parallel lists for swap-and-pop pattern
        self._callback_keys: list[int] = []
        self._callback_funcs: list[PortCallback] = []

        self._current_values: list[PortValue] | None = None
        self.value_name_list = (
            [None] * len(value_type_list)
            if value_name_list is None
            else value_name_list
        )

    @property
    def name(self):
        return self._name

    @property
    def direction(self):
        return self._direction

    @property
    def value_type_list(self):
        return self._value_type_list

    @property
    def current_values(self) -> list[PortValue] | None:
        return self._current_values

    def dispatch(self, values: list[PortValue]):
        self._current_values = values

        for callback in self._callback_funcs:
            callback(values)

    def subscribe(self, key: int, callback: PortCallback):
        # Check if key already exists
        try:
            i = self._callback_keys.index(key)
            # Update existing callback
            self._callback_funcs[i] = callback
        except ValueError:
            # Add new callback
            self._callback_keys.append(key)
            self._callback_funcs.append(callback)

    def unsubscribe(self, key: int):
        try:
            i = self._callback_keys.index(key)
            # Swap with last element and pop (O(1) removal)
            last_index = len(self._callback_keys) - 1
            if i != last_index:
                # Move last element to deleted position
                self._callback_keys[i] = self._callback_keys[last_index]
                self._callback_funcs[i] = self._callback_funcs[last_index]
            # Remove last element
            self._callback_keys.pop()
            self._callback_funcs.pop()
        except ValueError:
            # Key not found, ignore
            pass

    def has_callback(self, key: int) -> bool:
        """Check if a callback with the given key exists"""
        return key in self._callback_keys


class StaticTypeInputPort(StaticTypePort):
    __slots__ = ("dispatch_flags", "values_store", "_pending")

    def __init__(
        self,
        name: str,
        value_type_list: list[PortValueType],
        value_name_list: list[str] | None = None,
    ):
        super().__init__(name, PortDirection.INPUT, value_type_list, value_name_list)

        self.dispatch_flags: list[bool] = [False] * len(value_type_list)
        self.values_store: list[PortValue | None] = [None] * len(value_type_list)
        # Number of slots still None. A slot transitions None -> ndarray at
        # most once and never back (None is only the "not yet received"
        # sentinel; dispatching None as a value is outside the PortValue
        # contract), so "all slots filled" is tracked incrementally instead
        # of rescanning values_store on every receive.
        self._pending = len(value_type_list)

    def receive_value_with_index(self, index: int, values: list[PortValue]):
        store = self.values_store
        if store[index] is None:
            self._pending -= 1
        store[index] = values[0]

        if self.dispatch_flags[index] and self._pending == 0:
            # Expand code for best performance
            # self.dispatch(store)  # type: ignore

            # _pending == 0 guarantees every slot is filled (non-None)
            values_store: list[PortValue] = store  # type: ignore

            self._current_values = values_store

            for callback in self._callback_funcs:
                callback(values_store)


class StaticTypeOutputPort(StaticTypePort):
    __slots__ = ()

    def __init__(
        self,
        name: str,
        value_type_list: list[PortValueType],
        value_name_list: list[str] | None = None,
    ):
        super().__init__(name, PortDirection.OUTPUT, value_type_list, value_name_list)


def port_is_connectable(source: StaticTypePort, target: StaticTypePort) -> bool:
    if len(source.value_type_list) < len(target.value_type_list):
        return False

    # all() returns the true if all elements of the iterable are true or if the iterable is empty
    return all(
        port_value_type_can_cast(source_type, target_type)
        for source_type, target_type in zip(
            source.value_type_list, target.value_type_list
        )
    )


def port_is_connectable_with_index(
    source: StaticTypePort, target: StaticTypeInputPort, target_index: int
) -> bool:
    return port_value_type_can_cast(
        source.value_type_list[0], target.value_type_list[target_index]
    )


# --- Edge value conversion ---------------------------------------------------
# The cast table only gates which connections are allowed; the actual
# conversion is materialized here, on the edge, at connect time. These
# factories return the complete subscription callback (convert + deliver
# into the target port) fused into a single Python frame, or None when
# every slot already matches — in that case the caller subscribes the
# target's own dispatch / receive callback, so the hot path for
# same-dtype edges is unchanged. Conversion uses astype uniformly; a
# converted edge therefore always delivers an independent array, while
# an unconverted edge delivers the same reference as before.


def _slot_np_dtype(src: PortValueType, dst: PortValueType) -> np.dtype | None:
    """Return the numpy dtype to cast one slot to, or None if no cast."""
    if src.data_type == dst.data_type or dst.data_type == DataType.Any:
        return None
    return data_type_to_numpy_dtype(dst.data_type)


def make_edge_dispatch(
    source: StaticTypePort, target: StaticTypePort
) -> PortCallback | None:
    """Build the subscription callback for a full-port edge that needs
    conversion: it casts the mismatched slots and dispatches into
    ``target``. Returns None when every slot already matches (subscribe
    ``target.dispatch`` directly)."""
    dtypes = tuple(
        _slot_np_dtype(source.value_type_list[i], dst_t)
        for i, dst_t in enumerate(target.value_type_list)
    )
    if all(dt is None for dt in dtypes):
        return None

    if len(dtypes) == 1 and len(source.value_type_list) == 1:
        # Dominant case: single-slot edge on both ends — no surplus is
        # possible; convert and deliver in one frame.
        return lambda values, _d=target.dispatch, _dt=dtypes[0]: _d(
            [values[0].astype(_dt, copy=False)]
        )

    # The converting slot positions are fixed at connect time, so the
    # hot path below never tests for them — it only runs the actual
    # conversions.
    pairs = tuple((i, dt) for i, dt in enumerate(dtypes) if dt is not None)

    def cast_dispatch(
        values: list[PortValue], _d=target.dispatch, _pairs=pairs
    ) -> None:
        # C-level shallow copy keeps surplus source slots (a source may
        # legally be wider than the target) and list length unchanged.
        out = list(values)
        for i, dt in _pairs:
            out[i] = values[i].astype(dt, copy=False)
        _d(out)

    return cast_dispatch


def make_index_dispatch(
    source: StaticTypePort, target: StaticTypeInputPort, target_index: int
) -> PortCallback | None:
    """Build the subscription callback for an indexed edge (``in.N``)
    that needs conversion. Returns None when the slot already matches
    (subscribe the plain receive lambda directly).

    ``receive_value_with_index`` only reads ``values[0]``.
    """
    np_dtype = _slot_np_dtype(
        source.value_type_list[0], target.value_type_list[target_index]
    )
    if np_dtype is None:
        return None
    return lambda values, _r=target.receive_value_with_index, _i=target_index, _dt=np_dtype: _r(
        _i, [values[0].astype(_dt, copy=False)]
    )


def port_values_to_bytes(
    values: list[PortValue],
    value_type_list: list[PortValueType],
    byte_array: bytearray,
) -> bytearray:
    if len(values) < len(value_type_list):
        raise ValueError(
            f"Length of values ({len(values)}) is less than length of value_type_list ({len(value_type_list)})"
        )

    byte_array += len(value_type_list).to_bytes(1, "big")

    for value, value_type in zip(values, value_type_list):
        data_type = value_type.data_type

        byte_array += data_type.value.to_bytes(1, "big")
        byte_array += value_type.ndim.to_bytes(1, "big")
        byte_array += struct.pack(f">{len(value.shape) - 1}H", *value.shape[1:])

        match data_type:
            case DataType.Float32:
                value_bytes = value.astype(">f4", copy=False).tobytes()  # type: ignore
                byte_array += len(value_bytes).to_bytes(4, "big")
                byte_array += value_bytes

            case DataType.Float64:
                value_bytes = value.astype(">f8", copy=False).tobytes()  # type: ignore
                byte_array += len(value_bytes).to_bytes(4, "big")
                byte_array += value_bytes

            case DataType.Int8:
                value_bytes = value.astype(">i1", copy=False).tobytes()  # type: ignore
                byte_array += len(value_bytes).to_bytes(4, "big")
                byte_array += value_bytes

            case DataType.Uint8:
                value_bytes = value.astype(">u1", copy=False).tobytes()  # type: ignore
                byte_array += len(value_bytes).to_bytes(4, "big")
                byte_array += value_bytes

            case DataType.Bool:
                value_bytes = value.astype("bool", copy=False).tobytes()  # type: ignore
                byte_array += len(value_bytes).to_bytes(4, "big")
                byte_array += value_bytes

            case DataType.Int16:
                value_bytes = value.astype(">i2", copy=False).tobytes()  # type: ignore
                byte_array += len(value_bytes).to_bytes(4, "big")
                byte_array += value_bytes

            case DataType.Uint16:
                value_bytes = value.astype(">u2", copy=False).tobytes()  # type: ignore
                byte_array += len(value_bytes).to_bytes(4, "big")
                byte_array += value_bytes

            case DataType.Int32:
                value_bytes = value.astype(">i4", copy=False).tobytes()  # type: ignore
                byte_array += len(value_bytes).to_bytes(4, "big")
                byte_array += value_bytes

            case DataType.Uint32:
                value_bytes = value.astype(">u4", copy=False).tobytes()  # type: ignore
                byte_array += len(value_bytes).to_bytes(4, "big")
                byte_array += value_bytes

            case DataType.Int64:
                value_bytes = value.astype(">i8", copy=False).tobytes()  # type: ignore
                byte_array += len(value_bytes).to_bytes(4, "big")
                byte_array += value_bytes

            case DataType.Uint64:
                value_bytes = value.astype(">u8", copy=False).tobytes()  # type: ignore
                byte_array += len(value_bytes).to_bytes(4, "big")
                byte_array += value_bytes

            case DataType.String:
                # Each string followed by NULL terminator: "A\0B\0" for ["A", "B"]
                # Direct iteration works for both numpy arrays and lists
                if len(value) == 0:
                    byte_array += (0).to_bytes(4, "big")
                else:
                    string_bytes = "\0".join(value.ravel().tolist()).encode("utf-8")
                    byte_array += (len(string_bytes) + 1).to_bytes(4, "big")
                    byte_array += string_bytes
                    byte_array += b"\0"

            case _:
                raise ValueError(f"Unsupported data type: {value_type}")

    return byte_array
