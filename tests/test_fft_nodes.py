import time

import numpy as np
from scipy.fft import dct as scipy_dct

from nonoha_core.nodes.fft_nodes import StftNode, IstftNode, _dct2, _dct2_tables


def test_istft_node():
    node = IstftNode("test")

    node.set_properties({
        "win_size": 512,
        "in_shape": "[257]"
    })


def test_stft_istft_roundtrip():
    """STFT -> ISTFT roundtrip: verify waveform reconstruction with rectangular window."""
    win_size = 16
    hop = 4
    fs = 32

    stft = StftNode("stft")
    stft.set_properties({"win_size": win_size, "hop": hop, "fs": fs})

    istft = IstftNode("istft")
    istft.set_properties({
        "win_size": win_size,
        "hop": hop,
        "fs": fs,
        "in_shape": f"[{win_size // 2 + 1}]",
    })

    # Subscribe AFTER set_properties (ports are replaced when params change)
    fft_outputs: list = []
    stft.outputs["fft"].subscribe(999, lambda v: fft_outputs.append(v))

    series_outputs: list = []
    istft.outputs["series"].subscribe(999, lambda v: series_outputs.append(v))

    # Generate test signal: sine wave
    t = np.arange(256, dtype=np.float32) / fs
    signal = np.sin(2 * np.pi * 4 * t).astype(np.float32)

    # Feed through STFT
    stft.inputs["series"].dispatch([signal])
    assert len(fft_outputs) > 0

    # Feed STFT output through ISTFT
    for fft_out in fft_outputs:
        istft.inputs["fft"].dispatch(fft_out)

    assert len(series_outputs) > 0

    # Concatenate ISTFT outputs
    reconstructed = np.concatenate([s[0] for s in series_outputs])

    # Skip first win_size samples (warmup: incomplete overlap region).
    # For rectangular window, full overlap starts at position win_size - hop,
    # but skip a full win_size to be safe.
    n_skip = win_size
    n_compare = len(reconstructed) - n_skip
    assert n_compare > 0

    np.testing.assert_allclose(
        reconstructed[n_skip:n_skip + n_compare],
        signal[n_skip:n_skip + n_compare],
        atol=1e-5,
    )


def test_stft_istft_roundtrip_hann():
    """STFT -> ISTFT roundtrip with Hann window."""
    win_size = 64
    hop = 16
    fs = 256

    stft = StftNode("stft")
    stft.set_properties({"win_size": win_size, "hop": hop, "fs": fs})

    istft = IstftNode("istft")
    istft.set_properties({
        "win_size": win_size,
        "hop": hop,
        "fs": fs,
        "in_shape": f"[{win_size // 2 + 1}]",
    })

    # Subscribe after set_properties
    fft_outputs: list = []
    stft.outputs["fft"].subscribe(999, lambda v: fft_outputs.append(v))

    series_outputs: list = []
    istft.outputs["series"].subscribe(999, lambda v: series_outputs.append(v))

    # Set Hann window on both nodes
    hann = np.hanning(win_size).astype(np.float32)
    stft.inputs["window"].dispatch([hann[np.newaxis, :]])
    istft.inputs["window"].dispatch([hann[np.newaxis, :]])

    # Generate test signal
    t = np.arange(1024, dtype=np.float32) / fs
    signal = np.sin(2 * np.pi * 10 * t).astype(np.float32)

    # Feed through STFT -> ISTFT
    stft.inputs["series"].dispatch([signal])
    for fft_out in fft_outputs:
        istft.inputs["fft"].dispatch(fft_out)

    assert len(series_outputs) > 0
    reconstructed = np.concatenate([s[0] for s in series_outputs])

    # Skip warmup region
    n_skip = win_size
    n_compare = len(reconstructed) - n_skip
    assert n_compare > 0

    np.testing.assert_allclose(
        reconstructed[n_skip:n_skip + n_compare],
        signal[n_skip:n_skip + n_compare],
        atol=1e-5,
    )


