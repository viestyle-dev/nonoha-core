"""Memory benchmarks for nonoha-core operations."""

import numpy as np

from nonoha_core.port import StaticTypeOutputPort, PortValue
from nonoha_core.data_type import DataType, PortValueType


def _noop_callback(values: list[PortValue]) -> None:
    pass


def test_memory_1000_callbacks(memory_tracker):
    """Peak memory with 1000 callback subscriptions on a port."""
    memory_tracker.start()

    port = StaticTypeOutputPort("out", [PortValueType(DataType.Float32)])
    for i in range(1000):
        port.subscribe(i, _noop_callback)

    memory_tracker.stop()
    memory_tracker.assert_below(5 * 1024 * 1024, "1000 callbacks")


def test_memory_large_dispatch(memory_tracker):
    """Peak memory during dispatch of f32[100000] to 10 callbacks."""
    port = StaticTypeOutputPort(
        "out", [PortValueType(DataType.Float32, (100_000,))]
    )
    for i in range(10):
        port.subscribe(i, _noop_callback)

    memory_tracker.start()

    values = [np.ones((1, 100_000), dtype=np.float32)]
    for _ in range(100):
        port.dispatch(values)

    memory_tracker.stop()
    memory_tracker.assert_below(10 * 1024 * 1024, "large dispatch")
