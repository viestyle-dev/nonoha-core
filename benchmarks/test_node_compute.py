"""Benchmarks for individual node computation throughput."""

import numpy as np

from nonoha_core.nodes.arithmetic_operation_nodes import AddNode
from nonoha_core.nodes.fft_nodes import FftNode
from nonoha_core.nodes.buffer_nodes import ValuesBufferNode
from nonoha_core.data_type import DataType, PortValueType


def test_add_node(benchmark):
    """AddNode: 2-input f32[1000] element-wise addition."""
    node = AddNode("bench_add")
    node.set_properties({"in_types": "f32[1000],f32[1000]"})

    a = np.ones((1, 1000), dtype=np.float32)
    b = np.ones((1, 1000), dtype=np.float32) * 2.0

    input_port = node._input_values

    def do_compute():
        input_port.dispatch([a, b])

    benchmark(do_compute)


def test_fft_node(benchmark):
    """FftNode: rfft of f32[1024] windowed signal."""
    node = FftNode("bench_fft")

    signal = np.sin(np.linspace(0, 2 * np.pi * 10, 1024)).astype(np.float32)
    batched = signal[np.newaxis, :]

    input_port = node._input_vector

    def do_compute():
        input_port.dispatch([batched])

    benchmark(do_compute)


def test_values_buffer_node(benchmark):
    """ValuesBufferNode: 100 dispatches into buffer_size=256."""
    node = ValuesBufferNode("bench_buffer")
    node.set_properties({"buffer_size": 256, "in_types": "f32"})

    value = np.array([[1.0]], dtype=np.float32)

    input_port = node.inputs["values"]

    def do_fill():
        for _ in range(100):
            input_port.dispatch([value])

    benchmark(do_fill)
