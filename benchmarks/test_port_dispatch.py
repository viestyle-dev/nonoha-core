"""Benchmarks for port dispatch throughput."""

import numpy as np

from nonoha_core.port import (
    StaticTypeInputPort,
    StaticTypeOutputPort,
    PortValue,
)
from nonoha_core.data_type import DataType, PortValueType


def _noop_callback(values: list[PortValue]) -> None:
    pass


def _make_port_with_callbacks(
    n_callbacks: int, shape: tuple[int, ...] = (100,)
) -> StaticTypeOutputPort:
    port = StaticTypeOutputPort("out", [PortValueType(DataType.Float32, shape)])
    for i in range(n_callbacks):
        port.subscribe(i, _noop_callback)
    return port


def test_dispatch_10_callbacks(benchmark):
    """Dispatch to 10 subscribers — typical small graph fan-out."""
    port = _make_port_with_callbacks(10, (100,))
    values = [np.ones((1, 100), dtype=np.float32)]
    benchmark(port.dispatch, values)


def test_dispatch_100_callbacks(benchmark):
    """Dispatch to 100 subscribers — stress test."""
    port = _make_port_with_callbacks(100, (100,))
    values = [np.ones((1, 100), dtype=np.float32)]
    benchmark(port.dispatch, values)


def test_dispatch_large_payload(benchmark):
    """Dispatch large array (100k elements) to 10 subscribers."""
    port = _make_port_with_callbacks(10, (100_000,))
    values = [np.ones((1, 100_000), dtype=np.float32)]
    benchmark(port.dispatch, values)


def test_receive_value_with_index(benchmark):
    """InputPort conditional dispatch — 4-value port, last triggers."""
    port = StaticTypeInputPort(
        "in",
        [
            PortValueType(DataType.Float32, (10,)),
            PortValueType(DataType.Float32, (10,)),
            PortValueType(DataType.Float32, (10,)),
            PortValueType(DataType.Float32, (10,)),
        ],
    )
    port.dispatch_flags = [False, False, False, True]
    port.subscribe(0, _noop_callback)

    # Pre-fill first 3 values
    for i in range(3):
        port.values_store[i] = np.ones((1, 10), dtype=np.float32)

    trigger_values = [np.ones((1, 10), dtype=np.float32)]

    def do_receive():
        port.receive_value_with_index(3, trigger_values)

    benchmark(do_receive)


def test_dispatch_chain_10(benchmark):
    """Linear chain of 10 output→input dispatch cascades."""
    port_type = PortValueType(DataType.Float32, (100,))
    ports = []
    for i in range(10):
        out_port = StaticTypeOutputPort(f"out_{i}", [port_type])
        in_port = StaticTypeInputPort(f"in_{i}", [port_type])
        in_port.dispatch_flags = [True]
        ports.append((out_port, in_port))

    # Chain: out_0 → in_0 → out_1 → in_1 → ... → out_9
    for i in range(len(ports) - 1):
        out_port, in_port = ports[i]
        next_out, _ = ports[i + 1]

        def _forward(values, _next=next_out):
            _next.dispatch(values)

        in_port.subscribe(i, _forward)
        out_port.subscribe(
            i, lambda values, _inp=in_port: _inp.receive_value_with_index(0, values)
        )

    # Last input does nothing
    _, last_in = ports[-1]
    last_in.subscribe(999, _noop_callback)

    first_out = ports[0][0]
    values = [np.ones((1, 100), dtype=np.float32)]

    benchmark(first_out.dispatch, values)
