"""WaveGenerator: a function generator for test signals.

For each input time t (seconds) the output is

    series = amplitude * shape(u) + offset
    u      = frac(c)                                  (0 <= u < 1)
    c      = frequency * t + I_fm(t) + (pm + phase) / 2pi   (cycles)

where ``I_fm`` is the integral of the ``fm`` input (Hz) over time, and
``shape`` is sine, square, triangle or saw, all rising through 0 at u = 0.
Without ``fm`` the output depends on the times only: the same times give the
same values, and generators driven by one clock stay in phase. ``fm`` makes
the phase depend on its history (the integral restarts when the time goes
back, e.g. after a Clock reset).

``fm`` and ``pm`` hold the last block received and apply from the next
``times`` on: a modulating generator computed after its carrier acts one
block late. With a sine modulator, a ``pm`` amplitude of beta gives the same
spectrum as an ``fm`` deviation of beta * (modulating frequency).

Hot path (one call per block): every per-block constant is folded into one
scalar added once, each waveform is an affine function of u whose last step
writes the f32 output, and a constant ``fm`` only changes the frequency.
NumPy costs about 0.5 us per call, so the number of calls matters as much as
avoiding allocation.
"""

from __future__ import annotations

import logging
import math

import numpy as np

from nonoha_core.data_type import DataType, PortValueType, PropertyDataType
from nonoha_core.node import BaseNode, NodeDoc
from nonoha_core.port import PortValue, StaticTypeInputPort, StaticTypeOutputPort

logger = logging.getLogger(__name__)

WAVEFORMS = ("sine", "square", "triangle", "saw")
_TWO_PI = 2.0 * math.pi
_INV_TWO_PI = 1.0 / _TWO_PI
# Cycles added before frac(), so that triangle and saw become affine in u
# (no np.mod): triangle(u) = 1 - 4|frac(c + 1/4) - 1/2|, saw(u) = 2 frac(c + 1/2) - 1.
_SHIFT = {"sine": 0.0, "square": 0.0, "triangle": 0.25, "saw": 0.5}


class WaveGeneratorNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description=(
                "Function generator for test signals: sine, square, triangle or saw "
                "(not band-limited), one value per input time. fm (Hz) and pm (rad) "
                "modulate per sample; a sine pm of amplitude beta equals a sine fm "
                "of deviation beta x (modulating frequency)."
            ),
            category="Signal Generation",
            inputs={
                "times": "Sample times in seconds, e.g. Clock.times (f64)",
                "fm": "Frequency deviation in Hz added to 'frequency', per sample or one value (integrated over time)",
                "pm": "Phase deviation in radians, per sample or one value",
            },
            outputs={"series": "amplitude x waveform + offset, one value per time (f32)"},
        )

    PROPERTIES = {
        "frequency": {"description": "Frequency in Hz", "data_type": "f64", "default_value": 440.0},
        "amplitude": {"description": "Peak amplitude", "data_type": "f64", "default_value": 1.0},
        "offset": {"description": "Value added to the waveform (DC offset)", "data_type": "f64", "default_value": 0.0},
        "phase": {
            "description": "Phase in radians (every waveform rises through 0 at phase 0)",
            "data_type": "f64",
            "default_value": 0.0,
        },
        "waveform": {
            "description": "sine, square, triangle or saw",
            "data_type": "str",
            "default_value": "sine",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "WaveGenerator")

        # Inputs are f64 so that f32 senders connect too (f32 -> f64 casts,
        # f64 -> f32 does not). The output stays f32: its receivers are f32.
        f64 = PortValueType(DataType.Float64)
        self._input_times = StaticTypeInputPort("times", [f64])
        self._input_fm = StaticTypeInputPort("fm", [f64])
        self._input_pm = StaticTypeInputPort("pm", [f64])
        self._output_series = StaticTypeOutputPort("series", [PortValueType(DataType.Float32)])
        self._input_times.subscribe(id(self), self._on_times)
        self._input_fm.subscribe(id(self), self._on_fm)
        self._input_pm.subscribe(id(self), self._on_pm)
        for port in (self._input_times, self._input_fm, self._input_pm):
            self.inputs[port.name] = port
        self.outputs[self._output_series.name] = self._output_series

        # Per-block constants derived from the properties (see _mirror).
        self._frequency = 0.0
        self._waveform = "sine"
        self._constant_cycles = 0.0  # phase / 2pi + the waveform's shift
        self._scale = self._bias = 0.0  # series = scale * g(u) + bias
        self._sine_unscaled = True  # amplitude 1 and offset 0: sin() writes the output
        self._mirror()

        # Modulation blocks, copied on arrival: dispatched values are valid
        # only during the dispatch. None until the first block arrives.
        # pm is kept in cycles (converted while copying), so a block of times
        # adds it in one call.
        self._fm: np.ndarray | None = None
        self._pm_cycles: np.ndarray | None = None
        self._warned_length: dict[str, int] = {}

        # fm integral: cycles gained up to the last time (kept in [0, 1)),
        # and the last time and fm value, so blocks join without a seam.
        self._fm_cycles = 0.0
        self._last_time: float | None = None
        self._last_fm = 0.0

        # Buffers, reallocated only when the block length changes.
        self._allocate(0)

    def _allocate(self, n: int):
        self._cycles = np.empty(n, dtype=np.float64)
        self._work = np.empty(n, dtype=np.float64)
        self._step = np.empty(n, dtype=np.float64)
        self._work_tail = self._work[1:]  # views made once, not per block
        self._step_tail = self._step[1:]
        self._mask = np.empty(n, dtype=np.bool_)
        self._series = np.empty(n, dtype=np.float32)

    # -- properties ------------------------------------------------------------

    def set_properties(self, properties: dict[str, PropertyDataType]):
        updates: dict[str, PropertyDataType] = {}
        for key in ("frequency", "amplitude", "offset", "phase"):
            if key in properties:
                value = float(properties[key])  # type: ignore[arg-type]
                if not math.isfinite(value):
                    raise ValueError(f"{key} must be a finite number, got {value}")
                updates[key] = value
        if "waveform" in properties:
            waveform = str(properties["waveform"])
            if waveform not in WAVEFORMS:
                raise ValueError(f"waveform must be one of {', '.join(WAVEFORMS)}, got {waveform!r}")
            updates["waveform"] = waveform
        self.properties.update(updates)
        self._mirror()

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _mirror(self):
        """Fold the properties into the constants used per block."""
        p = self.properties
        amplitude = float(p["amplitude"])  # type: ignore[arg-type]
        offset = float(p["offset"])  # type: ignore[arg-type]
        waveform = str(p["waveform"])
        self._frequency = float(p["frequency"])  # type: ignore[arg-type]
        self._waveform = waveform
        self._constant_cycles = float(p["phase"]) * _INV_TWO_PI + _SHIFT[waveform]  # type: ignore[arg-type]
        self._sine_unscaled = amplitude == 1.0 and offset == 0.0
        if waveform == "sine":  # amplitude * sin(2pi u) + offset
            self._scale, self._bias = amplitude, offset
        elif waveform == "square":  # 2 amplitude * [u < 1/2] + (offset - amplitude)
            self._scale, self._bias = 2.0 * amplitude, offset - amplitude
        elif waveform == "triangle":  # -4 amplitude * |u - 1/2| + (amplitude + offset)
            self._scale, self._bias = -4.0 * amplitude, amplitude + offset
        else:  # saw: 2 amplitude * u + (offset - amplitude)
            self._scale, self._bias = 2.0 * amplitude, offset - amplitude

    # -- inputs ------------------------------------------------------------------

    def _on_fm(self, values: list[PortValue]):
        block = values[0]
        buffer = self._fm
        if buffer is None or buffer.shape != block.shape:
            buffer = self._fm = np.empty(block.shape, dtype=np.float64)
        np.copyto(buffer, block)

    def _on_pm(self, values: list[PortValue]):
        block = values[0]
        buffer = self._pm_cycles
        if buffer is None or buffer.shape != block.shape:
            buffer = self._pm_cycles = np.empty(block.shape, dtype=np.float64)
        np.multiply(block, _INV_TWO_PI, out=buffer)  # the copy, in cycles

    def _usable(self, port: str, block: np.ndarray, n: int) -> np.ndarray | None:
        """The modulation block if its length fits n times (n or 1), else None."""
        size = block.shape[0]
        if size == n or size == 1:
            if self._warned_length:
                self._warned_length.pop(port, None)
            return block
        if self._warned_length.get(port) != size:
            self._warned_length[port] = size
            logger.warning(
                f"{self.name}: {port} has {size} values for {n} times "
                f"(needs {n} or 1); it is ignored until the lengths match"
            )
        return None

    def _on_times(self, values: list[PortValue]):
        times = values[0]
        n = times.shape[0]
        if n == 0:
            return
        if self._cycles.shape[0] != n:
            self._allocate(n)
        cycles, work = self._cycles, self._work

        # c = frequency * t + I_fm + pm / 2pi + constant, in cycles (f64).
        # Everything constant within the block joins one scalar, added once.
        frequency = self._frequency
        constant = self._constant_cycles
        fm_samples = None
        if self._fm is not None:
            fm = self._usable("fm", self._fm, n)
            if fm is not None and fm.shape[0] > 1:
                fm_samples = fm
            else:  # one value (or none usable): a frequency offset, no integration
                deviation = 0.0 if fm is None else float(fm[0])
                frequency += deviation
                constant += self._fm_constant(times, deviation)
        np.multiply(times, frequency, out=cycles)
        if fm_samples is not None:
            constant += self._add_fm_samples(times, fm_samples, cycles)
        if self._pm_cycles is not None:
            pm_cycles = self._usable("pm", self._pm_cycles, n)
            if pm_cycles is not None:
                if pm_cycles.shape[0] == n:
                    np.add(cycles, pm_cycles, out=cycles)
                else:
                    constant += float(pm_cycles[0])
        if constant:
            np.add(cycles, constant, out=cycles)

        # u = frac(c), 0 <= u < 1 (floor keeps u exact; np.mod is slower)
        np.floor(cycles, out=work)
        np.subtract(cycles, work, out=cycles)

        series, scale, bias = self._series, self._scale, self._bias
        waveform = self._waveform
        if waveform == "sine":
            np.multiply(cycles, _TWO_PI, out=cycles)
            if self._sine_unscaled:
                np.sin(cycles, out=series, casting="same_kind")
            else:
                np.sin(cycles, out=cycles)
                np.multiply(cycles, scale, out=series, casting="same_kind")
                if bias:
                    np.add(series, bias, out=series)
        elif waveform == "square":
            np.less(cycles, 0.5, out=self._mask)
            np.multiply(self._mask, scale, out=series, casting="same_kind")
            np.add(series, bias, out=series)
        elif waveform == "triangle":
            np.subtract(cycles, 0.5, out=cycles)
            np.abs(cycles, out=cycles)
            np.multiply(cycles, scale, out=cycles)
            np.add(cycles, bias, out=series, casting="same_kind")
        else:  # saw
            np.multiply(cycles, scale, out=cycles)
            np.add(cycles, bias, out=series, casting="same_kind")
        self._output_series.dispatch([series])

    def _fm_start(self, first_time: float, first_fm: float) -> tuple[float, float]:
        """(cycles before this block, last time) after restarting if the time went back."""
        if self._last_time is None or first_time < self._last_time:
            # First block, or the time went back (e.g. a Clock reset): start over.
            self._fm_cycles = 0.0
            self._last_time, self._last_fm = first_time, first_fm
        return self._fm_cycles, self._last_time

    def _fm_constant(self, times: np.ndarray, deviation: float) -> float:
        """Constant fm: I(t) = I0 + deviation * (t - t0). Returns the cycles to add
        besides deviation * t (which the caller adds to the frequency)."""
        first_time, last_time = float(times[0]), float(times[-1])
        before, previous_time = self._fm_start(first_time, deviation)
        # cycles at t0: trapezoid over the gap since the previous block
        at_first = before + 0.5 * (self._last_fm + deviation) * (first_time - previous_time)
        self._fm_cycles = (at_first + deviation * (last_time - first_time)) % 1.0
        self._last_time, self._last_fm = last_time, deviation
        return at_first - deviation * first_time

    def _add_fm_samples(self, times: np.ndarray, fm: np.ndarray, cycles: np.ndarray) -> float:
        """Add the trapezoid integral of per-sample fm to cycles; returns the
        cycles carried from earlier blocks, for the caller's constant."""
        step, work = self._step, self._work
        first_time = float(times[0])
        first_fm = float(fm[0])
        before, previous_time = self._fm_start(first_time, first_fm)
        # step[k] = t[k] - t[k-1]; work[k] = fm[k-1] + fm[k] (the previous block's last values at k = 0)
        np.subtract(times[1:], times[:-1], out=self._step_tail)
        step[0] = first_time - previous_time
        np.add(fm[1:], fm[:-1], out=self._work_tail)
        work[0] = self._last_fm + first_fm
        np.multiply(step, work, out=step)
        np.cumsum(step, out=step)
        np.multiply(step, 0.5, out=step)
        np.add(cycles, step, out=cycles)
        self._fm_cycles = (before + float(step[-1])) % 1.0
        self._last_time, self._last_fm = float(times[-1]), float(fm[-1])
        return before