def test_stft_multidim_input():
    """StftNode with multi-dimensional in_shape (e.g. 3-channel) runs without error."""
    win_size = 16
    hop = 4

    node = StftNode("test")
    node.set_properties({"win_size": win_size, "hop": hop, "in_shape": "[3]"})

    fft_outputs: list = []
    node.outputs["fft"].subscribe(999, lambda v: fft_outputs.append(v))

    # Feed 3-channel data: (batch=32, channels=3)
    data = np.random.randn(32, 3).astype(np.float32)
    node.inputs["series"].dispatch([data])

    assert len(fft_outputs) > 0
    # Output shape: (num_windows, fft_size, 3)
    fft_result = fft_outputs[0][0]
    assert fft_result.ndim == 3
    assert fft_result.shape[1] == win_size // 2 + 1
    assert fft_result.shape[2] == 3


def test_istft_multidim_input():
    """IstftNode with multi-dimensional in_shape runs without error."""
    win_size = 16
    hop = 4
    fft_size = win_size // 2 + 1

    node = IstftNode("test")
    node.set_properties({
        "win_size": win_size,
        "hop": hop,
        "in_shape": f"[{fft_size}x3]",
    })

    series_outputs: list = []
    node.outputs["series"].subscribe(999, lambda v: series_outputs.append(v))

    # Feed multi-dimensional FFT data: (n_frames, fft_size, 3)
    n_frames = 20
    data = np.random.randn(n_frames, fft_size, 3).astype(np.complex64)
    node.inputs["fft"].dispatch([data])

    assert len(series_outputs) > 0
    # Output shape: (reconstructed_samples, 3)
    series_result = series_outputs[0][0]
    assert series_result.ndim == 2
    assert series_result.shape[1] == 3


def test_stft_multidim_roundtrip():
    """STFT -> ISTFT roundtrip with multi-dimensional (3-channel) input."""
    win_size = 16
    hop = 4
    fs = 32

    stft = StftNode("stft")
    stft.set_properties({
        "win_size": win_size, "hop": hop, "fs": fs,
        "in_shape": "[3]",
    })

    istft = IstftNode("istft")
    istft.set_properties({
        "win_size": win_size, "hop": hop, "fs": fs,
        "in_shape": f"[{win_size // 2 + 1}x3]",
    })

    fft_outputs: list = []
    stft.outputs["fft"].subscribe(999, lambda v: fft_outputs.append(v))

    series_outputs: list = []
    istft.outputs["series"].subscribe(999, lambda v: series_outputs.append(v))

    # 3-channel signal: (256 samples, 3 channels)
    t = np.arange(256, dtype=np.float32) / fs
    signal = np.stack([
        np.sin(2 * np.pi * 2 * t),
        np.sin(2 * np.pi * 4 * t),
        np.sin(2 * np.pi * 6 * t),
    ], axis=-1).astype(np.float32)

    stft.inputs["series"].dispatch([signal])
    for fft_out in fft_outputs:
        istft.inputs["fft"].dispatch(fft_out)

    assert len(series_outputs) > 0
    reconstructed = np.concatenate([s[0] for s in series_outputs])

    n_skip = win_size
    n_compare = len(reconstructed) - n_skip
    assert n_compare > 0

    np.testing.assert_allclose(
        reconstructed[n_skip:n_skip + n_compare],
        signal[n_skip:n_skip + n_compare],
        atol=1e-5,
    )


def test_stft_dynamic_property_change():
    """StftNode: dynamic property changes (especially shape) without error."""
    node = StftNode("test")

    # 1. Scalar input, win_size=16
    node.set_properties({"win_size": 16, "hop": 4})
    outputs1: list = []
    node.outputs["fft"].subscribe(901, lambda v: outputs1.append(v))

    data = np.random.randn(64).astype(np.float32)
    node.inputs["series"].dispatch([data])
    assert len(outputs1) > 0

    # 2. Change win_size to 8, hop to 2
    node.set_properties({"win_size": 8, "hop": 2})
    outputs2: list = []
    node.outputs["fft"].subscribe(902, lambda v: outputs2.append(v))

    data = np.random.randn(32).astype(np.float32)
    node.inputs["series"].dispatch([data])
    assert len(outputs2) > 0

    # 3. Change to multi-dimensional input (buffer auto-cleared by set_properties)
    node.set_properties({"win_size": 8, "hop": 2, "in_shape": "[2]"})
    outputs3: list = []
    node.outputs["fft"].subscribe(903, lambda v: outputs3.append(v))

    data = np.random.randn(16, 2).astype(np.float32)
    node.inputs["series"].dispatch([data])
    assert len(outputs3) > 0

    # 4. Change back to scalar with different params (buffer auto-cleared)
    node.set_properties({"win_size": 32, "hop": 8, "in_shape": ""})
    outputs4: list = []
    node.outputs["fft"].subscribe(904, lambda v: outputs4.append(v))

    data = np.random.randn(128).astype(np.float32)
    node.inputs["series"].dispatch([data])
    assert len(outputs4) > 0


