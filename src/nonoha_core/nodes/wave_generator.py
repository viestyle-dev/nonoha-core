import numpy as np

from nonoha_core.port import (
    StaticTypeInputPort,
    StaticTypeOutputPort,
)
from nonoha_core.node import BaseNode, NodeDoc
from nonoha_core.data_type import DataType, PortValueType, PropertyDataType


class WaveType:
    Sin = "sin"
    # Square = "square"  # TODO: Implement square wave


class WaveGeneratorNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Generate sine wave signal with configurable frequency, amplitude, and modulation",
            category="Signal Generation",
            inputs={"times": "", "modulation": ""},
            outputs={"series": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "WaveGenerator")

        self._frequency: float = 440.0
        self._amplitude = 1.0
        self._offset = 0.0

        self._input_times = StaticTypeInputPort(
            "times", [PortValueType(DataType.Float32)]
        )
        self._input_modulation = StaticTypeInputPort(
            "modulation", [PortValueType(DataType.Float32)]
        )
        self._output_series = StaticTypeOutputPort(
            "series", [PortValueType(DataType.Float32)]
        )

        self._input_times.subscribe(id(self), self._on_times)

        self._input_modulation.subscribe(id(self), self._on_modulation)
        self._modulation = np.array([0.0])

        self.inputs[self._input_times.name] = self._input_times
        self.inputs[self._input_modulation.name] = self._input_modulation
        self.outputs[self._output_series.name] = self._output_series

        self.properties["frequency"] = self._frequency
        self.properties["amplitude"] = self._amplitude
        self.properties["offset"] = self._offset

    def set_properties(self, properties: dict[str, PropertyDataType]):
        frequency = self._frequency
        amplitude = self._amplitude
        offset = self._offset

        if "frequency" in properties:
            frequency = float(properties["frequency"])
        if "amplitude" in properties:
            amplitude = float(properties["amplitude"])
        if "offset" in properties:
            offset = float(properties["offset"])

        self._frequency = frequency
        self._amplitude = amplitude
        self._offset = offset

        self.properties["frequency"] = frequency
        self.properties["amplitude"] = amplitude
        self.properties["offset"] = offset

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_modulation(self, values: list[np.ndarray]):
        self._modulation = values[0]

    def _on_times(self, values: list[np.ndarray]):
        times = values[0]
        series = (
            np.sin(2 * np.pi * self._frequency * times + self._modulation)
            * self._amplitude
            + self._offset
        )
        self._output_series.dispatch([series])
