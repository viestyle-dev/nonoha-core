"""Benchmarks for port value serialization (port_values_to_bytes)."""

import numpy as np

from nonoha_core.port import port_values_to_bytes
from nonoha_core.data_type import DataType, PortValueType


def test_to_bytes_f32_small(benchmark):
    """Serialize 1 Float32 value with 10 elements."""
    values = [np.ones((1, 10), dtype=np.float32)]
    types = [PortValueType(DataType.Float32)]

    def do_serialize():
        buf = bytearray()
        port_values_to_bytes(values, types, buf)
        return buf

    benchmark(do_serialize)


def test_to_bytes_f32_large(benchmark):
    """Serialize 1 Float32 value with 10,000 elements."""
    values = [np.ones((1, 10_000), dtype=np.float32)]
    types = [PortValueType(DataType.Float32)]

    def do_serialize():
        buf = bytearray()
        port_values_to_bytes(values, types, buf)
        return buf

    benchmark(do_serialize)


def test_to_bytes_multi_value(benchmark):
    """Serialize 4 values of mixed types."""
    values = [
        np.ones((1, 100), dtype=np.float32),
        np.ones((1, 50), dtype=np.float64),
        np.ones((1, 200), dtype=np.int16),
        np.ones((1, 10), dtype=np.uint8),
    ]
    types = [
        PortValueType(DataType.Float32),
        PortValueType(DataType.Float64),
        PortValueType(DataType.Int16),
        PortValueType(DataType.Uint8),
    ]

    def do_serialize():
        buf = bytearray()
        port_values_to_bytes(values, types, buf)
        return buf

    benchmark(do_serialize)


def test_to_bytes_string(benchmark):
    """Serialize String array with 100 elements."""
    strings = np.array([["hello"] * 100])
    types = [PortValueType(DataType.String)]

    def do_serialize():
        buf = bytearray()
        port_values_to_bytes([strings], types, buf)
        return buf

    benchmark(do_serialize)
