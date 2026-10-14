import numpy as np
import logging

from nonoha_core.port import StaticTypeOutputPort
from nonoha_core.node import BaseNode, NodeDoc, replace_node_output_port
from nonoha_core.data_type import (
    DataType,
    PortValueType,
    PropertyDataType,
)

logger = logging.getLogger(__name__)


# --- numpy-only window functions (scipy-free) --------------------------------
# Reimplements the subset of scipy.signal.windows that WindowNode used, with
# numpy only. Values match scipy.signal.windows.<name>(size) for the default
# symmetric (sym=True) window. Windows requiring extra parameters
# (kaiser: beta, gaussian: std, ...) are intentionally unsupported here because
# the node only passes `size`; add node properties first to enable them.
#
# Windows are recomputed only when the name or size changes (cached in
# `self._window`), never per sample, so a numpy implementation keeps the same
# performance as the previous scipy path.


def _general_cosine(size: int, coeffs) -> np.ndarray:
    """Symmetric generalized cosine window (matches scipy general_cosine sym=True)."""
    fac = np.linspace(-np.pi, np.pi, size)
    w = np.zeros(size)
    for k, a in enumerate(coeffs):
        w += a * np.cos(k * fac)
    return w


# Coefficients identical to scipy.signal.windows
_COSINE_COEFFS = {
    "hann": (0.5, 0.5),
    "hamming": (0.54, 0.46),
    "blackman": (0.42, 0.5, 0.08),
    "blackmanharris": (0.35875, 0.48829, 0.14128, 0.01168),
    "nuttall": (0.3635819, 0.4891775, 0.1365995, 0.0106411),
    "flattop": (
        0.21557895,
        0.41663158,
        0.277263158,
        0.083578947,
        0.006947368,
    ),
}