def test_stft_in_shape_change_auto_clears_buffer():
    """StftNode: changing in_shape auto-clears buffer without manual reset."""
    node = StftNode("test")
    node.set_properties({"win_size": 8, "hop": 2})

    outputs_scalar: list = []
    node.outputs["fft"].subscribe(901, lambda v: outputs_scalar.append(v))

    # Feed scalar data — leaves residual buffer
    data1 = np.arange(16, dtype=np.float32)
    node.inputs["series"].dispatch([data1])
    assert len(outputs_scalar) > 0
    assert node._buffer is not None
    assert node._buffer.ndim == 1  # 1D residual

    # Change in_shape to [2] without manual reset
    node.set_properties({"win_size": 8, "hop": 2, "in_shape": "[2]"})
    assert node._buffer is None  # auto-cleared

    outputs_2ch: list = []
    node.outputs["fft"].subscribe(902, lambda v: outputs_2ch.append(v))

    data2 = np.ones((16, 2), dtype=np.float32)
    node.inputs["series"].dispatch([data2])
    assert len(outputs_2ch) > 0


def test_istft_dynamic_property_change():
    """IstftNode: dynamic property changes (especially shape) without error."""
    node = IstftNode("test")

    # 1. Initial: win_size=16
    win_size = 16
    fft_size = win_size // 2 + 1
    node.set_properties({
        "win_size": win_size, "hop": 4,
        "in_shape": f"[{fft_size}]",
    })
    outputs1: list = []
    node.outputs["series"].subscribe(901, lambda v: outputs1.append(v))

    data = np.random.randn(20, fft_size).astype(np.complex64)
    node.inputs["fft"].dispatch([data])
    assert len(outputs1) > 0

    # 2. Change win_size=8, hop=2
    win_size = 8
    fft_size = win_size // 2 + 1
    node.set_properties({
        "win_size": win_size, "hop": 2,
        "in_shape": f"[{fft_size}]",
    })
    outputs2: list = []
    node.outputs["series"].subscribe(902, lambda v: outputs2.append(v))

    data = np.random.randn(20, fft_size).astype(np.complex64)
    node.inputs["fft"].dispatch([data])
    assert len(outputs2) > 0

    # 3. Change to multi-dimensional (buffer auto-cleared by set_properties)
    win_size = 8
    fft_size = win_size // 2 + 1
    node.set_properties({
        "win_size": win_size, "hop": 2,
        "in_shape": f"[{fft_size}x3]",
    })
    outputs3: list = []
    node.outputs["series"].subscribe(903, lambda v: outputs3.append(v))

    data = np.random.randn(20, fft_size, 3).astype(np.complex64)
    node.inputs["fft"].dispatch([data])
    assert len(outputs3) > 0

    # 4. Change back to 1D with different size (buffer auto-cleared)
    win_size = 32
    fft_size = win_size // 2 + 1
    node.set_properties({
        "win_size": win_size, "hop": 8,
        "in_shape": f"[{fft_size}]",
    })
    outputs4: list = []
    node.outputs["series"].subscribe(904, lambda v: outputs4.append(v))

    data = np.random.randn(20, fft_size).astype(np.complex64)
    node.inputs["fft"].dispatch([data])
    assert len(outputs4) > 0


# --- _dct2 tests ---


def test_dct2_1d_no_norm():
    """_dct2 matches scipy.fft.dct for 1D input without normalization."""
    x = np.random.randn(32).astype(np.float64)
    expected = scipy_dct(x, type=2)
    result = _dct2(x)
    np.testing.assert_allclose(result, expected, atol=1e-10)


def test_dct2_1d_ortho():
    """_dct2 matches scipy.fft.dct for 1D input with ortho normalization."""
    x = np.random.randn(32).astype(np.float64)
    expected = scipy_dct(x, type=2, norm="ortho")
    result = _dct2(x, norm="ortho")
    np.testing.assert_allclose(result, expected, atol=1e-10)


