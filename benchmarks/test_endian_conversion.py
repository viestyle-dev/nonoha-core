"""Benchmarks for numpy endianness conversion patterns.

Migrated from tests/test_endian_benchmark.py with pytest-benchmark integration.
"""

import sys

import numpy as np


def test_frombuffer_big_to_native(benchmark):
    """Deserialize 100K big-endian float32 to native order."""
    source = np.random.rand(100_000).astype(">f4")
    data = source.tobytes()

    def do_convert():
        return np.frombuffer(data, dtype=">f4").astype("<f4", copy=False)

    result = benchmark(do_convert)
    assert result.dtype.byteorder in ("=", "<", "|")


def test_astype_native_to_big(benchmark):
    """Serialize 100K native float32 to big-endian (network byte order)."""
    native = np.random.rand(100_000).astype(np.float32)

    def do_convert():
        return native.astype(">f4", copy=False)

    benchmark(do_convert)


def test_total_cost_convert_once(benchmark):
    """Convert once + 10 native ops vs operating on swapped data."""
    source = np.random.rand(100_000).astype(">f4")
    data = source.tobytes()

    def do_convert_and_compute():
        arr = np.frombuffer(data, dtype=">f4").astype("<f4", copy=False)
        for _ in range(10):
            arr = arr * 2.0 + 1.0
        return arr

    benchmark(do_convert_and_compute)
