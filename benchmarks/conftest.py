"""Shared fixtures for nonoha-core benchmarks."""

import tracemalloc
from dataclasses import dataclass

import pytest


@dataclass
class MemoryTracker:
    """Tracks peak memory allocation via tracemalloc."""

    peak: int = 0

    def start(self):
        tracemalloc.start()

    def stop(self) -> int:
        _, self.peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return self.peak

    def assert_below(self, limit_bytes: int, label: str = ""):
        msg = f"Peak memory {self.peak:,} bytes exceeds {limit_bytes:,} bytes"
        if label:
            msg = f"[{label}] {msg}"
        assert self.peak < limit_bytes, msg


@pytest.fixture
def memory_tracker():
    return MemoryTracker()