def test_dct2_2d_axis0():
    """_dct2 matches scipy.fft.dct along axis=0."""
    x = np.random.randn(16, 8).astype(np.float64)
    expected = scipy_dct(x, type=2, axis=0, norm="ortho")
    result = _dct2(x, axis=0, norm="ortho")
    np.testing.assert_allclose(result, expected, atol=1e-10)


def test_dct2_2d_axis1():
    """_dct2 matches scipy.fft.dct along axis=1 (MfccNode usage pattern)."""
    x = np.random.randn(8, 40).astype(np.float64)
    expected = scipy_dct(x, type=2, axis=1, norm="ortho")
    result = _dct2(x, axis=1, norm="ortho")
    np.testing.assert_allclose(result, expected, atol=1e-10)


def test_dct2_3d():
    """_dct2 matches scipy.fft.dct for 3D input (batch, n_mels, channels)."""
    x = np.random.randn(4, 40, 3).astype(np.float64)
    expected = scipy_dct(x, type=2, axis=1, norm="ortho")
    result = _dct2(x, axis=1, norm="ortho")
    np.testing.assert_allclose(result, expected, atol=1e-10)


def test_dct2_float32():
    """_dct2 works with float32 input (typical MfccNode data type)."""
    x = np.random.randn(8, 40).astype(np.float32)
    expected = np.asarray(scipy_dct(x, type=2, axis=1, norm="ortho"))
    result = _dct2(x, axis=1, norm="ortho")
    np.testing.assert_allclose(result, expected, atol=1e-5)


def test_dct2_odd_length():
    """_dct2 matches scipy.fft.dct for odd-length input."""
    x = np.random.randn(17).astype(np.float64)
    expected = scipy_dct(x, type=2, norm="ortho")
    result = _dct2(x, norm="ortho")
    np.testing.assert_allclose(result, expected, atol=1e-10)


def test_dct2_benchmark():
    """_dct2 vs scipy.fft.dct performance comparison."""
    cases = [
        ("1D (N=32)",           np.random.randn(32),              {"axis": -1}),
        ("1D (N=128)",          np.random.randn(128),             {"axis": -1}),
        ("2D (8x40) axis=1",   np.random.randn(8, 40),           {"axis": 1}),
        ("2D (8x40) f32",      np.random.randn(8, 40).astype(np.float32), {"axis": 1}),
        ("3D (4x40x3) axis=1", np.random.randn(4, 40, 3),        {"axis": 1}),
        ("3D (16x128x3)",      np.random.randn(16, 128, 3),      {"axis": 1}),
        ("2D (64x256)",        np.random.randn(64, 256),          {"axis": 1}),
    ]

    iterations = 1000
    runs = 5

    def measure(fn, x, iters, **kwargs):
        for _ in range(10):  # warmup
            fn(x, **kwargs)
        times = []
        for _ in range(runs):
            start = time.perf_counter()
            for _ in range(iters):
                fn(x, **kwargs)
            times.append((time.perf_counter() - start) / iters * 1e6)
        return sorted(times)[runs // 2]  # median

    print()
    print("=" * 80)
    print("_dct2 vs scipy.fft.dct  Benchmark")
    print("=" * 80)
    print(f"{'Case':<25} {'scipy (us)':>10} {'_dct2 (us)':>10} {'+ tables':>10} {'ratio':>7} {'t.ratio':>7}")
    print("-" * 80)

    for name, x, kwargs in cases:
        axis = kwargs["axis"]
        N = x.shape[axis]
        tables = _dct2_tables(N, x.ndim, axis)

        scipy_kwargs = {"type": 2, "norm": "ortho", **kwargs}
        t_scipy = measure(
            lambda x, **kw: scipy_dct(x, **kw), x, iterations, **scipy_kwargs
        )
        t_dct2 = measure(_dct2, x, iterations, norm="ortho", **kwargs)
        t_tables = measure(_dct2, x, iterations, norm="ortho", tables=tables, **kwargs)
        ratio = t_dct2 / t_scipy
        t_ratio = t_tables / t_scipy
        print(f"{name:<25} {t_scipy:>8.1f}   {t_dct2:>8.1f}   {t_tables:>8.1f}   {ratio:>5.2f}x  {t_ratio:>5.2f}x")

    print()
    print("ratio > 1 = slower than scipy, < 1 = faster")