def _triang(size: int) -> np.ndarray:
    """Triangular window (matches scipy.signal.windows.triang sym=True)."""
    n = np.arange(1, (size + 1) // 2 + 1)
    if size % 2 == 0:
        w = (2 * n - 1.0) / size
        w = np.r_[w, w[::-1]]
    else:
        w = 2 * n / (size + 1.0)
        w = np.r_[w, w[-2::-1]]
    return w


def _cosine(size: int) -> np.ndarray:
    """Cosine (half-sine) window (matches scipy.signal.windows.cosine sym=True)."""
    return np.sin(np.pi / size * (np.arange(size) + 0.5))


def _tukey(size: int, alpha: float = 0.5) -> np.ndarray:
    """Tukey (tapered cosine) window (matches scipy.signal.windows.tukey sym=True)."""
    if alpha <= 0:
        return np.ones(size)
    if alpha >= 1.0:
        return _general_cosine(size, (0.5, 0.5))  # == hann
    n = np.arange(size)
    width = int(np.floor(alpha * (size - 1) / 2.0))
    n1 = n[: width + 1]
    n2 = n[width + 1 : size - width - 1]
    n3 = n[size - width - 1 :]
    w1 = 0.5 * (1 + np.cos(np.pi * (-1 + 2.0 * n1 / (alpha * (size - 1)))))
    w2 = np.ones(n2.shape)
    w3 = 0.5 * (1 + np.cos(np.pi * (-2.0 / alpha + 1 + 2.0 * n3 / (alpha * (size - 1)))))
    return np.concatenate((w1, w2, w3))


_SIMPLE_WINDOWS = {"boxcar", "rectangular", "rect", "bartlett", "triang", "cosine", "sine", "tukey"}


def supported_windows() -> list[str]:
    """Names accepted by `_make_window` (numpy-only)."""
    return sorted(set(_COSINE_COEFFS) | _SIMPLE_WINDOWS)


def _make_window(name: str, size: int) -> np.ndarray:
    """Generate a window by name using numpy only (scipy-free).

    Matches scipy.signal.windows.<name>(size) for the default symmetric window.
    """
    key = name.lower()
    if size <= 0:
        return np.zeros(max(size, 0))
    if size == 1:
        return np.ones(1)

    if key in _COSINE_COEFFS:
        return _general_cosine(size, _COSINE_COEFFS[key])
    if key in ("boxcar", "rectangular", "rect"):
        return np.ones(size)
    if key == "bartlett":
        return np.bartlett(size)
    if key == "triang":
        return _triang(size)
    if key in ("cosine", "sine"):
        return _cosine(size)
    if key == "tukey":
        return _tukey(size)

    raise ValueError(
        f"Unsupported window {name!r} (numpy-only WindowNode). "
        f"Supported: {supported_windows()}. "
        "Windows needing extra parameters (kaiser/gaussian/...) require node properties."
    )


class WindowNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Generate a window function (e.g. hann, blackman) for spectral analysis",
            category="Signal Generation",
            inputs={},
            outputs={"window": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "Window")

        size = 1024
        # blackman, hann
        window_name = "hann"
        window = _make_window(window_name, size)

        output_window = StaticTypeOutputPort(
            "window", [PortValueType(DataType.Float32, (size,))]
        )

        self._size = size
        self._window_name = window_name
        self._window = window
        self._output_window = output_window

        self.outputs[output_window.name] = output_window

        self.properties["size"] = size
        self.properties["window"] = window_name

        output_window.dispatch([window[np.newaxis, :]])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        window_name = self._window_name
        if "window" in properties:
            window_name = str(properties["window"])

        size = self._size
        if "size" in properties:
            size = int(properties["size"])

        new_output_window = self._output_window
        if size != self._size:
            new_output_window = StaticTypeOutputPort(
                "window",
                [PortValueType(DataType.Float32, (size,))],
            )

        new_window = None
        if window_name != self._window_name or size != self._size:
            new_window = _make_window(window_name, size)

        if new_output_window != self._output_window:
            replace_node_output_port(self, self._output_window, new_output_window)
            self._output_window = new_output_window

        if window_name != self._window_name or size != self._size:
            window = _make_window(window_name, size)

            self._window = window

        self._window_name = window_name
        self._size = size
        self._window = new_window if new_window is not None else self._window

        self.properties["size"] = size
        self.properties["window"] = window_name

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

        if new_window is not None:
            self._output_window.dispatch([new_window[np.newaxis, :]])

        if self.parent_graph is not None and (new_window is not None):
            self.parent_graph.flush_outputs()


# class RealVecWindowApplyNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealVecWindowApply")

#         input_vector = StaticTypePort(
#             "vector", PortDirection.INPUT, [DataType.Float32Vec]
#         )
#         input_vector.subscribe(id(self), self._on_input_vector)

#         input_window = StaticTypePort(
#             "window", PortDirection.INPUT, [DataType.Float32Vec]
#         )

#         output_vector = StaticTypePort(
#             "vector", PortDirection.OUTPUT, [DataType.Float32Vec]
#         )

#         self._output_vector = output_vector
#         self._input_vector = input_vector
#         self._input_window = input_window

#         self.inputs[input_vector.name] = input_vector
#         self.inputs[input_window.name] = input_window
#         self.outputs[output_vector.name] = output_vector

#     def _on_input_vector(self, values_any: list[Any]):
#         vector_array: np.ndarray = values_any[0]

#         if self._input_window.current_values is None:
#             logger.warning("Window is not set.")
#             return

#         window_array: np.ndarray = self._input_window.current_values[0]

#         try:
#             out = vector_array * window_array
#             # print(f"{out=}")
#         except Exception as e:
#             logger.warning(f"Error: {e}")
#             return

#         self._output_vector.dispatch([out])

#         # if vectors.shape[1] != self._window.size:
#         #     self._window = getattr(scipy.signal.windows, self._window_name)(
#         #         vectors.shape[1]
#         #     )

#         # out = vectors * self._window

#         # self._output_vector.dispatch([out])


# # class InversePinkWindowNode(BaseNode):
# #     def __init__(self, name: str):
# #         super().__init__(name, "InversePinkWindow")

# #         input_freqs = StaticTypePort(
# #             "freqs", PortDirection.INPUT, [DataType.Float32Vec]
# #         )
# #         input_freqs.subscribe(id(self), self._on_input_freqs)

# #         output_window = StaticTypePort(
# #             "window", PortDirection.OUTPUT, [DataType.Float32Vec]
# #         )

# #         self._output_window = output_window
# #         self._input_freqs = input_freqs

# #         self.inputs[input_freqs.name] = input_freqs
# #         self.outputs[output_window.name] = output_window

# #     def _on_input_freqs(self, values_any: list[Any]):
# #         freqs_array: np.ndarray = values_any[0]

# #         window = 1 / freqs_array
# #         print(f"{window=}")

# #         # self._output_window.dispatch([window])


# class RampUpWindowNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RampUpWindow")

#         input_size = StaticTypePort("size", PortDirection.INPUT, [DataType.Int32])
#         input_size.subscribe(id(self), self._on_input_size)

#         output_window = StaticTypePort(
#             "window", PortDirection.OUTPUT, [DataType.Float32Vec]
#         )

#         self._start = 0.0
#         self._stop = 1.0

#         self._output_window = output_window
#         self._input_size = input_size

#         self.inputs[input_size.name] = input_size
#         self.outputs[output_window.name] = output_window

#         self.properties["start"] = self._start
#         self.properties["stop"] = self._stop

#         self.set_properties_input(
#             ["start", "stop"],
#             [DataType.Float32, DataType.Float32],
#         )

#     def set_properties(self, properties: dict[str, PropertyDataType]):
#         start = self._start
#         stop = self._stop

#         if "start" in properties:
#             start = float(properties["start"])
#         if "stop" in properties:
#             stop = float(properties["stop"])

#         self._start = start
#         self._stop = stop

#         self.properties["start"] = start
#         self.properties["stop"] = stop

#         if self.parent_graph is not None:
#             self.parent_graph.notify_properties_changed(self)

#     def _on_input_size(self, values_any: list[Any]):
#         size_array: np.ndarray = values_any[0]

#         for size in size_array:
#             window = np.linspace(self._start, self._stop, size)
#             self._output_window.dispatch([window])
