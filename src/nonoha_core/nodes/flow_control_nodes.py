# flow_control_nodes — Flow control nodes for dispatch routing and gating.

from typing import Any
import asyncio
import logging

import numpy as np

from nonoha_core.node import (
    BaseNode,
    NodeDoc,
    replace_node_input_port,
    replace_node_output_port,
)
from nonoha_core.data_type import (
    DataType,
    PortValueType,
    PropertyDataType,
    name_to_port_value_type,
)
from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)

logger = logging.getLogger(__name__)

# <https://dev.epicgames.com/documentation/en-us/unreal-engine/flow-control-in-unreal-engine>


class OneShotGateNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Pass one value through, then auto-lock until unlocked",
            category="Flow Control",
            inputs={
                "in": "Data to gate (passes once, then locks)",
                "unlock": "Any signal to unlock the gate",
            },
            outputs={
                "out": "Gated output (same type as in)",
            },
        )

    PROPERTIES = {
        "value_type_list": {
            "description": "Comma-separated port value types",
            "data_type": "str",
            "default_value": "f32",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "OneShotGate")

        value_type_list = [
            name_to_port_value_type(name.strip())
            for name in str(self.properties["value_type_list"]).split(",")
        ]

        input_in = StaticTypeInputPort(
            "in",
            value_type_list,
        )
        input_in.subscribe(id(self), self._on_input_in)

        input_unlock = StaticTypeInputPort(
            "unlock",
            [PortValueType(DataType.Any)],
        )
        input_unlock.subscribe(id(self), self._on_input_unlock)

        output_out = StaticTypeOutputPort(
            "out",
            value_type_list,
        )

        self._input_in = input_in
        self._input_unlock = input_unlock
        self._output_out = output_out
        self._value_type_list = value_type_list
        self._locked = False

        self.inputs[input_in.name] = input_in
        self.inputs[input_unlock.name] = input_unlock
        self.outputs[output_out.name] = output_out

    def set_properties(self, properties: dict[str, PropertyDataType]):
        value_type_list = self._value_type_list

        if "value_type_list" in properties:
            value_type_list_str = properties["value_type_list"]
            if not isinstance(value_type_list_str, str):
                raise ValueError("value_type_list must be a string")
            value_type_list = [
                name_to_port_value_type(name.strip())
                for name in value_type_list_str.split(",")
            ]

        new_input_in = self._input_in
        new_output_out = self._output_out
        if value_type_list != self._value_type_list:
            new_input_in = StaticTypeInputPort("in", value_type_list)
            new_output_out = StaticTypeOutputPort("out", value_type_list)

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        self._value_type_list = value_type_list
        self.properties["value_type_list"] = ",".join([t.name for t in value_type_list])

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_in(self, values: list[PortValue]):
        if self._locked:
            return
        self._locked = True
        self._output_out.dispatch(values)

    def _on_input_unlock(self, values: list[PortValue]):
        self._locked = False


class SequenceNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        props = properties or {}
        count = int(props.get("count", 2))
        return NodeDoc(
            description="Dispatch input to multiple outputs in order",
            category="Flow Control",
            inputs={"in": "Input values to fan out"},
            outputs={f"out_{i}": f"Output copy {i}" for i in range(count)},
        )

    PROPERTIES = {
        "count": {
            "description": "Number of output ports",
            "data_type": "i32",
            "default_value": 2,
        },
        "value_type_list": {
            "description": "Comma-separated port value types",
            "data_type": "str",
            "default_value": "f32",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Sequence")

        count: int = int(self.properties["count"])

        value_type_list = [
            name_to_port_value_type(name.strip())
            for name in str(self.properties["value_type_list"]).split(",")
        ]
        input_values = StaticTypeInputPort(
            "in",
            value_type_list,
        )
        input_values.subscribe(id(self), self._on_input_values)

        output_values_list = [
            StaticTypeOutputPort(
                f"out_{i}",
                value_type_list,
            )
            for i in range(count)
        ]

        self._input_values = input_values
        self._output_values_list = output_values_list
        self._count = count
        self._value_type_list = value_type_list

        self.inputs[input_values.name] = input_values
        for output_values in output_values_list:
            self.outputs[output_values.name] = output_values

    def set_properties(self, properties: dict[str, PropertyDataType]):
        count = self._count
        value_type_list = self._value_type_list

        if "count" in properties:
            count = int(properties["count"])
            if count < 1:
                raise ValueError("count must be at least 1")
        if "value_type_list" in properties:
            if not isinstance(properties["value_type_list"], str):
                raise ValueError("value_type_list must be a string")
            value_type_list = [
                name_to_port_value_type(name.strip())
                for name in properties["value_type_list"].split(",")
            ]

        type_changed = value_type_list != self._value_type_list
        count_changed = count != self._count

        if type_changed or count_changed:
            # Input port: replace if type changed
            if type_changed:
                new_input = StaticTypeInputPort("in", value_type_list)
                replace_node_input_port(
                    self, self._input_values, new_input, self._on_input_values
                )
                self._input_values = new_input

            # Output ports: overlap/remove/add pattern
            old_count = self._count
            overlap = min(old_count, count)
            new_output_list: list[StaticTypeOutputPort] = []

            for i in range(overlap):
                if type_changed:
                    new_port = StaticTypeOutputPort(f"out_{i}", value_type_list)
                    replace_node_output_port(
                        self, self._output_values_list[i], new_port
                    )
                    new_output_list.append(new_port)
                else:
                    new_output_list.append(self._output_values_list[i])

            for i in range(overlap, old_count):
                old_port = self._output_values_list[i]
                if self.parent_graph is not None:
                    self.parent_graph.disconnect_all_from_node_output(
                        self.name, old_port.name
                    )
                self.outputs.pop(old_port.name)

            for i in range(overlap, count):
                new_port = StaticTypeOutputPort(f"out_{i}", value_type_list)
                new_output_list.append(new_port)
                self.outputs[new_port.name] = new_port

            self._output_values_list = new_output_list
            self._count = count
            self._value_type_list = value_type_list

        self.properties["count"] = count
        self.properties["value_type_list"] = ",".join(
            [value_type.name for value_type in value_type_list]
        )

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, values_any: list[Any]):
        for output_values in self._output_values_list:
            output_values.dispatch(values_any)


class YieldNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Defer dispatch to the next event loop iteration and flush outputs",
            category="Flow Control",
            inputs={"in": "Input values to defer"},
            outputs={"out": "Deferred output (dispatched on next event loop tick)"},
        )

    PROPERTIES = {
        "in_types": {
            "description": "Comma-separated input value types",
            "data_type": "str",
            "default_value": "f32",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Yield")

        in_types = [
            name_to_port_value_type(name.strip())
            for name in str(self.properties["in_types"]).split(",")
        ]

        input_in = StaticTypeInputPort(
            "in",
            in_types,
        )
        output_out = StaticTypeOutputPort(
            "out",
            in_types,
        )
        input_in.subscribe(id(self), self._on_input_in)

        self._main_loop: asyncio.AbstractEventLoop | None = None
        self._handle = None

        self._input_in = input_in
        self._output_out = output_out
        self.inputs[input_in.name] = input_in
        self.outputs[output_out.name] = output_out

    def activate(self):
        self._main_loop = asyncio.get_running_loop()

    def set_properties(self, properties: dict[str, PropertyDataType]):
        in_types = self._input_in.value_type_list
        if "in_types" in properties:
            in_types_str = properties["in_types"]
            if not isinstance(in_types_str, str):
                raise ValueError("in_types must be a comma-separated string")
            in_types = [
                name_to_port_value_type(name.strip())
                for name in in_types_str.split(",")
            ]

        new_input_in = self._input_in
        new_output_out = self._output_out
        if in_types != self._input_in.value_type_list:
            new_input_in = StaticTypeInputPort("in", in_types)
            new_output_out = StaticTypeOutputPort("out", in_types)

        if new_input_in != self._input_in:
            replace_node_input_port(
                self, self._input_in, new_input_in, self._on_input_in
            )
            self._input_in = new_input_in

        if new_output_out != self._output_out:
            replace_node_output_port(self, self._output_out, new_output_out)
            self._output_out = new_output_out

        self.properties["in_types"] = ",".join(
            [value_type.name for value_type in in_types]
        )

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _process_input(self, values: list[PortValue]):
        self._output_out.dispatch(values)

        if self.parent_graph is not None:
            self.parent_graph.flush_outputs()

    def _on_input_in(self, values: list[PortValue]):
        if self._main_loop is None:
            return
        self._main_loop.call_soon(self._process_input, values)


class ValuesLatchNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Latch input values and re-dispatch on trigger",
            category="Flow Control",
            inputs={
                "dispatch": "Trigger to re-dispatch the latched values",
                "values": "Values to latch (stored for later dispatch)",
            },
            outputs={
                "values": "Latched values (on input or trigger)",
            },
        )

    PROPERTIES = {
        "value_type_list": {
            "description": "Comma-separated port value types",
            "data_type": "str",
            "default_value": "f32,f32",
        },
        "dispatch_if_input": {
            "description": "Also dispatch immediately when new values arrive",
            "data_type": "bool",
            "default_value": True,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ValuesLatch")

        value_type_list = [
            name_to_port_value_type(name.strip())
            for name in str(self.properties["value_type_list"]).split(",")
        ]

        input_dispatch = StaticTypeInputPort(
            "dispatch",
            [PortValueType(DataType.Any)],
        )
        input_dispatch.subscribe(id(self), self._on_input_dispatch)

        input_values = StaticTypeInputPort(
            "values",
            value_type_list,
        )
        input_values.subscribe(id(self), self._on_input_values)

        output_values = StaticTypeOutputPort(
            "values",
            value_type_list,
        )

        self._input_values = input_values
        self._input_dispatch = input_dispatch
        self._output_values = output_values
        self._value_type_list = value_type_list
        self._dispatch_if_input = bool(self.properties["dispatch_if_input"])

        self.inputs[input_values.name] = input_values
        self.inputs[input_dispatch.name] = input_dispatch
        self.outputs[output_values.name] = output_values

    def set_properties(self, properties: dict[str, PropertyDataType]):
        value_type_list = self._value_type_list

        if "value_type_list" in properties:
            value_type_list_str = properties["value_type_list"]
            if not isinstance(value_type_list_str, str):
                raise ValueError("value_type_list must be a string")

            value_type_list = [
                name_to_port_value_type(name.strip())
                for name in value_type_list_str.split(",")
            ]

        dispatch_if_input = self._dispatch_if_input
        if "dispatch_if_input" in properties:
            dispatch_if_input = bool(properties["dispatch_if_input"])

        if value_type_list != self._value_type_list:
            new_input = StaticTypeInputPort("values", value_type_list)
            new_output = StaticTypeOutputPort("values", value_type_list)

            replace_node_input_port(
                self, self._input_values, new_input, self._on_input_values
            )
            self._input_values = new_input

            replace_node_output_port(self, self._output_values, new_output)
            self._output_values = new_output

            self._value_type_list = value_type_list

        self._dispatch_if_input = dispatch_if_input

        self.properties["value_type_list"] = ",".join([t.name for t in value_type_list])
        self.properties["dispatch_if_input"] = dispatch_if_input

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, values: list[PortValue]):
        if self._dispatch_if_input:
            self._output_values.dispatch(values)

    def _on_input_dispatch(self, values: list[PortValue]):
        current_values = self._input_values.current_values
        if current_values is not None:
            self._output_values.dispatch(current_values)


class ValuesDelayNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description=(
                "Delay dispatch of the latest input values by a configurable "
                "duration. A new input cancels any pending dispatch and starts "
                "a fresh timer. The reset input also cancels any pending "
                "dispatch without scheduling a new one. A task identity check "
                "guarantees that a sleep completion racing against a cancel "
                "will not produce a stale dispatch."
            ),
            category="Flow Control",
            inputs={
                "values": "Input values (latest value dispatched after delay)",
                "reset": "Cancel any pending delayed dispatch",
            },
            outputs={
                "values": "Delayed output of the latest input",
            },
        )

    PROPERTIES = {
        "value_type_list": {
            "description": "Comma-separated port value types",
            "data_type": "str",
            "default_value": "i8",
        },
        "delay": {
            "description": "Delay duration in seconds",
            "data_type": "f64",
            "default_value": 5.0,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ValuesDelay")

        self._delay: float = float(self.properties["delay"])
        self._task: asyncio.Task | None = None

        value_type_list = [
            name_to_port_value_type(name.strip())
            for name in str(self.properties["value_type_list"]).split(",")
        ]
        input_values = StaticTypeInputPort(
            "values",
            value_type_list,
        )
        input_values.subscribe(id(self), self._on_input_values)

        input_reset = StaticTypeInputPort(
            "reset",
            [PortValueType(DataType.Any)],
        )
        input_reset.subscribe(id(self), self._on_input_reset)

        output_values = StaticTypeOutputPort(
            "values",
            value_type_list,
        )

        self._output_values = output_values
        self._input_values = input_values
        self._input_reset = input_reset
        self._value_type_list = value_type_list

        self.inputs[input_values.name] = input_values
        self.inputs[input_reset.name] = input_reset
        self.outputs[output_values.name] = output_values

    def finalize(self):
        if self._task is not None:
            self._task.cancel()

    def set_properties(self, properties: dict[str, PropertyDataType]):
        value_type_list = self._value_type_list

        if "value_type_list" in properties:
            value_type_list_str = properties["value_type_list"]
            if not isinstance(value_type_list_str, str):
                raise ValueError("value_type_list must be a string")

            value_type_list = [
                name_to_port_value_type(name.strip())
                for name in value_type_list_str.split(",")
            ]

        delay = self._delay
        if "delay" in properties:
            delay = float(properties["delay"])

        new_input_values = self._input_values
        new_output_values = self._output_values

        if value_type_list != self._value_type_list:
            new_input_values = StaticTypeInputPort("values", value_type_list)
            new_output_values = StaticTypeOutputPort("values", value_type_list)

        if new_input_values != self._input_values:
            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values

        if new_output_values != self._output_values:
            replace_node_output_port(
                self,
                self._output_values,
                new_output_values,
            )
            self._output_values = new_output_values

        self._delay = delay
        self._value_type_list = value_type_list

        self.properties["value_type_list"] = ",".join([t.name for t in value_type_list])
        self.properties["delay"] = delay

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    async def _delay_dispatch(self):
        # Capture self-reference before the suspend point. After awakening, we
        # compare against self._task to detect whether we are still the latest
        # task. This rejects stale dispatches in two race scenarios:
        #   1. asyncio scheduler race — the sleep timer fires in the same loop
        #      cycle as a cancel request; the timer's wake-up may be processed
        #      before the cancel is delivered, allowing the awaited sleep to
        #      return normally despite cancellation having been requested.
        #   2. consecutive input race — a new input arrived (or reset fired)
        #      between sleep wake-up and the dispatch line; self._task has
        #      already been replaced (or cleared by reset) so this task is no
        #      longer the latest.
        # The task identity check rejects both cases without a generation
        # counter; self._task itself acts as the generation identifier.
        current_task = asyncio.current_task()
        try:
            await asyncio.sleep(self._delay)
        except asyncio.CancelledError:
            return

        if self._task is not current_task:
            return

        values = self._input_values.current_values
        if values is None:
            return

        self._output_values.dispatch(values)
        if self.parent_graph is not None:
            self.parent_graph.flush_outputs()

    def _on_input_values(self, _values: list[PortValue]):
        if self._task is not None:
            self._task.cancel()

        self._task = asyncio.create_task(self._delay_dispatch())

    def _on_input_reset(self, _values: list[PortValue]):
        if self._task is not None:
            self._task.cancel()
        # Setting to None is essential for the task identity check: a stale
        # task awakening after this reset will see self._task is None and bail
        # out instead of dispatching.
        self._task = None


class ValueChangedNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Only dispatch when the input value differs from the previous one",
            category="Flow Control",
            inputs={
                "value": "Input value to compare with previous",
            },
            outputs={
                "value": "Output only when value has changed",
            },
        )

    PROPERTIES = {
        "value_type": {
            "description": "Port value type",
            "data_type": "str",
            "default_value": "i8",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ValueChanged")

        self._value_type = name_to_port_value_type(str(self.properties["value_type"]))
        self._value_array = None

        input_value = StaticTypeInputPort(
            "value",
            [self._value_type],
        )
        input_value.subscribe(id(self), self._on_input_value)
        output_value = StaticTypeOutputPort(
            "value",
            [self._value_type],
        )

        self._output_value = output_value
        self._input_value = input_value

        self.inputs[input_value.name] = input_value
        self.outputs[output_value.name] = output_value

    def set_properties(self, properties: dict[str, PropertyDataType]):
        value_type = self._value_type
        if "value_type" in properties:
            name = properties["value_type"]
            if not isinstance(name, str):
                raise ValueError("value_type must be a string")
            value_type = name_to_port_value_type(name)

        new_input_value = self._input_value
        new_output_value = self._output_value
        if value_type != self._value_type:
            new_input_value = StaticTypeInputPort("value", [value_type])
            new_output_value = StaticTypeOutputPort("value", [value_type])

        if new_input_value != self._input_value:
            replace_node_input_port(
                self, self._input_value, new_input_value, self._on_input_value
            )
            self._input_value = new_input_value

        if new_output_value != self._output_value:
            replace_node_output_port(self, self._output_value, new_output_value)
            self._output_value = new_output_value

        self._value_type = value_type
        self.properties["value_type"] = value_type.name

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_value(self, values: list[PortValue]):
        value_array = values[0]

        if self._value_array is None:
            self._value_array = value_array
            self._output_value.dispatch([value_array])
            return

        if len(value_array) != len(self._value_array):
            self._value_array = value_array
            self._output_value.dispatch([value_array])
            return

        if not np.array_equal(value_array, self._value_array):
            self._value_array = value_array
            self._output_value.dispatch([value_array])
            return


class BoolBranchNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Route each boolean element to true or false output",
            category="Flow Control",
            inputs={
                "bool": "Boolean values to route",
            },
            outputs={
                "true": "Elements where value is true",
                "false": "Elements where value is false",
            },
        )

    def __init__(self, name: str):
        super().__init__(name, "BoolBranch")

        input_bool = StaticTypeInputPort(
            "bool",
            [PortValueType(DataType.Bool)],
        )
        input_bool.subscribe(id(self), self._on_input_bool)

        output_true = StaticTypeOutputPort(
            "true",
            [PortValueType(DataType.Bool)],
        )
        output_false = StaticTypeOutputPort(
            "false",
            [PortValueType(DataType.Bool)],
        )

        self._output_true = output_true
        self._output_false = output_false

        self.inputs[input_bool.name] = input_bool
        self.outputs[output_true.name] = output_true
        self.outputs[output_false.name] = output_false

    def _on_input_bool(self, values_any: list[PortValue]):
        bool_array: np.ndarray = values_any[0]

        for b in bool_array:
            if b:
                self._output_true.dispatch([np.array([b])])
            else:
                self._output_false.dispatch([np.array([b])])


class SwitchBranchNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        props = properties or {}
        case_values_str = str(props.get("case_values", "0,1,2"))
        case_values = [int(v) for v in case_values_str.split(",")]
        return NodeDoc(
            description="Route each integer element to a matching case output or else",
            category="Flow Control",
            inputs={
                "value": "Integer values to route by case",
            },
            outputs={
                **{f"case_{cv}": f"Elements matching value {cv}" for cv in case_values},
                "else": "Elements not matching any case",
            },
        )

    PROPERTIES = {
        "case_values": {
            "description": "Comma-separated integer case values",
            "data_type": "str",
            "default_value": "0,1,2",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "SwitchBranch")

        input_value = StaticTypeInputPort(
            "value",
            [PortValueType(DataType.Int32)],
        )
        input_value.subscribe(id(self), self._on_input_value)

        case_values: list[int] = [
            int(v) for v in str(self.properties["case_values"]).split(",")
        ]
        output_cases: dict[int, StaticTypeOutputPort] = {
            case_value: StaticTypeOutputPort(
                f"case_{case_value}",
                [PortValueType(DataType.Int32)],
            )
            for case_value in case_values
        }
        output_else = StaticTypeOutputPort(
            "else",
            [PortValueType(DataType.Int32)],
        )

        self._output_cases = output_cases
        self._output_else = output_else
        self._case_values = case_values

        self.inputs[input_value.name] = input_value
        self.outputs[output_else.name] = output_else
        for output_case in output_cases.values():
            self.outputs[output_case.name] = output_case

    def set_properties(self, properties: dict[str, PropertyDataType]):
        case_values = self._case_values

        if "case_values" in properties:
            case_values_str = properties["case_values"]
            if not isinstance(case_values_str, str):
                raise ValueError("case_values must be a string")
            case_values = [int(case_value) for case_value in case_values_str.split(",")]

        new_output_cases = self._output_cases
        if case_values != self._case_values:
            new_output_cases: dict[int, StaticTypeOutputPort] = {
                case_value: StaticTypeOutputPort(
                    f"case_{case_value}", [PortValueType(DataType.Int32)]
                )
                for case_value in case_values
            }

        if new_output_cases != self._output_cases:
            old_set = set(self._case_values)
            new_set = set(case_values)

            # Remove cases no longer present
            for cv in self._case_values:
                if cv not in new_set:
                    old_port = self._output_cases[cv]
                    if self.parent_graph is not None:
                        self.parent_graph.disconnect_all_from_node_output(
                            self.name, old_port.name
                        )
                    self.outputs.pop(old_port.name)

            # Reuse existing or add new cases
            result_cases: dict[int, StaticTypeOutputPort] = {}
            for cv in case_values:
                if cv in old_set:
                    result_cases[cv] = self._output_cases[cv]
                else:
                    new_port = new_output_cases[cv]
                    result_cases[cv] = new_port
                    self.outputs[new_port.name] = new_port

            self._output_cases = result_cases

        self._case_values = case_values

        self.properties["case_values"] = ",".join(
            str(case_value) for case_value in case_values
        )

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_value(self, values: list[PortValue]):
        value_array: np.ndarray = values[0]

        for value in value_array:
            if value in self._output_cases:
                self._output_cases[value].dispatch([np.array([value])])
            else:
                self._output_else.dispatch([np.array([value])])


class ValuesBranchNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        props = properties or {}
        output_count = int(props.get("output_count", 2))
        return NodeDoc(
            description="Route values to one of multiple outputs based on an index",
            category="Flow Control",
            inputs={
                "values": "Values to route",
                "index": "Index selecting which output to dispatch to",
            },
            outputs={f"out_{i}": f"Output branch {i}" for i in range(output_count)},
        )

    PROPERTIES = {
        "value_type_list": {
            "description": "Comma-separated port value types",
            "data_type": "str",
            "default_value": "f32",
        },
        "output_count": {
            "description": "Number of output branches",
            "data_type": "i32",
            "default_value": 2,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ValuesBranch")

        self._index = -1
        self._output_count = int(self.properties["output_count"])

        value_type_list = [
            name_to_port_value_type(name.strip())
            for name in str(self.properties["value_type_list"]).split(",")
        ]
        input_values = StaticTypeInputPort(
            "values",
            value_type_list,
        )
        input_values.subscribe(id(self), self._on_input_values)

        input_index = StaticTypeInputPort(
            "index",
            [PortValueType(DataType.Int8)],
        )

        output_values_list = [
            StaticTypeOutputPort(
                f"out_{i}",
                value_type_list,
            )
            for i in range(self._output_count)
        ]

        self._output_values_list = output_values_list
        self._input_values = input_values
        self._value_type_list = value_type_list
        self._input_index = input_index

        self.inputs[input_values.name] = input_values
        self.inputs[input_index.name] = input_index
        for output_values in output_values_list:
            self.outputs[output_values.name] = output_values

    def set_properties(self, properties: dict[str, PropertyDataType]):
        output_count = self._output_count
        if "output_count" in properties:
            output_count = int(properties["output_count"])

        if output_count < 1:
            raise ValueError("output_count must be at least 1")

        value_type_list = self._value_type_list
        if "value_type_list" in properties:
            if not isinstance(properties["value_type_list"], str):
                raise ValueError("value_type_list must be a string")
            value_type_list = [
                name_to_port_value_type(name.strip())
                for name in properties["value_type_list"].split(",")
            ]

        new_input_values = self._input_values
        if value_type_list != self._value_type_list:
            new_input_values = StaticTypeInputPort("values", value_type_list)

        new_output_values_list = self._output_values_list
        if (
            self._value_type_list != value_type_list
            or self._output_count != output_count
        ):
            new_output_values_list = [
                StaticTypeOutputPort(f"out_{i}", value_type_list)
                for i in range(output_count)
            ]

        if new_input_values != self._input_values:
            replace_node_input_port(
                self, self._input_values, new_input_values, self._on_input_values
            )
            self._input_values = new_input_values

        if new_output_values_list != self._output_values_list:
            type_changed = value_type_list != self._value_type_list
            old_count = len(self._output_values_list)
            overlap = min(old_count, output_count)
            result_list: list[StaticTypeOutputPort] = []

            for i in range(overlap):
                if type_changed:
                    replace_node_output_port(
                        self, self._output_values_list[i], new_output_values_list[i]
                    )
                    result_list.append(new_output_values_list[i])
                else:
                    result_list.append(self._output_values_list[i])

            for i in range(overlap, old_count):
                old_port = self._output_values_list[i]
                if self.parent_graph is not None:
                    self.parent_graph.disconnect_all_from_node_output(
                        self.name, old_port.name
                    )
                self.outputs.pop(old_port.name)

            for i in range(overlap, output_count):
                result_list.append(new_output_values_list[i])
                self.outputs[new_output_values_list[i].name] = new_output_values_list[i]

            self._output_values_list = result_list

        self._value_type_list = value_type_list
        self._output_count = output_count

        self.properties["value_type_list"] = ",".join([t.name for t in value_type_list])
        self.properties["output_count"] = output_count

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, values: list[PortValue]):
        index_values = self._input_index.current_values
        if index_values is None:
            return

        index_array = index_values[0]

        len_index_array = len(index_array)

        if len_index_array == 0:
            return

        if len_index_array == 1:
            index = index_array[0]
            if 0 <= index < self._output_count:
                self._output_values_list[index].dispatch(values)
            return

        if len_index_array != len(values):
            logger.warning(
                f"{self.name}: index array length {len_index_array} does not match values length {len(values)}"
            )
            return
        for index, value in zip(index_array, values):
            if 0 <= index < self._output_count:
                self._output_values_list[index].dispatch([value])


class ValuesGateNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        props = properties or {}
        input_count = int(props.get("input_count", 2))
        return NodeDoc(
            description="Pass through only the input selected by an index",
            category="Flow Control",
            inputs={
                **{f"in_{i}": f"Input channel {i}" for i in range(input_count)},
                "index": "Index selecting which input to pass through",
            },
            outputs={
                "out": "Output from the selected input",
            },
        )

    PROPERTIES = {
        "value_type_list": {
            "description": "Comma-separated port value types",
            "data_type": "str",
            "default_value": "f32",
        },
        "input_count": {
            "description": "Number of input channels",
            "data_type": "i32",
            "default_value": 2,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "ValuesGate")

        input_count = int(self.properties["input_count"])

        value_type_list = [
            name_to_port_value_type(name.strip())
            for name in str(self.properties["value_type_list"]).split(",")
        ]
        input_value_list = [
            StaticTypeInputPort(
                f"in_{i}",
                value_type_list,
            )
            for i in range(input_count)
        ]
        for i, input_value in enumerate(input_value_list):
            input_value.subscribe(
                id(self),
                lambda values_any, index=i: self._on_input_values(index, values_any),
            )

        input_index = StaticTypeInputPort(
            "index",
            [PortValueType(DataType.Int8)],
        )

        output_values = StaticTypeOutputPort(
            "out",
            value_type_list,
        )

        self._input_value_list = input_value_list
        self._value_type_list = value_type_list
        self._input_index = input_index
        self._output_values = output_values
        self._input_count = input_count
        self._index = -1

        self.inputs[input_index.name] = input_index
        for input_value in input_value_list:
            self.inputs[input_value.name] = input_value
        self.outputs[output_values.name] = output_values

    def set_properties(self, properties: dict[str, PropertyDataType]):
        input_count = self._input_count
        if "input_count" in properties:
            input_count = int(properties["input_count"])

        if input_count < 1:
            raise ValueError("input_count must be at least 1")

        value_type_list = self._value_type_list
        if "value_type_list" in properties:
            if not isinstance(properties["value_type_list"], str):
                raise ValueError("value_type_list must be a string")
            value_type_list = [
                name_to_port_value_type(name.strip())
                for name in properties["value_type_list"].split(",")
            ]

        if self._value_type_list != value_type_list or self._input_count != input_count:
            type_changed = value_type_list != self._value_type_list
            old_count = self._input_count
            overlap = min(old_count, input_count)
            new_input_list: list[StaticTypeInputPort] = []

            # Overlapping inputs: replace if type changed
            for i in range(overlap):
                if type_changed:
                    new_port = StaticTypeInputPort(f"in_{i}", value_type_list)
                    replace_node_input_port(
                        self,
                        self._input_value_list[i],
                        new_port,
                        lambda values_any, index=i: self._on_input_values(
                            index, values_any
                        ),
                    )
                    new_input_list.append(new_port)
                else:
                    new_input_list.append(self._input_value_list[i])

            # Removed inputs
            for i in range(overlap, old_count):
                old_port = self._input_value_list[i]
                if self.parent_graph is not None:
                    self.parent_graph.disconnect_all_from_node_input(
                        self.name, old_port.name
                    )
                old_port.unsubscribe(id(self))
                self.inputs.pop(old_port.name)

            # Added inputs
            for i in range(overlap, input_count):
                new_port = StaticTypeInputPort(f"in_{i}", value_type_list)
                new_port.subscribe(
                    id(self),
                    lambda values_any, index=i: self._on_input_values(
                        index, values_any
                    ),
                )
                new_input_list.append(new_port)
                self.inputs[new_port.name] = new_port

            self._input_value_list = new_input_list

            # Output port: replace if type changed
            if type_changed:
                new_output = StaticTypeOutputPort("out", value_type_list)
                replace_node_output_port(self, self._output_values, new_output)
                self._output_values = new_output

            self._value_type_list = value_type_list
            self._input_count = input_count

        self.properties["value_type_list"] = ",".join([t.name for t in value_type_list])
        self.properties["input_count"] = input_count

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_values(self, index: int, values_any: list[PortValue]):
        if self._input_index.current_values is None:
            return

        target_index: int = self._input_index.current_values[0][-1]
        if target_index != index:
            return

        self._output_values.dispatch(values_any)


class TransitionNode(BaseNode):
    """Detect a string state's entry into and exit from a target value.

    Inspired by UML state machine semantics. Given a `current` input that
    streams the latest state name, emits an `enter` pulse the moment current
    becomes equal to the target state, and an `exit` pulse the moment current
    leaves the target state. A property `target` configures the state name to
    monitor.

    Batched-input traversal
    -----------------------
    A single dispatch may carry an array of multiple state samples (e.g.
    `["A", "B", "A"]` arriving in one batch when upstream events bunch up).
    Naively reading only the latest element would miss the intermediate
    transitions and silently skip cleanup work that is wired off `exit`.
    Instead, this node walks the array element by element, comparing each
    sample to the previous one, and emits enter/exit pulses for every
    transition encountered. Order is preserved so downstream effects
    (load → stop → unload, etc.) fire in the correct sequence.
    """

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description=(
                "Detect string state transitions into and out of a target "
                "value. Emits an `enter` pulse when current becomes target, "
                "and an `exit` pulse when current leaves target. Walks each "
                "element of batched input arrays so no intermediate "
                "transition is dropped."
            ),
            category="Flow Control",
            inputs={
                "current": "Current state name (str, batch input supported)",
            },
            outputs={
                "enter": "True pulse when current enters target state",
                "exit": "True pulse when current leaves target state",
            },
        )

    PROPERTIES = {
        "target": {
            "description": "State name to monitor for entry and exit",
            "data_type": "str",
            "default_value": "",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Transition")

        self._target: str = str(self.properties.get("target", ""))
        # Initial _prev_state of "" means the first input is treated as a
        # transition from "no-state" into whatever arrives. If the first
        # arriving state equals target, an `enter` fires once. If it differs,
        # nothing is emitted. This matches the cold-boot expectation that
        # upstream SessionState replays the latest venue at startup.
        self._prev_state: str = ""

        input_current = StaticTypeInputPort(
            "current",
            [PortValueType(DataType.String)],
        )
        input_current.subscribe(id(self), self._on_input_current)

        bool_type = PortValueType(DataType.Bool)
        output_enter = StaticTypeOutputPort("enter", [bool_type])
        output_exit = StaticTypeOutputPort("exit", [bool_type])

        self._input_current = input_current
        self._output_enter = output_enter
        self._output_exit = output_exit

        self.inputs[input_current.name] = input_current
        self.outputs[output_enter.name] = output_enter
        self.outputs[output_exit.name] = output_exit

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # Phase 1: validate to local vars; nothing on self is mutated yet.
        target = self._target
        if "target" in properties:
            v = properties["target"]
            if not isinstance(v, str):
                raise ValueError("target must be a string")
            target = v

        # Phase 2: apply atomically.
        self._target = target
        self.properties["target"] = target

        # Phase 3: notify only — no other reactive work here.
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_current(self, values: list[PortValue]):
        # values[0] is the 1-d ndarray carrying one or more state samples,
        # statically typed via StaticTypeInputPort. No asarray/reshape guard:
        # the static port type is the contract and we trust it.
        arr = values[0]
        n = len(arr)
        if n == 0:
            return

        target = self._target
        # Compute phase: project string state to "is in target" bool stream,
        # then use vectorized edge detection. +1 → enter (not-target → target),
        # -1 → exit (target → not-target), 0 → no transition. _prev_state
        # is read but not written here so a reentrant call into this node
        # via the dispatch chain cannot corrupt this loop's view of it.
        in_target_int = (arr == target).astype(np.int8, copy=False)
        prev_in_target = (self._prev_state == target)
        diffs = np.diff(in_target_int, prepend=np.int8(prev_in_target))
        indices = np.flatnonzero(diffs != 0)
        kinds = diffs[indices]  # +1 / -1 in source order

        # Commit phase: atomic state update before any side effects. Any
        # reentrant call into this node's input via the dispatch chain
        # will see the fully-committed post-batch _prev_state, never an
        # in-flight intermediate value. Same atomic state-update
        # philosophy as the transactional set_properties pattern.
        self._prev_state = str(arr[-1])

        # Dispatch phase: emit pulses in source order.
        # flush_outputs() is NOT called: this is a synchronous reactive
        # callback driven by an input port subscribe, and broadcast is
        # handled by the engine in the normal tick. Calling flush here
        # would be redundant (and was a bug in the prior implementation).
        for k in kinds:
            if k == 1:
                self._output_enter.dispatch(
                    [np.array([True], dtype=np.bool_)]
                )
            else:
                self._output_exit.dispatch(
                    [np.array([True], dtype=np.bool_)]
                )


class BoolEdgeNode(BaseNode):
    """Detect bool transitions and emit pulses on rising and falling edges.

    Mirrors TransitionNode's enter/exit pattern for the bool case.

    Cold-boot semantics
    -------------------
    The first observed sample is treated as initial-state observation;
    no pulse is emitted regardless of its value. This matches the
    behavior of Verilog `posedge`, LabVIEW Boolean Crossing, RxJS
    `pairwise`, TouchDesigner Trigger CHOP, and the IEC 61131-8
    recommendation. It intentionally differs from IEC 61131-3 R_TRIG,
    which treats the initial internal memory as FALSE and fires on the
    first TRUE input. Typical callers want "fire only on a real
    transition that happened during runtime", not on whatever value
    happened to be sampled first after engine boot.

    Reentrancy and ordering
    -----------------------
    A single dispatch may carry an array of multiple bool samples (e.g.
    when upstream values bunch up into one batch). The implementation
    runs in three phases:

      1. Compute: read self._prev once into a local; use np.diff to
         compute every transition vectorized; gather kinds (+1 for
         rising, -1 for falling) in source order.
      2. Commit: atomically write self._prev to the post-batch value.
      3. Dispatch: emit pulses in source order.

    Because the commit precedes any dispatch, a reentrant call into this
    node's input via the dispatch chain (a downstream feedback path)
    sees the fully-committed post-batch state, never an in-flight
    intermediate value. Same atomic state-update philosophy as the
    transactional set_properties pattern.

    No flush_outputs(): this is a synchronous reactive callback driven
    by an input port subscribe, and broadcast is handled by the engine
    in the normal tick.
    """

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description=(
                "Emit pulses on bool transitions: `rising` fires when "
                "value goes false -> true, `falling` fires when value "
                "goes true -> false. The first observed sample is "
                "treated as initial-state observation (no pulse) so "
                "engine cold-boot does not produce a spurious edge. "
                "Walks batched input element by element."
            ),
            category="Flow Control",
            inputs={"value": "Boolean input (batch supported)"},
            outputs={
                "rising": "True pulse on false -> true transition",
                "falling": "True pulse on true -> false transition",
            },
        )

    def __init__(self, name: str):
        super().__init__(name, "BoolEdge")
        # None marks "uninitialized" — first sample only registers state
        # without emitting any pulse.
        self._prev: bool | None = None

        bool_type = PortValueType(DataType.Bool)
        input_value = StaticTypeInputPort("value", [bool_type])
        input_value.subscribe(id(self), self._on_input_value)
        output_rising = StaticTypeOutputPort("rising", [bool_type])
        output_falling = StaticTypeOutputPort("falling", [bool_type])

        self._input_value = input_value
        self._output_rising = output_rising
        self._output_falling = output_falling

        self.inputs[input_value.name] = input_value
        self.outputs[output_rising.name] = output_rising
        self.outputs[output_falling.name] = output_falling

    def _on_input_value(self, values: list[PortValue]):
        arr = values[0]
        n = len(arr)
        if n == 0:
            return

        arr_int = arr.astype(np.int8, copy=False)

        # Compute phase: vectorized transition detection via np.diff.
        # +1 -> rising (false -> true), -1 -> falling (true -> false),
        # 0 -> no change.
        if self._prev is None:
            # Cold-boot: first sample only registers the initial state
            # with no edge comparison against it. Diffs are computed
            # within arr alone, so a single-sample batch produces no
            # transitions.
            if n == 1:
                self._prev = bool(arr[0])
                return
            diffs = np.diff(arr_int)
        else:
            diffs = np.diff(arr_int, prepend=np.int8(self._prev))

        indices = np.flatnonzero(diffs != 0)
        kinds = diffs[indices]  # +1 / -1 in source order

        # Commit phase: atomic state update before any side effects.
        self._prev = bool(arr[-1])

        # Dispatch phase: emit pulses in source order. Allocate per
        # dispatch (cheap, matches BoolBranch's pattern; safer than
        # sharing one array since the engine may retain references).
        for k in kinds:
            if k == 1:
                self._output_rising.dispatch(
                    [np.array([True], dtype=np.bool_)]
                )
            else:
                self._output_falling.dispatch(
                    [np.array([True], dtype=np.bool_)]
                )
