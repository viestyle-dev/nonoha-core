"""Benchmarks for port subscribe/unsubscribe operations."""

from nonoha_core.port import StaticTypeOutputPort, PortValue
from nonoha_core.data_type import DataType, PortValueType


def _noop_callback(values: list[PortValue]) -> None:
    pass


def test_subscribe_1000(benchmark):
    """Subscribe 1000 callbacks sequentially."""
    def do_subscribe():
        port = StaticTypeOutputPort("out", [PortValueType(DataType.Float32)])
        for i in range(1000):
            port.subscribe(i, _noop_callback)

    benchmark(do_subscribe)


def test_unsubscribe_middle(benchmark):
    """Unsubscribe 200 callbacks from the middle of 1000."""
    port = StaticTypeOutputPort("out", [PortValueType(DataType.Float32)])

    def setup():
        for i in range(1000):
            port.subscribe(i, _noop_callback)

    def do_unsubscribe():
        for i in range(400, 600):
            port.unsubscribe(i)

    benchmark.pedantic(do_unsubscribe, setup=setup, rounds=100)


def test_subscribe_unsubscribe_cycle(benchmark):
    """100 subscribe→unsubscribe cycles on same port."""
    port = StaticTypeOutputPort("out", [PortValueType(DataType.Float32)])

    def do_cycle():
        for i in range(100):
            port.subscribe(i + 10000, _noop_callback)
        for i in range(100):
            port.unsubscribe(i + 10000)

    benchmark(do_cycle)
