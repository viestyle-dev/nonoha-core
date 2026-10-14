import numpy as np
import logging

from nonoha_core.node import (
    BaseNode,
    NodeDoc,
    PropertyDataType,
    replace_node_input_port,
)
from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)
from nonoha_core.data_type import DataType, PortValueType, name_to_port_value_type

logger = logging.getLogger(__name__)


class StringFormatNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Format multiple input values into a string using a format template",
            category="String",
            inputs={"in": ""},
            outputs={"formatted": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "StringFormat")

        format_str: str = "record,{},{:.2f}"
        in_types = [PortValueType(DataType.String), PortValueType(DataType.Float32)]

        input_in = StaticTypeInputPort("in", in_types)
        input_in.subscribe(id(self), self._on_input_in)
        output_formatted = StaticTypeOutputPort(
            "formatted", [PortValueType(DataType.String)]
        )

        self._in_types = in_types
        self._input_in = input_in
        self._output_formatted = output_formatted
        self._format_str = format_str

        self.inputs[input_in.name] = input_in
        self.outputs[output_formatted.name] = output_formatted

        self.properties["format_str"] = format_str
        self.properties["in_types"] = ", ".join([t.name for t in in_types])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract and validate properties
        format_str = self._format_str
        if "format_str" in properties:
            format_str_prop = properties["format_str"]
            if not isinstance(format_str_prop, str):
                raise ValueError("format_str must be a string")
            format_str = format_str_prop

        in_types = self._in_types
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a string")
            in_types = [
                name_to_port_value_type(t.strip()) for t in in_types_str.split(",")
            ]
            if any(t.shape != () for t in in_types):
                raise ValueError("Only scalar types are supported for in_types")

        # 2. Create new ports if necessary
        new_input_in = self._input_in
        if in_types != self._in_types:
            new_input_in = StaticTypeInputPort("in", in_types)

        # 3. (No internal state recalculation needed)

        # 4. Replace ports atomically if changed
        if new_input_in is not self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        # 5. Update instance variables and properties dictionary
        self._in_types = in_types
        self._format_str = format_str
        self.properties["format_str"] = format_str
        self.properties["in_types"] = ", ".join([t.name for t in in_types])

        # 6. Notify graph of updates
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        batch_size = len(values[0])
        formatted = np.empty(batch_size, dtype=np.dtypes.StringDType())  # type: ignore

        try:
            for i in range(batch_size):
                args = [v[i] for v in values]
                formatted[i] = self._format_str.format(*args)
        except Exception as e:
            logger.warning(f"{self.name}: format error: {e}")
            return

        self._output_formatted.dispatch([formatted])
