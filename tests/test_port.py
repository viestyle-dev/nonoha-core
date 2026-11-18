import numpy as np

from nonoha_core.data_type import DataType, PortValueType
from nonoha_core.port import StaticTypeInputPort, port_values_to_bytes


def test_serialize_port_values():
    test = port_values_to_bytes(
        [np.array([1, 2, 3], dtype=np.int8)],
        [PortValueType(DataType.Int8)],
        bytearray(),
    )
    # fmt: off
    assert test == bytearray(
        [
            1,  # Length of value_type_list
            1,  # DataType.Int8
            0,  # ndim
            0, 0, 0, 3, # Length of data
            1, 2, 3,
        ]
    )
    # fmt: on

    test = port_values_to_bytes(
        [np.array([[[1, 2], [3, 4], [5, 6]]], dtype=np.uint8)],
        [PortValueType(DataType.Uint8, (3, 2))],
        bytearray(),
    )

    # fmt: off
    assert test == bytearray(
        [
            1,  # Length of value_type_list
            2,  # DataType.Uint8
            2,  # ndim
            0, 3, 0, 2, # shape
            0, 0, 0, 6, # Length of data
            1, 2,
            3, 4,
            5, 6,
        ]
    )
    # fmt: on



def _reference_port_values_to_bytes(values, value_type_list, byte_array):
    """The encoder as it was before the one-conversion rewrite (1.1.0.dev0):
    the oracle the rewrite must match byte for byte."""
    import struct

    byte_array += len(value_type_list).to_bytes(1, "big")
    big_endian = {
        DataType.Float32: ">f4", DataType.Float64: ">f8", DataType.Int8: ">i1",
        DataType.Uint8: ">u1", DataType.Bool: "bool", DataType.Int16: ">i2",
        DataType.Uint16: ">u2", DataType.Int32: ">i4", DataType.Uint32: ">u4",
        DataType.Int64: ">i8", DataType.Uint64: ">u8",
    }
    for value, value_type in zip(values, value_type_list):
        data_type = value_type.data_type
        byte_array += data_type.value.to_bytes(1, "big")
        byte_array += value_type.ndim.to_bytes(1, "big")
        byte_array += struct.pack(f">{len(value.shape) - 1}H", *value.shape[1:])
        if data_type == DataType.String:
            if len(value) == 0:
                byte_array += (0).to_bytes(4, "big")
            else:
                string_bytes = "\0".join(value.ravel().tolist()).encode("utf-8")
                byte_array += (len(string_bytes) + 1).to_bytes(4, "big")
                byte_array += string_bytes
                byte_array += b"\0"
        else:
            value_bytes = value.astype(big_endian[data_type], copy=False).tobytes()
            byte_array += len(value_bytes).to_bytes(4, "big")
            byte_array += value_bytes
    return byte_array


def test_serialize_matches_the_previous_encoder_byte_for_byte():
    rng = np.random.default_rng(7)
    numeric = [
        (DataType.Bool, np.bool_), (DataType.Int8, np.int8), (DataType.Uint8, np.uint8),
        (DataType.Int16, np.int16), (DataType.Uint16, np.uint16), (DataType.Int32, np.int32),
        (DataType.Uint32, np.uint32), (DataType.Int64, np.int64), (DataType.Uint64, np.uint64),
        (DataType.Float32, np.float32), (DataType.Float64, np.float64),
    ]
    cases = []
    for data_type, np_type in numeric:
        for shape in [(), (3,), (2, 4), (2, 3, 4)]:
            for batch in [1, 5]:
                raw = rng.integers(0, 100, size=(batch, *shape)) if data_type != DataType.Bool else rng.integers(0, 2, size=(batch, *shape))
                array = raw.astype(np_type)
                cases.append(([array], [PortValueType(data_type, shape)]))
                # big-endian input, Fortran order, a strided view, another dtype (cast)
                cases.append(([array.astype(array.dtype.newbyteorder(">"))], [PortValueType(data_type, shape)]))
                cases.append(([np.asfortranarray(array)], [PortValueType(data_type, shape)]))
                if array.shape[-1] > 1 and array.ndim > 1:
                    cases.append(([array[..., ::2]], [PortValueType(data_type, (*shape[:-1], len(range(0, shape[-1], 2))))]))
                cases.append(([raw.astype(np.float64)], [PortValueType(data_type, shape)]))
    strings = np.array([["a", "bc"], ["日本", ""]], dtype=np.dtypes.StringDType())
    cases.append(([strings], [PortValueType(DataType.String, (2,))]))
    cases.append(([np.array([], dtype=np.dtypes.StringDType())], [PortValueType(DataType.String)]))
    # several values in one message, written after existing bytes
    cases.append(([np.ones((2, 3), np.float32), np.zeros((2,), np.int16)],
                  [PortValueType(DataType.Float32, (3,)), PortValueType(DataType.Int16)]))
    for values, types in cases:
        expected = _reference_port_values_to_bytes(values, types, bytearray(b"head"))
        assert port_values_to_bytes(values, types, bytearray(b"head")) == expected, (values, types)


