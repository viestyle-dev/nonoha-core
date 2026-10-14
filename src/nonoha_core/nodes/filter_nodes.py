import logging
import traceback

import numpy as np

from nonoha_core.node import (
    BaseNode,
    NodeDoc,
    PropertyDataType,
    replace_node_input_port,
    replace_node_output_port,
)
from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)
from nonoha_core.data_type import DataType, PortValueType, name_to_port_value_type

logger = logging.getLogger(__name__)


class EmaFilterNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Exponential Moving Average filter for smoothing time-series data",
            category="Filter",
            inputs={"series": "", "reset": ""},
            outputs={"series": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "EmaFilter")

        in_type = PortValueType(DataType.Float32)
        alpha = 0.1

        input_series = StaticTypeInputPort("series", [in_type])
        output_series = StaticTypeOutputPort("series", [in_type])
        input_reset = StaticTypeInputPort("reset", [PortValueType(DataType.Any)])

        input_series.subscribe(id(self), self._on_input_series)
        input_reset.subscribe(id(self), self._on_input_reset)

        self._alpha = alpha
        self._in_type = in_type
        # Previous value, stored with the configured shape
        self._prev = np.zeros(in_type.shape, dtype=np.float64)

        self._input_series = input_series
        self._output_series = output_series
        self._input_reset = input_reset

        self.inputs[input_series.name] = input_series
        self.inputs[input_reset.name] = input_reset
        self.outputs[output_series.name] = output_series

        self.properties["in_type"] = in_type.name
        self.properties["alpha"] = alpha

    def set_properties(self, properties: dict[str, PropertyDataType]):
        alpha = self._alpha
        if "alpha" in properties:
            alpha = float(properties["alpha"])
            if alpha <= 0 or alpha > 1:
                raise ValueError("Alpha must be in range (0, 1]")

        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)

            if in_type.data_type not in [DataType.Float32, DataType.Float64]:
                raise ValueError("In type must be Float32 or Float64")

        new_input_series = self._input_series
        new_output_series = self._output_series
        if in_type != self._in_type:
            new_input_series = StaticTypeInputPort("series", [in_type])
            new_output_series = StaticTypeOutputPort("series", [in_type])

            # Reset prev when the shape changes
            self._prev = np.zeros(in_type.shape, dtype=np.float64)

        # Replace the ports
        if new_input_series != self._input_series:
            replace_node_input_port(
                self, self._input_series, new_input_series, self._on_input_series
            )
            self._input_series = new_input_series

        if new_output_series != self._output_series:
            replace_node_output_port(self, self._output_series, new_output_series)
            self._output_series = new_output_series

        self._alpha = alpha
        self._in_type = in_type

        self.properties["in_type"] = in_type.name
        self.properties["alpha"] = alpha

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_reset(self, values: list[PortValue]):
        self._prev.fill(0.0)

    def _on_input_series(self, values: list[PortValue]):
        series: np.ndarray = values[0]

        try:
            filtered = np.zeros_like(series)

            # Per-sample processing, independent of the element shape
            for index in range(len(series)):
                current = series[index]
                # NumPy array ops handle the element shape automatically
                filtered[index] = self._prev = (
                    self._alpha * current + (1 - self._alpha) * self._prev
                )
        except Exception as e:
            logger.warning(f"{self.name=}: {e=}")
            traceback.print_exc()
            return

        self._output_series.dispatch([filtered])
