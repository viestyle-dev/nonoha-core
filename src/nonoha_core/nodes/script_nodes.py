from types import CodeType
import numpy as np
import logging
import json
import time

from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)
from nonoha_core.node import BaseNode, NodeDoc, replace_node_input_port, replace_node_output_port
from nonoha_core.data_type import (
    DataType,
    PortValueType,
    PropertyDataType,
    data_type_to_numpy_dtype,
    name_to_port_value_type,
)

logger = logging.getLogger(__name__)


class PureScriptNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Execute custom Python script to transform input values",
            category="Script",
            inputs={"values": ""},
            outputs={"out": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "PureScript")

        source: str = ""
        in_value_type_list = [
            PortValueType(DataType.Float32),
            PortValueType(DataType.Float32),
        ]
        out_value_type_list = [PortValueType(DataType.Float32)]

        input_in = StaticTypeInputPort("values", in_value_type_list)
        output_out = StaticTypeOutputPort("out", out_value_type_list)

        input_in.subscribe(id(self), self._on_input_in)

        self._source = source
        self._compiled_code: CodeType | None = None
        self._in_value_type_list = in_value_type_list
        self._out_value_type_list = out_value_type_list
        self._out_numpy_dtypes = tuple(
            data_type_to_numpy_dtype(vt.data_type) for vt in out_value_type_list
        )
        self._out_valid_checks = tuple(
            (i, d) for i, d in enumerate(self._out_numpy_dtypes) if d is not None
        )
        self._out_len = len(out_value_type_list)
        self._input_in = input_in
        self._output_out = output_out
        self._env_template = {
            "__builtins__": {
                "print": print,
                "range": range,
                "min": min,
                "max": max,
                "len": len,
            },
            "np": np,
            "json": json,
        }

        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

        self.properties["source"] = source
        self.properties["in_value_type_list"] = ",".join(
            [value_type.name for value_type in in_value_type_list]
        )
        self.properties["out_value_type_list"] = ",".join(
            [value_type.name for value_type in out_value_type_list]
        )

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract properties
        source = self._source
        if "source" in properties:
            source = str(properties["source"])

        in_value_type_list = self._in_value_type_list
        if "in_value_type_list" in properties:
            in_value_type_list_str = properties["in_value_type_list"]
            if not isinstance(in_value_type_list_str, str):
                raise ValueError("in_value_type_list must be a string")
            in_value_type_list = [
                name_to_port_value_type(name)
                for name in in_value_type_list_str.split(",")
            ]

        out_value_type_list = self._out_value_type_list
        if "out_value_type_list" in properties:
            out_value_type_list_str = properties["out_value_type_list"]
            if not isinstance(out_value_type_list_str, str):
                raise ValueError("out_value_type_list must be a string")
            out_value_type_list = [
                name_to_port_value_type(name)
                for name in out_value_type_list_str.split(",")
            ]

        # 2. Prepare new ports
        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_value_type_list != self._in_value_type_list:
            new_input_in = StaticTypeInputPort("values", in_value_type_list)
        if out_value_type_list != self._out_value_type_list:
            new_output_out = StaticTypeOutputPort("out", out_value_type_list)

        # 3. Update internal state
        if source != self._source:
            self._compiled_code = (
                None
                if not source.strip()
                else compile(source, f"<script_{self.name}>", "exec")
            )
            self._source = source

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in
            self._in_value_type_list = in_value_type_list

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out
            self._out_value_type_list = out_value_type_list
            self._out_numpy_dtypes = tuple(
                data_type_to_numpy_dtype(vt.data_type) for vt in out_value_type_list
            )
            self._out_valid_checks = tuple(
                (i, d) for i, d in enumerate(self._out_numpy_dtypes) if d is not None
            )
            self._out_len = len(out_value_type_list)

        self.properties["source"] = source
        self.properties["in_value_type_list"] = ",".join(
            vt.name for vt in in_value_type_list
        )
        self.properties["out_value_type_list"] = ",".join(
            vt.name for vt in out_value_type_list
        )

        # 4. Notify graph
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        if self._compiled_code is None:
            return

        try:
            env = self._env_template.copy()
            env["v"] = values
            env["out"] = None

            # # start measuring execution time
            # start_time = time.perf_counter()

            exec(self._compiled_code, env, env)

            # # stop measuring execution time
            # end_time = time.perf_counter()
            # execution_time = (end_time - start_time) * 1000  # convert to milliseconds

            # logger.info(f"Script {self.name} executed in {execution_time:.3f} ms")

            out = env.get("out")

        except Exception as e:
            logger.warning(f"Error in script {self.name}: {e}")
            return

        if out is None:
            return

        if not isinstance(out, list):
            logger.warning(f"{self.name}: Output must be a list, but got {type(out)}")
            return

        if len(out) != self._out_len:
            logger.warning(
                f"{self.name}: Output length must be {self._out_len}, but got {len(out)}"
            )
            return

        for i, expected_dtype in self._out_valid_checks:
            v = out[i]
            if not isinstance(v, np.ndarray) or v.dtype != expected_dtype:
                actual = f"ndarray({v.dtype}, {list(v.shape)})" if isinstance(v, np.ndarray) else type(v).__name__
                logger.warning(f"{self.name}: Output[{i}] expected ndarray({expected_dtype}), got {actual}")
                return

        self._output_out.dispatch(out)