# --- receive_value_with_index firing semantics (fill tracking) ---

F32 = PortValueType(DataType.Float32)
_V = [np.array([1.0], dtype=np.float32)]


def _port_with_recorder(nslots, flag_index):
    port = StaticTypeInputPort("in", [F32] * nslots)
    port.dispatch_flags[flag_index] = True
    fired = []
    port.subscribe(1, lambda values: fired.append(list(values)))
    return port, fired


def test_receive_no_fire_until_all_slots_filled():
    port, fired = _port_with_recorder(3, flag_index=0)

    port.receive_value_with_index(0, _V)  # flagged, but slots 1,2 empty
    assert fired == []
    port.receive_value_with_index(1, _V)
    assert fired == []
    port.receive_value_with_index(2, _V)  # full, but slot 2 is not flagged
    assert fired == []
    port.receive_value_with_index(0, _V)  # flagged + full -> fire
    assert len(fired) == 1


def test_receive_repeated_set_on_same_slot_before_full():
    """Re-setting an already-filled slot must not fake fullness."""
    port, fired = _port_with_recorder(2, flag_index=0)

    port.receive_value_with_index(0, _V)
    port.receive_value_with_index(0, _V)  # same slot again; slot 1 still empty
    assert fired == []
    port.receive_value_with_index(1, _V)  # now full (unflagged slot)
    assert fired == []
    port.receive_value_with_index(0, _V)  # flagged + full -> fire
    assert len(fired) == 1


def test_receive_steady_state_fires_every_time():
    """Once full, every flagged receive fires (streaming steady state)."""
    port, fired = _port_with_recorder(2, flag_index=1)
    port.receive_value_with_index(0, _V)
    for _ in range(5):
        port.receive_value_with_index(1, _V)
    assert len(fired) == 5


def test_receive_unflagged_slot_never_fires():
    port, fired = _port_with_recorder(2, flag_index=1)
    port.receive_value_with_index(0, _V)
    port.receive_value_with_index(1, _V)  # fire (flagged)
    port.receive_value_with_index(0, _V)  # unflagged: no fire even when full
    port.receive_value_with_index(0, _V)
    assert len(fired) == 1


def test_receive_delivers_current_store_contents():
    port, fired = _port_with_recorder(2, flag_index=1)
    a = [np.array([1.0], dtype=np.float32)]
    b = [np.array([2.0], dtype=np.float32)]
    c = [np.array([3.0], dtype=np.float32)]

    port.receive_value_with_index(0, a)
    port.receive_value_with_index(1, b)
    assert float(fired[0][0][0]) == 1.0 and float(fired[0][1][0]) == 2.0

    port.receive_value_with_index(0, c)  # overwrite slot 0 (no fire)
    port.receive_value_with_index(1, b)  # fire with updated slot 0
    assert float(fired[1][0][0]) == 3.0


import timeit
import random


def test_list_vs_dict():
    N = 10**6
    # Prepare a list and a dict (dict keyed by index, same kind of random values)
    data_list = [random.random() for _ in range(N)]
    data_dict = {i: random.random() for i in range(N)}

    def sum_list(lst):
        total = 0
        for val in lst:
            total += val
        return total

    def sum_dict_values(dct):
        total = 0
        for val in dct.values():
            total += val
        return total

    # Run 10 times and measure the average duration
    list_time = timeit.timeit(lambda: sum_list(data_list), number=10)
    dict_time = timeit.timeit(lambda: sum_dict_values(data_dict), number=10)

    print(f"List iteration time: {list_time:.6f} seconds")
    print(f"Dict values iteration time: {dict_time:.6f} seconds")
