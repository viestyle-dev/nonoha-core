import numpy as np
import logging

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


class MeanNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Arithmetic mean of array elements along an axis",
            category="Statistics",
            inputs={"in": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Mean")

        in_type = PortValueType(DataType.Float32)
        axis: int | None = 0
        out_type = self._get_out_type(in_type, axis)

        input_in = StaticTypeInputPort("in", [in_type])
        input_in.subscribe(id(self), self._on_input_in)

        output_out = StaticTypeOutputPort("out", [out_type])

        self._input_in = input_in
        self._output_out = output_out
        self._in_type = in_type
        self._axis = axis

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis

    def _get_out_type(self, in_type: PortValueType, axis: int | None) -> PortValueType:
        if axis is None:
            return PortValueType(in_type.data_type)
        if axis == 0:
            return PortValueType(in_type.data_type, in_type.shape)

        np_in_shape = (-1, *in_type.shape)
        out_shape = (*np_in_shape[:axis], *np_in_shape[axis + 1 :])
        out_shape = out_shape[1:]

        return PortValueType(in_type.data_type, out_shape)

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("In type must be a string")

            in_type = name_to_port_value_type(in_type_str)

            if in_type.data_type not in [DataType.Float32, DataType.Float64]:
                raise ValueError("In type must be Float32 or Float64")

        axis = self._axis
        if "axis" in properties:
            axis = None if (val := properties.get("axis", "")) == "" else int(val)

        new_input_in = self._input_in
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])

        new_output_out = self._output_out
        if in_type != self._in_type or axis != self._axis:
            out_type = self._get_out_type(in_type, axis)
            new_output_out = StaticTypeOutputPort("out", [out_type])

        # ---

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        self._in_type = in_type
        self._axis = axis
        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis if axis is not None else ""

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        out = np.mean(values[0], axis=self._axis)

        if self._axis is None or self._axis == 0:
            out = np.expand_dims(out, axis=0)

        self._output_out.dispatch([out])


class IncrementalMeanNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Running mean updated incrementally with each input batch (Welford + Kahan)",
            category="Statistics",
            inputs={"in": "", "reset": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "IncrementalMean")

        in_type = PortValueType(DataType.Float32)

        input_in = StaticTypeInputPort("in", [in_type])
        input_in.subscribe(id(self), self._on_input_in)

        input_reset = StaticTypeInputPort("reset", [PortValueType(DataType.Any)])
        input_reset.subscribe(id(self), self._on_input_reset)

        output_out = StaticTypeOutputPort("out", [in_type])
        # output_count = StaticTypePort("count", PortDirection.OUTPUT, [DataType.Uint32])

        self._in_type = in_type
        self._mean = np.zeros(in_type.shape, dtype=np.float64)
        self._c_mean = np.zeros(
            in_type.shape, dtype=np.float64
        )  # Kahan summation algorithm
        self._n = 0

        self._input_in = input_in
        self._output_out = output_out

        self.inputs[input_in.name] = input_in
        self.inputs[input_reset.name] = input_reset
        self.outputs[output_out.name] = output_out

        self.properties["in_type"] = in_type.name

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract properties
        in_type = self._in_type

        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("In type must be a string")

            in_type = name_to_port_value_type(in_type_str)

            if in_type.data_type not in [DataType.Float32, DataType.Float64]:
                raise ValueError("In type must be Float32 or Float64")

        # 2. Prepare new ports
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_type != self._in_type:
            new_input_in = StaticTypeInputPort("in", [in_type])
            new_output_out = StaticTypeOutputPort("out", [in_type])

        # 3. Update internal state
        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        if in_type != self._in_type:
            self._mean = np.zeros(in_type.shape)
            self._c_mean = np.zeros(in_type.shape)
            self._n = 0

        self._in_type = in_type
        self.properties["in_type"] = in_type.name

        # 4. Notify graph
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_reset(self, values: list[PortValue]):
        self._mean.fill(0.0)
        self._c_mean.fill(0.0)
        self._n = 0

        # self._output_count.dispatch([np.array([self._n])])

    def _on_input_in(self, values: list[PortValue]):
        series = values[0]

        n_batch = len(series)
        batch_mean = np.mean(series, axis=0)

        if self._n == 0:
            self._mean[...] = batch_mean
            self._c_mean.fill(0.0)
            self._n = n_batch
        else:
            # --- Welford (mean update) --------------------------------- #
            n_total = self._n + n_batch
            delta = batch_mean - self._mean
            incr = delta * (n_batch / n_total)  # increment to add

            # --- Kahan compensated summation: mean += incr ------------- #
            y = incr - self._c_mean
            t = self._mean + y
            self._c_mean[...] = (t - self._mean) - y  # new compensation term
            self._mean[...] = t

            self._n = n_total

        self._output_out.dispatch([np.array([self._mean])])
