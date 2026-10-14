from typing import Any, NamedTuple
import numpy as np
import time
import logging
import traceback

from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)
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


logger = logging.getLogger(__name__)


class Dct2Tables(NamedTuple):
    reorder: np.ndarray
    twiddle_re: np.ndarray  # 2.0 * cos(pi * k / (2N)), real-valued
    twiddle_im: np.ndarray  # 2.0 * sin(pi * k / (2N)), real-valued


def _dct2_tables(N: int, ndim: int, axis: int) -> Dct2Tables:
    """Precompute reorder indices and twiddle factors for _dct2."""
    even_idx = np.arange(0, N, 2)
    odd_idx = np.arange(1, N, 2)[::-1]
    reorder = np.concatenate([even_idx, odd_idx])

    k = np.arange(N, dtype=np.float64)
    shape = [1] * ndim
    shape[axis] = N
    angle = np.pi * k.reshape(shape) / (2 * N)
    # twiddle = exp(-j * angle), real part = cos(angle), imag part = -sin(angle)
    # result = 2 * Re(V * twiddle) = 2 * (Vr * cos - Vi * (-sin)) = 2*Vr*cos + 2*Vi*sin
    # Fold 2.0 into precomputed arrays
    twiddle_re = 2.0 * np.cos(angle)
    twiddle_im = 2.0 * np.sin(angle)

    return Dct2Tables(reorder, twiddle_re, twiddle_im)


def _dct2(
    x: np.ndarray,
    axis: int = -1,
    norm: str | None = None,
    *,
    tables: Dct2Tables | None = None,
) -> np.ndarray:
    """DCT Type-II via FFT.

    Reference: https://doi.org/10.1109/TASSP.1980.1163351
    Formula: y[k] = 2 * sum_{n=0}^{N-1} x[n] * cos(pi * k * (2n+1) / (2N))
    """
    N = x.shape[axis]

    if tables is None:
        tables = _dct2_tables(N, x.ndim, axis)

    # 1. Reorder: even-indexed ascending, then odd-indexed descending
    v = np.take(x, tables.reorder, axis=axis)

    # 2. FFT
    V = np.fft.fft(v, axis=axis)

    # 3. Twiddle multiply (real-only arithmetic, 2.0 folded into tables)
    result = V.real * tables.twiddle_re + V.imag * tables.twiddle_im

    # 4. Orthonormal normalization
    if norm == "ortho":
        result *= np.sqrt(1.0 / (2 * N))
        idx: list[slice | int] = [slice(None)] * x.ndim
        idx[axis] = 0
        result[tuple(idx)] /= np.sqrt(2.0)

    return result


class FftNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Compute real FFT of windowed input with frequency output",
            category="FFT",
            inputs={"vector": "", "window": ""},
            outputs={"fft": "", "freqs": ""},
        )

    PROPERTIES = {
        "fs": {
            "description": "Sample rate (Hz)",
            "data_type": "u32",
            "default_value": 600,
        },
        "in_shape": {
            "description": "Input port shape string",
            "data_type": "str",
            "default_value": "[1024]",
        },
        "win_size": {
            "description": "FFT window size",
            "data_type": "u32",
            "default_value": 1024,
        },
        "axis": {
            "description": "FFT axis (1-based within port shape)",
            "data_type": "u32",
            "default_value": 1,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Fft")

        fs = 600
        win_size = 1024
        axis = 1
        freqs = np.fft.rfftfreq(win_size, 1 / fs)
        in_type = PortValueType(DataType.Float32, (win_size,))
        out_type = self._get_out_type(in_type, win_size, axis)

        input_vector = StaticTypeInputPort("vector", [in_type])
        input_vector.subscribe(id(self), self._on_input_vector)

        input_window = StaticTypeInputPort(
            "window",
            [PortValueType(DataType.Float32, (win_size,))],
        )
        input_window.subscribe(id(self), self._on_input_window)

        output_fft = StaticTypeOutputPort("fft", [out_type])
        output_freqs = StaticTypeOutputPort(
            "freqs",
            [PortValueType(DataType.Float32, (freqs.size,))],
        )

        self._input_vector = input_vector
        self._input_window = input_window
        self._output_fft = output_fft
        self._output_freqs = output_freqs
        self._freqs = freqs
        self._fs = fs
        self._win_size = win_size
        self._axis = axis
        self._in_type = in_type
        self._window = np.ones(win_size)
        self._window_reshaped = self._reshape_window(self._window, in_type, axis)

        self.inputs[input_vector.name] = input_vector
        self.inputs[input_window.name] = input_window
        self.outputs[output_fft.name] = output_fft
        self.outputs[output_freqs.name] = output_freqs

        output_freqs.dispatch([freqs[np.newaxis, :]])

    def _get_out_type(self, in_type: PortValueType, win_size: int, axis: int):
        if axis <= 0 or axis > len(in_type.shape):
            raise ValueError(f"Invalid axis: {axis}")
        if in_type.shape[axis - 1] != win_size:
            raise ValueError(f"Input shape mismatch: {in_type.shape} != {win_size}")

        out_shape = list(in_type.shape)
        out_shape[axis - 1] = win_size // 2 + 1

        return PortValueType(DataType.Complex64, tuple(out_shape))

    def _reshape_window(self, window: np.ndarray, in_type: PortValueType, axis: int):
        win_shape = [1] * (len(in_type.shape) + 1)
        win_shape[axis] = len(window)

        return window.reshape(win_shape)

    def set_properties(self, properties: dict[str, Any]):
        fs = self._fs
        if "fs" in properties:
            fs = int(properties["fs"])

        win_size = self._win_size
        if "win_size" in properties:
            win_size = int(properties["win_size"])

        axis = self._axis
        if "axis" in properties:
            axis = int(properties["axis"])

        in_type = self._in_type
        if "in_shape" in properties:
            in_type = name_to_port_value_type(f"f32{properties['in_shape']}")

        new_input_vector = self._input_vector
        if in_type != self._in_type:
            new_input_vector = StaticTypeInputPort("vector", [in_type])

        new_output_fft = self._output_fft
        if axis != self._axis or win_size != self._win_size or in_type != self._in_type:
            new_output_fft = StaticTypeOutputPort(
                "fft",
                [self._get_out_type(in_type, win_size, axis)],
            )

        new_freqs = None
        if win_size != self._win_size or fs != self._fs:
            new_freqs = np.fft.rfftfreq(win_size, 1 / fs)

        new_input_window = self._input_window
        new_window = None
        if win_size != self._win_size:
            new_input_window = StaticTypeInputPort(
                "window",
                [PortValueType(DataType.Float32, (win_size,))],
            )
            new_window = np.ones(win_size)

        new_output_freqs = self._output_freqs
        if win_size != self._win_size:
            new_output_freqs = StaticTypeOutputPort(
                "freqs",
                [PortValueType(DataType.Float32, (win_size // 2 + 1,))],
            )
        # ---

        if new_input_vector != self._input_vector:
            replace_node_input_port(
                self, self._input_vector, new_input_vector, self._on_input_vector
            )
            self._input_vector = new_input_vector

        if new_input_window != self._input_window:
            replace_node_input_port(
                self, self._input_window, new_input_window, self._on_input_window
            )
            self._input_window = new_input_window

        if new_output_fft != self._output_fft:
            replace_node_output_port(self, self._output_fft, new_output_fft, None)
            self._output_fft = new_output_fft

        if new_output_freqs != self._output_freqs:
            replace_node_output_port(self, self._output_freqs, new_output_freqs, None)
            self._output_freqs = new_output_freqs

        self._win_size = win_size
        self._fs = fs
        self._axis = axis
        self._in_type = in_type
        self._window = new_window if new_window is not None else self._window
        self._window_reshaped = self._reshape_window(self._window, in_type, axis)

        self.properties["fs"] = fs
        self.properties["win_size"] = win_size
        self.properties["axis"] = axis
        self.properties["in_shape"] = in_type.shape_str

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

        if new_freqs is not None:
            self._output_freqs.dispatch([new_freqs[np.newaxis, :]])

        if self.parent_graph is not None and (new_freqs is not None):
            self.parent_graph.flush_outputs()

    def _on_input_window(self, values: list[PortValue]):
        window_array: np.ndarray = values[0]
        window = window_array[-1]
        if window.size != self._win_size:
            logger.warning(f"Window size mismatch: {window.size} != {self._win_size}")
            return

        self._window = window
        self._window_reshaped = self._reshape_window(
            self._window, self._in_type, self._axis
        )

    def _on_input_vector(self, values: list[PortValue]):
        vector_array: np.ndarray = values[0]
        vector_array = vector_array * self._window_reshaped
        fft_array = np.fft.rfft(vector_array, axis=self._axis)
        self._output_fft.dispatch([fft_array])
        # print(f"{fft_array.shape=}")


# class IFftNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "IFft")

#         fs = 600
#         input_fft = StaticTypeInputPort(
#             "fft", PortDirection.INPUT, [DataType.Complex64Vec]
#         )
#         input_fft.subscribe(id(self), self._on_fft)

#         output_vector = StaticTypeOutputPort(
#             "vector", PortDirection.OUTPUT, [DataType.Float32Vec]
#         )

#         self._output_vector = output_vector
#         self._fs = fs

#         self.inputs[input_fft.name] = input_fft
#         self.outputs[output_vector.name] = output_vector

#         self.properties["fs"] = fs

#     def set_properties(self, properties: dict[str, PropertyDataType]):
#         fs = self._fs

#         if "fs" in properties:
#             fs = int(properties["fs"])

#         self._fs = fs
#         self.properties["fs"] = fs

#         if self.parent_graph is not None:
#             self.parent_graph.notify_properties_changed(self)

#     def _on_fft(self, values_any: list[Any]):
#         fft_array: np.ndarray = values_any[0]

#         time_series_array = np.fft.irfft(fft_array, axis=1)
#         self._output_vector.dispatch([time_series_array])


class StftNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Short-Time Fourier Transform for streaming spectral analysis",
            category="FFT",
            inputs={"series": "", "window": "", "reset": ""},
            outputs={"fft": "", "freqs": ""},
        )

    PROPERTIES = {
        "in_shape": {
            "description": "Input port shape string",
            "data_type": "str",
            "default_value": "",
        },
        "fs": {
            "description": "Sample rate (Hz)",
            "data_type": "u32",
            "default_value": 600,
        },
        "win_size": {
            "description": "FFT window size",
            "data_type": "u32",
            "default_value": 1024,
        },
        "hop": {
            "description": "Hop size (samples)",
            "data_type": "u32",
            "default_value": 10,
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Stft")

        in_type = PortValueType(DataType.Float32)
        fs = 600
        win_size = 1024
        hop = 10
        freqs = np.fft.rfftfreq(win_size, 1 / fs)
        win = np.ones(win_size)

        input_series = StaticTypeInputPort("series", [in_type])
        input_series.subscribe(id(self), self._on_input_series)

        input_window = StaticTypeInputPort(
            "window",
            [PortValueType(DataType.Float32, (win_size,))],
        )
        input_window.subscribe(id(self), self._on_input_window)

        input_reset = StaticTypeInputPort("reset", [PortValueType(DataType.Any)])
        input_reset.subscribe(id(self), self._on_input_reset)

        output_fft = StaticTypeOutputPort(
            "fft",
            [
                PortValueType(
                    DataType.Complex64,
                    (
                        win_size // 2 + 1,
                        *in_type.shape,
                    ),
                )
            ],
        )

        output_freqs = StaticTypeOutputPort(
            "freqs",
            [PortValueType(DataType.Float32, (freqs.size,))],
        )

        output_freqs.dispatch([freqs[np.newaxis, :]])

        self._hop = hop
        self._fs = fs
        self._win_size = win_size
        self._input_window = input_window
        self._input_series = input_series
        self._output_fft = output_fft
        self._output_freqs = output_freqs
        self._win = win
        self._in_type = in_type
        self._buffer: np.ndarray | None = None

        self.inputs[input_series.name] = input_series
        self.inputs[input_window.name] = input_window
        self.inputs[input_reset.name] = input_reset
        self.outputs[output_freqs.name] = output_freqs
        self.outputs[output_fft.name] = output_fft

    def set_properties(self, properties: dict[str, Any]):
        fs = self._fs
        if "fs" in properties:
            fs = int(properties["fs"])

        win_size = self._win_size
        if "win_size" in properties:
            win_size = int(properties["win_size"])

        hop = self._hop
        if "hop" in properties:
            hop = int(properties["hop"])

        in_type = self._in_type
        if "in_shape" in properties:
            in_type = name_to_port_value_type(f"f32{properties['in_shape']}")

        new_input_series = self._input_series
        if in_type != self._in_type:
            new_input_series = StaticTypeInputPort("series", [in_type])

        new_freqs = None
        if win_size != self._win_size or fs != self._fs:
            new_freqs = np.fft.rfftfreq(win_size, 1 / fs)

        new_input_window = self._input_window
        new_window = None
        if win_size != self._win_size:
            new_input_window = StaticTypeInputPort(
                "window",
                [PortValueType(DataType.Float32, (win_size,))],
            )
            new_window = np.ones(win_size)

        new_output_fft = self._output_fft
        if win_size != self._win_size or in_type != self._in_type:
            new_output_fft = StaticTypeOutputPort(
                "fft",
                [
                    PortValueType(
                        DataType.Complex64,
                        (
                            win_size // 2 + 1,
                            *in_type.shape,
                        ),
                    )
                ],
            )

        new_output_freqs = self._output_freqs
        if win_size != self._win_size:
            new_output_freqs = StaticTypeOutputPort(
                "freqs",
                [PortValueType(DataType.Float32, (win_size // 2 + 1,))],
            )

        if new_input_series != self._input_series:
            replace_node_input_port(
                self, self._input_series, new_input_series, self._on_input_series
            )
            self._input_series = new_input_series

        if new_input_window != self._input_window:
            replace_node_input_port(
                self, self._input_window, new_input_window, self._on_input_window
            )
            self._input_window = new_input_window

        if new_output_fft != self._output_fft:
            replace_node_output_port(self, self._output_fft, new_output_fft)
            self._output_fft = new_output_fft

        if new_output_freqs != self._output_freqs:
            replace_node_output_port(self, self._output_freqs, new_output_freqs)
            self._output_freqs = new_output_freqs

        if in_type != self._in_type or win_size != self._win_size:
            self._buffer = None

        self._win_size = win_size
        self._hop = hop
        self._fs = fs
        self._in_type = in_type
        self._win = new_window if new_window is not None else self._win

        self.properties["fs"] = fs
        self.properties["hop"] = hop
        self.properties["win_size"] = win_size
        self.properties["in_shape"] = in_type.shape_str

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

        if new_freqs is not None:
            self._output_freqs.dispatch([new_freqs[np.newaxis, :]])

        if self.parent_graph is not None and (new_freqs is not None):
            self.parent_graph.flush_outputs()

    def _on_input_window(self, values: list[PortValue]):
        window_array: np.ndarray = values[0]  # type: ignore
        if len(window_array) == 0:
            return

        window = window_array[-1]
        if window.size != self._win.size:
            logger.warning(f"Window size mismatch: {window.size} != {self._win.size}")
            return

        self._win = window

    def _on_input_series(self, values_any: list[Any]):
        input_series: np.ndarray = values_any[0]

        self._buffer = (
            input_series
            if self._buffer is None
            else np.concatenate([self._buffer, input_series], axis=0)
        )

        if len(self._buffer) < self._win_size:
            return

        # start_time = time.time()
        try:
            # Number of frames available for batch processing
            num_windows = (len(self._buffer) - self._win_size) // self._hop + 1

            # Get the buffer's shape and strides
            buffer_shape = self._buffer.shape
            buffer_strides = self._buffer.strides

            # Preserve every dimension except the leading (time) axis
            other_dims = buffer_shape[1:] if len(buffer_shape) > 1 else ()
            other_strides = buffer_strides[1:] if len(buffer_strides) > 1 else ()

            # Compute the framed shape and strides
            new_shape = (num_windows, self._win_size) + other_dims
            new_strides = (
                buffer_strides[0] * self._hop,  # type: ignore
                buffer_strides[0],  # type: ignore
            ) + other_strides

            # Frame the signal with stride tricks (zero-copy view)
            frames = np.lib.stride_tricks.as_strided(
                self._buffer,
                shape=new_shape,
                strides=new_strides,
                writeable=False,
            )

            # Reshape the window function for broadcasting:
            # first dim = frame count, second = window size, rest match the input
            win_shape = [1, self._win_size] + [1] * (len(new_shape) - 2)
            win_array = self._win.reshape(win_shape)

            frames = frames * win_array

            # print(f"{frames.shape=}, {self._buffer.shape=}, {win_array.shape=}")
            # print(f"{frames=}")
            # return

            # Run the FFT and obtain the complex spectrum
            fft_results = np.fft.rfft(frames, axis=1)
            # print(f"{fft_results.shape=}")
            # return

            self._buffer = self._buffer[num_windows * self._hop :]
            # end_time = time.time()
        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            traceback.print_exc()
            return

        # print(f"Time: {end_time - start_time:.6f}")
        self._output_fft.dispatch([fft_results])
        # print(f"{fft_results.shape=}")

    def _on_input_reset(self, values: list[PortValue]):
        self._buffer = None


class IstftNode(BaseNode):
    """_summary_
    https://stackoverflow.com/questions/2459295/invertible-stft-and-istft-in-python

    https://jp.mathworks.com/help/signal/ref/istft.html

    Args:
        BaseNode (_type_): _description_
    """

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Inverse Short-Time Fourier Transform for time-domain reconstruction",
            category="FFT",
            inputs={"fft": "", "window": "", "reset": ""},
            outputs={"series": ""},
        )

    PROPERTIES = {
        "in_shape": {
            "description": "Input port shape string",
            "data_type": "str",
            "default_value": "[513]",
        },
        "fs": {
            "description": "Sample rate (Hz)",
            "data_type": "u32",
            "default_value": 600,
        },
        "win_size": {
            "description": "FFT window size",
            "data_type": "u32",
            "default_value": 1024,
        },
        "hop": {
            "description": "Hop size (samples)",
            "data_type": "u32",
            "default_value": 10,
        },
    }

    @staticmethod
    def _compute_dual_win(win: np.ndarray, hop: int) -> np.ndarray:
        """Return the dual window used to invert an STFT via overlap-add.

        Perfect reconstruction requires normalizing each output sample by
        the total squared-window weight it receives from all overlapping
        frames: dual[n] = win[n] / D[n], with D[n] the sum of win[j]^2 over
        every j congruent to n modulo ``hop``. Since D[n] depends only on
        n mod hop, it is computed once per residue and tiled.
        """
        num_rows = -(-len(win) // hop)  # ceil division
        squared = np.zeros(num_rows * hop, dtype=win.dtype)
        squared[: len(win)] = win * win
        weight_per_residue = squared.reshape(num_rows, hop).sum(axis=0)
        total_weight = np.tile(weight_per_residue, num_rows)[: len(win)]

        # A residue whose weight is at the level of summation round-off
        # (num_rows additions of values up to the maximum weight) is
        # effectively zero and cannot be normalized.
        threshold = np.finfo(win.dtype).eps * num_rows * total_weight.max()
        if not np.all(total_weight > threshold):
            raise ValueError(
                f"window (length {len(win)}) with hop {hop} leaves samples "
                "without overlap coverage; the STFT cannot be inverted"
            )
        return win / total_weight

    def __init__(self, name: str):
        super().__init__(name, "Istft")

        win_size = 1024
        in_type = PortValueType(DataType.Complex64, (win_size // 2 + 1,))
        win = np.ones(win_size)
        hop = 10
        fs = 600

        input_fft = StaticTypeInputPort("fft", [in_type])
        input_window = StaticTypeInputPort(
            "window", [PortValueType(DataType.Float32, (win_size,))]
        )
        input_reset = StaticTypeInputPort("reset", [PortValueType(DataType.Any)])
        input_fft.subscribe(id(self), self._on_input_fft)
        input_window.subscribe(id(self), self._on_input_window)
        input_reset.subscribe(id(self), self._on_input_reset)

        output_series = StaticTypeOutputPort(
            "series", [PortValueType(DataType.Float32, in_type.shape[1:])]
        )

        self._fs = fs
        self._win = win
        self._win_size = win_size
        self._hop = hop
        self._in_type = in_type

        self._series0 = np.zeros((self._win_size, *in_type.shape[1:]))
        self._series1 = np.zeros((self._win_size, *in_type.shape[1:]))
        self._series_start = 0
        self._dual_win: np.ndarray | None = self._compute_dual_win(win, hop)

        self._input_fft = input_fft
        self._input_window = input_window
        self._output_series = output_series
        self.inputs[input_fft.name] = input_fft
        self.inputs[input_window.name] = input_window
        self.inputs[input_reset.name] = input_reset
        self.outputs[output_series.name] = output_series

    def set_properties(self, properties: dict[str, Any]):
        fs = self._fs
        if "fs" in properties:
            fs = int(properties["fs"])

        hop = self._hop
        if "hop" in properties:
            hop = int(properties["hop"])

        win_size = self._win.size
        if "win_size" in properties:
            win_size = int(properties["win_size"])

        in_type = self._in_type
        if "in_shape" in properties:
            in_type = name_to_port_value_type(f"c64{properties['in_shape']}")

        if in_type.shape[0] != win_size // 2 + 1:
            raise ValueError(
                f"Invalid input or window shape: {(in_type.shape[0])=} != {(win_size // 2 + 1)=}"
            )

        if hop <= 0:
            raise ValueError(f"hop must be positive: {hop}")

        if hop > win_size:
            raise ValueError(
                f"hop must be less than or equal to win_size: {hop} > {win_size}"
            )

        new_input_fft = self._input_fft
        if in_type != self._in_type:
            new_input_fft = StaticTypeInputPort("fft", [in_type])

        new_input_window = self._input_window
        new_win = None
        if win_size != self._win.size:
            new_input_window = StaticTypeInputPort(
                "window",
                [PortValueType(DataType.Float32, (win_size,))],
            )
            new_win = np.ones(win_size)

        new_dual_win = None
        if win_size != self._win.size or fs != self._fs or hop != self._hop:
            new_dual_win = self._compute_dual_win(
                new_win if new_win is not None else self._win, hop
            )

        if win_size != self._win_size or in_type != self._in_type:
            self._series0 = np.zeros((win_size, *in_type.shape[1:]))
            self._series1 = np.zeros((win_size, *in_type.shape[1:]))
            self._series_start = 0

        new_output_series = self._output_series
        if in_type != self._in_type:
            new_output_series = StaticTypeOutputPort(
                "series", [PortValueType(DataType.Float32, in_type.shape[1:])]
            )

        if new_input_fft != self._input_fft:
            replace_node_input_port(
                self, self._input_fft, new_input_fft, self._on_input_fft
            )
            self._input_fft = new_input_fft

        if new_input_window != self._input_window:
            replace_node_input_port(
                self, self._input_window, new_input_window, self._on_input_window
            )
            self._input_window = new_input_window

        if new_output_series != self._output_series:
            replace_node_output_port(self, self._output_series, new_output_series)
            self._output_series = new_output_series

        self._fs = fs
        self._win = new_win if new_win is not None else self._win
        self._win_size = win_size
        self._in_type = in_type
        self._hop = hop
        self._dual_win = new_dual_win if new_dual_win is not None else self._dual_win

        self.properties["in_shape"] = in_type.shape_str
        self.properties["fs"] = fs
        self.properties["hop"] = hop
        self.properties["win_size"] = win_size

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_window(self, values: list[PortValue]):
        window_array: np.ndarray = values[0]
        if len(window_array) == 0:
            return

        window = window_array[-1]
        if window.size != self._win.size:
            logger.warning(f"Window size mismatch: {window.size} != {self._win.size}")
            return

        self._win = window

        try:
            self._dual_win = self._compute_dual_win(window, self._hop)
        except ValueError as e:
            logger.warning(f"Failed to compute dual window: {e}")
            self._dual_win = None

    def _on_input_reset(self, values: list[PortValue]):
        self._series0 = np.zeros_like(self._series0)
        self._series1 = np.zeros_like(self._series1)
        self._series_start = 0

    def _on_input_fft(self, values: list[PortValue]):
        if self._dual_win is None:
            logger.warning("Dual window is not computed. Cannot perform Istft.")
            return

        fft_array: np.ndarray = values[0]

        input_shape = fft_array.shape

        # Determine whether the input has extra (channel) dimensions
        has_extra_dims = len(input_shape) > 2

        # Reshape dual_win for broadcasting
        if has_extra_dims:
            # Expand the shape to cover the extra dimensions,
            # e.g. [win_size] -> [win_size, 1, 1, ...]
            expanded_dims = [self._win_size] + [1] * (len(input_shape) - 2)
            dual_win = self._dual_win.reshape(expanded_dims)
        else:
            dual_win = self._dual_win

        # Run the inverse FFT
        time_series_array = np.fft.irfft(fft_array, axis=1)

        # Apply the dual window
        time_series_array = time_series_array * dual_win

        # Collect the reconstructed blocks
        results = []

        for time_series in time_series_array:
            self._series0[self._series_start :] += time_series[
                : self._win_size - self._series_start
            ]
            self._series1[: self._series_start] += time_series[
                self._win_size - self._series_start :
            ]

            self._series_start = self._series_start + self._hop

            if self._series_start >= self._win_size:
                results.append(self._series0.copy())

                self._series0, self._series1 = self._series1, self._series0
                self._series_start -= self._win_size
                self._series1.fill(0)

        # Dispatch once after all frames have been processed
        if results:
            results_array = np.concatenate(results)

            # print(results_array.shape)
            self._output_series.dispatch([results_array])


class MfccNode(BaseNode):
    """Mel-Frequency Cepstral Coefficients (MFCC) extraction node.

    Input: FFT result from FftNode or StftNode
        - c64[fft_size] (batch shape: batch, fft_size)
        - c64[fft_size x C] (batch shape: batch, fft_size, C)
        - c64[fft_size x C x D] (batch shape: batch, fft_size, C, D)
        Processing is always along axis=0 of port shape (axis=1 after batch).
    Output: MFCC coefficients with same extra dimensions
        - f32[n_mfcc] (batch shape: batch, n_mfcc)
        - f32[n_mfcc x C] (batch shape: batch, n_mfcc, C)
        - f32[n_mfcc x C x D] (batch shape: batch, n_mfcc, C, D)

    The mel filterbank is pre-computed and cached for efficiency.
    """

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Extract Mel-Frequency Cepstral Coefficients from FFT input",
            category="FFT",
            inputs={"fft": ""},
            outputs={"mfcc": ""},
        )

    PROPERTIES = {
        "fs": {
            "description": "Sample rate (Hz)",
            "data_type": "u32",
            "default_value": 48000,
        },
        "n_mels": {
            "description": "Number of mel filter bands",
            "data_type": "u32",
            "default_value": 128,
        },
        "n_mfcc": {
            "description": "Number of MFCC coefficients",
            "data_type": "u32",
            "default_value": 20,
        },
        "fmin": {
            "description": "Minimum frequency (Hz)",
            "data_type": "f64",
            "default_value": 20.0,
        },
        "fmax": {
            "description": "Maximum frequency (Hz)",
            "data_type": "f64",
            "default_value": 20000.0,
        },
        "in_type": {
            "description": "Input port value type string",
            "data_type": "str",
            "default_value": "c64[2049]",
        },
    }

    def __init__(self, name: str):
        super().__init__(name, "Mfcc")

        # Default values for music analysis at 48kHz
        fs = 48000
        n_mels = 128  # More mel bands for music (captures harmonics better)
        n_mfcc = 20  # More coefficients for music analysis
        fmin = 20.0  # Human hearing lower limit
        fmax = 20000.0  # Human hearing upper limit

        # Default input type: c64[2049] (mono, 4096 FFT)
        in_type = PortValueType(DataType.Complex64, (2049,))

        # fft_size is the first dimension of in_type shape
        fft_size = in_type.shape[0]

        # Output type: replace fft_size with n_mfcc, keep extra dimensions
        out_shape = (n_mfcc,) + in_type.shape[1:]
        out_type = PortValueType(DataType.Float32, out_shape)

        # Pre-compute mel filterbank
        mel_filterbank = self._create_mel_filterbank(fs, fft_size, n_mels, fmin, fmax)

        input_fft = StaticTypeInputPort("fft", [in_type])
        input_fft.subscribe(id(self), self._on_input_fft)

        output_mfcc = StaticTypeOutputPort("mfcc", [out_type])

        self._input_fft = input_fft
        self._output_mfcc = output_mfcc

        self._fs = fs
        self._n_mels = n_mels
        self._n_mfcc = n_mfcc
        self._fmin = fmin
        self._fmax = fmax
        self._in_type = in_type
        self._mel_filterbank = mel_filterbank
        self._dct2_tables = _dct2_tables(n_mels, 1 + len(in_type.shape), axis=1)

        self.inputs[input_fft.name] = input_fft
        self.outputs[output_mfcc.name] = output_mfcc

    @staticmethod
    def _hz_to_mel(hz: float) -> float:
        """Convert Hz to mel scale."""
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    @staticmethod
    def _mel_to_hz(mel: float) -> float:
        """Convert mel scale to Hz."""
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    def _create_mel_filterbank(
        self, fs: int, fft_size: int, n_mels: int, fmin: float, fmax: float
    ) -> np.ndarray:
        """Create mel filterbank matrix.

        Args:
            fs: Sampling rate
            fft_size: Number of FFT bins (n_fft // 2 + 1)
            n_mels: Number of mel filters
            fmin: Minimum frequency
            fmax: Maximum frequency

        Returns:
            Mel filterbank matrix of shape (n_mels, fft_size)
        """
        # n_fft is (fft_size - 1) * 2
        n_fft = (fft_size - 1) * 2

        # Create mel scale points
        mel_min = self._hz_to_mel(fmin)
        mel_max = self._hz_to_mel(fmax)
        mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
        hz_points = np.array([self._mel_to_hz(m) for m in mel_points])

        # Convert to FFT bin indices
        bin_points = np.floor((n_fft + 1) * hz_points / fs).astype(int)
        bin_points = np.clip(bin_points, 0, fft_size - 1)

        # Create triangular filterbank
        filterbank = np.zeros((n_mels, fft_size), dtype=np.float32)
        for i in range(n_mels):
            left = bin_points[i]
            center = bin_points[i + 1]
            right = bin_points[i + 2]

            # Rising slope
            if center > left:
                filterbank[i, left:center] = np.linspace(
                    0, 1, center - left, dtype=np.float32
                )
            # Falling slope
            if right > center:
                filterbank[i, center:right] = np.linspace(
                    1, 0, right - center, dtype=np.float32
                )

        return filterbank

    def set_properties(self, properties: dict[str, PropertyDataType]):
        # 1. Extract properties
        fs = self._fs
        if "fs" in properties:
            fs = int(properties["fs"])

        n_mels = self._n_mels
        if "n_mels" in properties:
            n_mels = int(properties["n_mels"])
            if n_mels < 1:
                raise ValueError("n_mels must be at least 1")

        n_mfcc = self._n_mfcc
        if "n_mfcc" in properties:
            n_mfcc = int(properties["n_mfcc"])
            if n_mfcc < 1:
                raise ValueError("n_mfcc must be at least 1")
            if n_mfcc > n_mels:
                raise ValueError("n_mfcc cannot exceed n_mels")

        fmin = self._fmin
        if "fmin" in properties:
            fmin = float(properties["fmin"])

        fmax = self._fmax
        if "fmax" in properties:
            fmax = float(properties["fmax"])

        in_type = self._in_type
        if "in_type" in properties:
            in_type_str = properties["in_type"]
            if not isinstance(in_type_str, str):
                raise ValueError("in_type must be a string")
            in_type = name_to_port_value_type(in_type_str)
            if in_type.data_type != DataType.Complex64:
                raise ValueError("in_type must be Complex64")
            if len(in_type.shape) == 0:
                raise ValueError("in_type must have at least one dimension (fft_size)")

        # fft_size is the first dimension of in_type shape
        fft_size = in_type.shape[0]

        # 2. Check if ports need to be recreated
        # Output type: replace fft_size with n_mfcc, keep extra dimensions
        out_shape = (n_mfcc,) + in_type.shape[1:]
        out_type = PortValueType(DataType.Float32, out_shape)

        new_input_fft = self._input_fft
        if in_type != self._in_type:
            new_input_fft = StaticTypeInputPort("fft", [in_type])

        new_output_mfcc = self._output_mfcc
        if n_mfcc != self._n_mfcc or in_type != self._in_type:
            new_output_mfcc = StaticTypeOutputPort("mfcc", [out_type])

        # 3. Recalculate mel filterbank if necessary
        old_fft_size = self._in_type.shape[0]
        new_mel_filterbank = None
        if (
            fs != self._fs
            or n_mels != self._n_mels
            or fmin != self._fmin
            or fmax != self._fmax
            or fft_size != old_fft_size
        ):
            new_mel_filterbank = self._create_mel_filterbank(
                fs, fft_size, n_mels, fmin, fmax
            )

        # 4. Replace ports if changed
        if new_input_fft != self._input_fft:
            replace_node_input_port(
                self, self._input_fft, new_input_fft, self._on_input_fft
            )
            self._input_fft = new_input_fft

        if new_output_mfcc != self._output_mfcc:
            replace_node_output_port(self, self._output_mfcc, new_output_mfcc)
            self._output_mfcc = new_output_mfcc

        # 5. Update state
        if n_mels != self._n_mels or in_type != self._in_type:
            self._dct2_tables = _dct2_tables(n_mels, 1 + len(in_type.shape), axis=1)

        self._fs = fs
        self._n_mels = n_mels
        self._n_mfcc = n_mfcc
        self._fmin = fmin
        self._fmax = fmax
        self._in_type = in_type
        if new_mel_filterbank is not None:
            self._mel_filterbank = new_mel_filterbank

        self.properties["fs"] = fs
        self.properties["n_mels"] = n_mels
        self.properties["n_mfcc"] = n_mfcc
        self.properties["fmin"] = fmin
        self.properties["fmax"] = fmax
        self.properties["in_type"] = in_type.name

        # 6. Notify graph
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_fft(self, values: list[PortValue]):
        """Process FFT input and compute MFCC.

        Input shape (with batch dimension):
            - (batch, fft_size)
            - (batch, fft_size, C)
            - (batch, fft_size, C, D)
            Processing is always along axis=1 (fft_size axis).
        Output shape:
            - (batch, n_mfcc)
            - (batch, n_mfcc, C)
            - (batch, n_mfcc, C, D)
        """
        fft_array: np.ndarray = values[0]

        try:
            # 1. Compute power spectrum: |FFT|^2
            power_spectrum = np.abs(fft_array) ** 2

            # 2. Apply mel filterbank
            # power_spectrum: (batch, fft_size, *extra)
            # mel_filterbank: (n_mels, fft_size)
            # result: (batch, n_mels, *extra)
            #
            # tensordot contracts axis=1 of power_spectrum with axis=1 of mel_filterbank
            # Result shape: (batch, *extra, n_mels) - n_mels is at the end
            mel_spectrum = np.tensordot(
                power_spectrum, self._mel_filterbank, axes=([1], [1])
            )
            # Move n_mels from last position to axis=1
            mel_spectrum = np.moveaxis(mel_spectrum, -1, 1)

            # 3. Log transform (avoid log(0))
            mel_spectrum = np.log(mel_spectrum + 1e-10)

            # 4. DCT to get MFCCs
            # mel_spectrum: (batch, n_mels, *extra)
            # Apply DCT along axis=1 (n_mels axis) and take first n_mfcc coefficients
            mfcc_full = _dct2(
                mel_spectrum, axis=1, norm="ortho", tables=self._dct2_tables
            )
            # Use slicing along axis=1 to get first n_mfcc coefficients
            slices: list[slice] = [slice(None)] * mfcc_full.ndim
            slices[1] = slice(None, self._n_mfcc)
            mfcc = mfcc_full[tuple(slices)]

            self._output_mfcc.dispatch([mfcc.astype(np.float32)])

        except Exception as e:
            logger.warning(f"{self.name}: {e}")
            traceback.print_exc()
