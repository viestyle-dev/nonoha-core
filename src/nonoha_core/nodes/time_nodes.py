import asyncio
import time
import numpy as np
import logging
from datetime import datetime

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


class SystemTimeNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Output the current system time as Unix timestamp on dispatch",
            category="Time",
            inputs={"dispatch": ""},
            outputs={"time": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "SystemTime")

        input_dispatch = StaticTypeInputPort("dispatch", [PortValueType(DataType.Any)])
        input_dispatch.subscribe(id(self), self._on_input_dispatch)

        output_time = StaticTypeOutputPort("time", [PortValueType(DataType.Float64)])

        self._output_time = output_time

        self.inputs[input_dispatch.name] = input_dispatch
        self.outputs[output_time.name] = output_time

    def _on_input_dispatch(self, values: list[PortValue]):
        dispatch_array = values[0]
        # Maximum Unix time representable per storage unit:
        # int64 nanoseconds:
        #  year 2262
        # int64 milliseconds:
        #  year 292,471,208

        # For f64 seconds, precision degrades in stages:
        # | Year   | time.time() value | Precision (s) | Precision        |
        # |--------|-------------------|---------------|------------------|
        # | 2024   | 1.7×10^9          | 2×10^-10      | 0.2 nanoseconds  |
        # | 2038   | 2.1×10^9          | 2×10^-10      | 0.2 nanoseconds  |
        # | 2242   | 8.6×10^9          | 1×10^-9       | 1 nanosecond     |
        # | 4000   | 6×10^10           | 7×10^-9       | 7 nanoseconds    |
        # | 35000  | 1×10^12           | 2×10^-7       | 0.2 milliseconds |
        # time_millis = time.time_ns() // 1_000_000
        time_secs = time.time()
        time_array = np.full(len(dispatch_array), time_secs, dtype=np.float64)
        self._output_time.dispatch([time_array])

        # print(time.time_ns(), time.time())


class TimeDecomposeNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Decompose Unix timestamp into year, month, day, hour, minute, second, microsecond",
            category="Time",
            inputs={"time": ""},
            outputs={
                "year": "",
                "month": "",
                "day": "",
                "hour": "",
                "minute": "",
                "second": "",
                "microsecond": "",
                "completed": "",
            },
        )

    def __init__(self, name: str):
        super().__init__(name, "TimeDecompose")

        input_time = StaticTypeInputPort("time", [PortValueType(DataType.Float64)])
        input_time.subscribe(id(self), self._on_input_time)

        output_year = StaticTypeOutputPort("year", [PortValueType(DataType.Int32)])
        output_month = StaticTypeOutputPort("month", [PortValueType(DataType.Int32)])
        output_day = StaticTypeOutputPort("day", [PortValueType(DataType.Int32)])
        output_hour = StaticTypeOutputPort("hour", [PortValueType(DataType.Int32)])
        output_minute = StaticTypeOutputPort("minute", [PortValueType(DataType.Int32)])
        output_second = StaticTypeOutputPort("second", [PortValueType(DataType.Int32)])
        output_microsecond = StaticTypeOutputPort(
            "microsecond", [PortValueType(DataType.Int32)]
        )
        output_completed = StaticTypeOutputPort(
            "completed", [PortValueType(DataType.Bool)]
        )

        self._output_year = output_year
        self._output_month = output_month
        self._output_day = output_day
        self._output_hour = output_hour
        self._output_minute = output_minute
        self._output_second = output_second
        self._output_microsecond = output_microsecond
        self._output_completed = output_completed

        self.outputs[output_completed.name] = output_completed
        self.inputs[input_time.name] = input_time
        self.outputs[output_year.name] = output_year
        self.outputs[output_month.name] = output_month
        self.outputs[output_day.name] = output_day
        self.outputs[output_hour.name] = output_hour
        self.outputs[output_minute.name] = output_minute
        self.outputs[output_second.name] = output_second
        self.outputs[output_microsecond.name] = output_microsecond

    def _on_input_time(self, values: list[PortValue]):
        time_array: np.ndarray = values[0]

        year_array = np.empty(len(time_array), dtype=np.int32)
        month_array = np.empty(len(time_array), dtype=np.int32)
        day_array = np.empty(len(time_array), dtype=np.int32)
        hour_array = np.empty(len(time_array), dtype=np.int32)
        minute_array = np.empty(len(time_array), dtype=np.int32)
        second_array = np.empty(len(time_array), dtype=np.int32)
        microsecond_array = np.empty(len(time_array), dtype=np.int32)

        try:
            for i, time_secs in enumerate(time_array):
                dt = datetime.fromtimestamp(time_secs)
                year_array[i] = dt.year
                month_array[i] = dt.month
                day_array[i] = dt.day
                hour_array[i] = dt.hour
                minute_array[i] = dt.minute
                second_array[i] = dt.second
                microsecond_array[i] = dt.microsecond
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return

        self._output_year.dispatch([year_array])
        self._output_month.dispatch([month_array])
        self._output_day.dispatch([day_array])
        self._output_hour.dispatch([hour_array])
        self._output_minute.dispatch([minute_array])
        self._output_second.dispatch([second_array])
        self._output_microsecond.dispatch([microsecond_array])

        self._output_completed.dispatch([np.array([True])])


class TimeStringifyNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Format Unix timestamp as a string using strftime format",
            category="Time",
            inputs={"time": ""},
            outputs={"string": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "TimeStringify")

        input_time = StaticTypeInputPort("time", [PortValueType(DataType.Float64)])
        input_time.subscribe(id(self), self._on_input_time)

        output_string = StaticTypeOutputPort("string", [PortValueType(DataType.String)])

        format_str = "%Y-%m-%d %H:%M:%S.%f"
        self._format_str = format_str

        self._output_string = output_string

        self.inputs[input_time.name] = input_time
        self.outputs[output_string.name] = output_string

        self.properties["format_str"] = format_str

    def set_properties(self, properties: dict[str, PropertyDataType]):
        format_str = self._format_str
        if "format_str" in properties:
            format_str = properties["format_str"]
            if not isinstance(format_str, str):
                raise ValueError("format_str must be a string")

        self._format_str = format_str
        self.properties["format_str"] = format_str

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_time(self, values: list[PortValue]):
        time_array: np.ndarray = values[0]

        format_str = self._format_str

        formatted = np.empty(len(time_array), dtype=np.dtypes.StringDType())  # type: ignore
        try:
            for i, time_secs in enumerate(time_array):
                dt = datetime.fromtimestamp(time_secs)
                formatted[i] = dt.strftime(format_str)
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return

        self._output_string.dispatch([formatted])


class TimeDailyRangeWithinNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Check if current time falls within a daily time range",
            category="Time",
            inputs={"time": ""},
            outputs={"in_range": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "TimeDailyRangeWithin")

        input_time = StaticTypeInputPort(
            "time",
            [
                PortValueType(DataType.Int32),
                PortValueType(DataType.Int32),
                PortValueType(DataType.Int32),
            ],
            ["hour", "minute", "second"],
        )
        input_time.subscribe(id(self), self._on_input_time)

        output_in_range = StaticTypeOutputPort(
            "in_range", [PortValueType(DataType.Bool)]
        )

        self._start_time_str = "09:00:00"
        self._end_time_str = "18:00:00"

        # Pre-calculated time values in seconds for comparison
        self._start_time_seconds = 32400  # 09:00:00 = 9 * 3600
        self._end_time_seconds = 64800  # 18:00:00 = 18 * 3600

        self._output_in_range = output_in_range

        self.inputs[input_time.name] = input_time
        self.outputs[output_in_range.name] = output_in_range

        self.properties["start_time"] = self._start_time_str
        self.properties["end_time"] = self._end_time_str

    def set_properties(self, properties: dict[str, PropertyDataType]):
        start_time_str = self._start_time_str
        end_time_str = self._end_time_str
        start_time_seconds = self._start_time_seconds
        end_time_seconds = self._end_time_seconds

        if "start_time" in properties:
            start_time_str = properties["start_time"]
            if not isinstance(start_time_str, str):
                raise ValueError("start_time must be a string")
            # Parse and validate
            start_h, start_m, start_s = self._parse_time_string(start_time_str)
            start_time_seconds = start_h * 3600 + start_m * 60 + start_s

        if "end_time" in properties:
            end_time_str = properties["end_time"]
            if not isinstance(end_time_str, str):
                raise ValueError("end_time must be a string")
            # Parse and validate
            end_h, end_m, end_s = self._parse_time_string(end_time_str)
            end_time_seconds = end_h * 3600 + end_m * 60 + end_s

        self._start_time_str = start_time_str
        self._end_time_str = end_time_str
        self._start_time_seconds = start_time_seconds
        self._end_time_seconds = end_time_seconds

        self.properties["start_time"] = self._start_time_str
        self.properties["end_time"] = self._end_time_str

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _parse_time_string(self, time_str: str) -> tuple[int, int, int]:
        """Parse time string in HH:MM or HH:MM:SS format.

        Returns:
            tuple of (hour, minute, second)
        """
        parts = time_str.split(":")
        if len(parts) == 2:
            hour, minute = int(parts[0]), int(parts[1])
            second = 0
        elif len(parts) == 3:
            hour, minute, second = int(parts[0]), int(parts[1]), int(parts[2])
        else:
            raise ValueError(f"Invalid time format: {time_str}. Use HH:MM or HH:MM:SS")

        if not (0 <= hour <= 23):
            raise ValueError(f"Hour must be 0-23: {hour}")
        if not (0 <= minute <= 59):
            raise ValueError(f"Minute must be 0-59: {minute}")
        if not (0 <= second <= 59):
            raise ValueError(f"Second must be 0-59: {second}")

        return hour, minute, second

    def _on_input_time(self, values: list[PortValue]):
        hour_array: np.ndarray = values[0]
        minute_array: np.ndarray = values[1]
        second_array: np.ndarray = values[2]

        start_time_seconds = self._start_time_seconds
        end_time_seconds = self._end_time_seconds

        try:
            # Vectorized calculation of current time in seconds
            current_time_array = hour_array * 3600 + minute_array * 60 + second_array

            if start_time_seconds <= end_time_seconds:
                # Normal range (e.g., 12:00 ~ 13:00)
                result = (current_time_array >= start_time_seconds) & (current_time_array <= end_time_seconds)
            else:
                # Range crosses midnight (e.g., 23:00 ~ 2:00)
                result = (current_time_array >= start_time_seconds) | (current_time_array <= end_time_seconds)
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            return

        self._output_in_range.dispatch([result])


class ClockNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Generate periodic time values at a configurable sample rate",
            category="Time",
            inputs={"enabled": "", "reset": ""},
            outputs={"times": ""},
        )

    PROPERTIES = {
        "fs": {
            "description": "Sample rate (Hz)",
            "data_type": "f64",
            "default_value": 600.0,
        },
        "pack_size": {
            "description": "Number of samples per pack",
            "data_type": "u32",
            "default_value": 20,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Clock")

        self._fs = 600.0
        self._pack_size = 20
        self._emit_interval_ms = 1000 / self._fs * self._pack_size
        self._times = np.arange(self._pack_size, dtype=np.float32) / self._fs

        input_enabled = StaticTypeInputPort("enabled", [PortValueType(DataType.Bool)])
        input_enabled.subscribe(id(self), self._on_input_enabled)

        input_reset = StaticTypeInputPort("reset", [PortValueType(DataType.Any)])
        input_reset.subscribe(id(self), self._on_input_reset)

        output_times = StaticTypeOutputPort("times", [PortValueType(DataType.Float32)])

        self._output_times = output_times

        self.inputs[input_enabled.name] = input_enabled
        self.inputs[input_reset.name] = input_reset
        self.outputs[output_times.name] = output_times

        self._timer_task: asyncio.Task | None = None

    def finalize(self):
        if self._timer_task is not None:
            self._timer_task.cancel()
            self._timer_task = None

    def set_properties(self, properties: dict[str, PropertyDataType]):
        fs = self._fs
        pack_size = self._pack_size

        if "fs" in properties:
            fs = float(properties["fs"])
            if fs <= 0:
                raise ValueError(f"fs must be greater than 0, got {fs}")

        if "pack_size" in properties:
            pack_size = int(properties["pack_size"])
            if pack_size <= 0:
                raise ValueError(f"pack_size must be greater than 0, got {pack_size}")

        need_restart_timer = False
        if fs != self._fs or pack_size != self._pack_size:
            emit_interval_ms = 1000 / fs * pack_size
            times = np.arange(pack_size, dtype=np.float32) / fs

            self._fs = fs
            self._pack_size = pack_size
            self._emit_interval_ms = emit_interval_ms
            self._times = times
            need_restart_timer = True

        self.properties["fs"] = self._fs
        self.properties["pack_size"] = self._pack_size

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

        # Restart timer if parameters changed and timer is running
        if need_restart_timer:
            self._restart_timer_if_running()

    def _restart_timer_if_running(self):
        if self._timer_task is not None:
            self._timer_task.cancel()
            self._timer_task = asyncio.create_task(self._emit_times())

    def _on_input_reset(self, values: list[PortValue]):
        self._times = np.arange(self._pack_size, dtype=np.float32) / self._fs
        # Restart timer to apply the reset immediately
        self._restart_timer_if_running()

    def _on_input_enabled(self, values: list[PortValue]):
        bool_array: np.ndarray = values[0]
        enabled = bool_array[-1]

        if enabled:
            if self._timer_task is None:
                timer_task = asyncio.create_task(self._emit_times())
                self._timer_task = timer_task
        else:
            if self._timer_task is not None:
                self._timer_task.cancel()
                self._timer_task = None

    async def _emit_times(self):
        try:
            while True:
                await asyncio.sleep(self._emit_interval_ms / 1000.0)
                self._output_times.dispatch([self._times])
                self._times += self._pack_size / self._fs

                if self.parent_graph is not None:
                    self.parent_graph.flush_outputs()
        except asyncio.CancelledError:
            pass


class TickClockNode(BaseNode):
    """Tick-driven clock that emits accumulated time without drift.

    Unlike ClockNode (asyncio-driven, self-firing), TickClockNode advances only
    when its ``tick`` input is dispatched. Output ``times[i] = (frame_index + i) / fs``
    is computed exactly each tick from an integer frame counter, so no
    floating-point accumulation error builds up over long runs.

    Designed to be driven by an external precise timer such as
    ``ArtNetDmxSend.ready`` so that the emitted logical time stays in lock-step
    with the consumer's actual frame rate.
    """

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description=(
                "Emit accumulated time on each external tick. "
                "times[i] = (frame_index + i) / fs, computed exactly each tick "
                "(no drift). Drive `tick` from an external precise timer "
                "(e.g. ArtNetDmxSend.ready) to stay in sync with it."
            ),
            category="Time",
            inputs={"tick": "", "reset": ""},
            outputs={"times": ""},
        )

    PROPERTIES = {
        "fs": {
            "description": (
                "Sample rate in Hz. Output times = frame_index / fs, "
                "computed each tick (no floating-point drift)."
            ),
            "data_type": "f64",
            "default_value": 30.0,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "TickClock")

        # typed attributes (runtime source of truth)
        self._fs = 30.0
        self._frame_index = 0  # Python int, unbounded

        input_tick = StaticTypeInputPort("tick", [PortValueType(DataType.Any)])
        input_tick.subscribe(id(self), self._on_input_tick)

        input_reset = StaticTypeInputPort("reset", [PortValueType(DataType.Any)])
        input_reset.subscribe(id(self), self._on_input_reset)

        output_times = StaticTypeOutputPort(
            "times", [PortValueType(DataType.Float64)]
        )

        self._output_times = output_times

        self.inputs[input_tick.name] = input_tick
        self.inputs[input_reset.name] = input_reset
        self.outputs[output_times.name] = output_times

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # Phase 1: validate into locals
        fs = self._fs
        if "fs" in properties:
            fs_val = float(properties["fs"])
            if fs_val <= 0:
                raise ValueError(f"fs must be greater than 0, got {fs_val}")
            fs = fs_val

        # Phase 2: atomic commit to typed attribute
        self._fs = fs

        # Phase 3: record to self.properties for serialization
        self.properties["fs"] = self._fs

        if self.parent_graph is not None:
            self.parent_graph.notify_properties_changed(self)

    def _on_input_tick(self, values: list[PortValue]):
        n = len(values[0])
        if n == 0:
            return
        start = self._frame_index
        self._frame_index += n
        # int64 / f64 → f64. f64 integer precision (2^53) holds for ~9.5e15
        # frames; at 30 fps that's ~10 million years. No practical overflow.
        indices = np.arange(start, start + n, dtype=np.int64)
        times = indices / self._fs
        self._output_times.dispatch([times])

    def _on_input_reset(self, values: list[PortValue]):
        self._frame_index = 0
        self._output_times.dispatch([np.array([0.0], dtype=np.float64)])
