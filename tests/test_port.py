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
