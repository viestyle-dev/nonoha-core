"""Sample frames: the same bytes as the reference encoding for every value
that fitted, and the reductions that replaced truncation."""

import itertools

import numpy as np
import pytest

from inspection_reference import FLAG_TRUNCATED, reference_frame, reference_reduce
from nonoha_core.inspection import ReduceSpec, encode_sample, reduce_values

rng = np.random.default_rng(7)

NUMERIC = [np.bool_, np.int8, np.uint8, np.int16, np.uint16, np.int32, np.uint32, np.int64, np.uint64, np.float32, np.float64]


def numeric(dtype, shape):
    if dtype is np.bool_:
        return rng.random(shape) > 0.5
    if np.issubdtype(dtype, np.integer):
        info = np.iinfo(dtype)
        return rng.integers(max(info.min, -1000), min(info.max, 1000), shape, endpoint=True).astype(dtype)
    return rng.standard_normal(shape).astype(dtype)


def cases():
    shapes = [(1,), (5,), (1, 3), (4, 3), (2, 3, 4), (1, 6, 5, 3), ()]
    for dtype, shape in itertools.product(NUMERIC, shapes):
        yield f"{np.dtype(dtype).name}{shape}", [numeric(dtype, shape)], {}
    base = numeric(np.float32, (3, 40, 30))
    yield "non-contiguous transposed", [base.transpose(0, 2, 1)], {}
    yield "non-contiguous strided", [base[:, ::3, 1::2]], {}
    yield "big-endian input", [base.astype(">f4")], {}
    yield "batch all", [base], {"batch": "all"}
    yield "batch 2", [base], {"batch": 2}
    yield "slice", [base], {"batch": "all", "slices": [[5, 25, 2], None]}
    yield "slice beyond rank", [base], {"slices": [None, [0, 10], [1, 2]]}
    yield "cast f32", [numeric(np.float64, (2, 7))], {"batch": "all", "cast": "f32"}
    yield "cast f64 of ints", [numeric(np.int16, (2, 7))], {"batch": "all", "cast": "f64"}
    yield "cast f32 leaves bool", [numeric(np.bool_, (1, 7))], {"cast": "f32"}
    c64 = (rng.standard_normal((1, 20, 30)) + 1j * rng.standard_normal((1, 20, 30))).astype(np.complex64)
    yield "complex64", [c64], {}
    yield "complex128", [c64.astype(np.complex128)], {}
    yield "complex cast f64", [c64], {"cast": "f64"}
    yield "complex strided", [c64], {"auto_stride": [0, 1], "max_bytes": 600}
    image = rng.integers(0, 255, (1, 1080, 1920, 3), dtype=np.uint8)
    yield "image strided", [image], {"auto_stride": [0, 1]}
    yield "image strided 1M", [image], {"batch": "all", "auto_stride": [0, 1], "max_bytes": 1 << 20}
    yield "f32 frame strided", [rng.random((1, 720, 1280), dtype=np.float32)], {"auto_stride": [0, 1]}
    yield "vector strided", [rng.random((1, 100_000), dtype=np.float32)], {"auto_stride": [0]}
    yield "two slots fitting", [numeric(np.float32, (2, 3)), numeric(np.int32, (2,))], {"batch": "all"}
    yield "strings", [np.array(["a", "日本語", ""])], {"batch": "all"}
    yield "string 0-d", [np.array("hello")], {}
    yield "audio block", [rng.random((512, 2), dtype=np.float32)], {"batch": "all", "auto_stride": [0, 1], "max_bytes": 1 << 20}


CASES = list(cases())


@pytest.mark.parametrize("name,values,kw", CASES, ids=[c[0] for c in CASES])
def test_the_same_bytes_as_before_for_values_that_fitted(name, values, kw):
    ref_values, ref_types, ref_steps, ref_flags = reference_reduce(values, **kw)
    assert not ref_flags & FLAG_TRUNCATED, "a case that fitted before"
    spec = ReduceSpec(**kw)
    reduced = reduce_values(values, spec)
    frame = encode_sample(3, 11, 7, 42, 1.25, reduced)
    assert bytes(frame) == reference_frame(3, 11, 7, 42, 1.25, ref_values, ref_types, ref_steps, ref_flags)


# --- what fitting changed: the total decides, items first, then one stride ---------------

from nonoha_core.inspection.reduce import FLAG_REDUCED  # noqa: E402


def test_two_slots_are_fitted_together_instead_of_dropped():
    # each fits alone, together they did not: they were dropped before
    values = [np.zeros((1, 60000), np.uint8), np.zeros((1, 40000), np.uint8)]
    r = reduce_values(values, ReduceSpec(auto_stride=[0], max_bytes=64 * 1024))
    assert r.values is not None and r.nbytes <= 64 * 1024
    assert [a.shape for a in r.values] == [(1, 30000), (1, 20000)] and r.steps == [(2,), (2,)]
    assert r.flags & FLAG_REDUCED
    # a dimension over 65535 needs a larger step even when the bytes fit
    long = [np.zeros((1, 204800), np.uint8)]
    assert reduce_values(long, ReduceSpec(auto_stride=[0], max_bytes=1 << 20)).steps == [(4,)]


def test_rounding_up_is_counted():
    r = reduce_values([np.zeros((1, 1023, 1025), np.uint8)], ReduceSpec(auto_stride=[0, 1], max_bytes=256 * 1024))
    assert r.values is not None and r.values[0].nbytes <= 256 * 1024 and r.steps == [(3, 3)]


def test_too_many_items_keep_the_newest_and_every_channel():
    block = np.arange(48000 * 8, dtype=np.float32).reshape(48000, 8)
    r = reduce_values([block], ReduceSpec(batch="all", auto_stride=[0, 1], max_bytes=1 << 20))
    kept = r.values[0]
    assert kept.shape == (32768, 8) and r.steps == [(1,)]  # no channel strided away
    assert np.array_equal(kept, block[-32768:]) and r.flags & FLAG_REDUCED


def test_a_dimension_a_frame_cannot_hold_is_strided_or_reported():
    wide = np.zeros((1, 131072), np.float32)
    r = reduce_values([wide], ReduceSpec(auto_stride=[0], max_bytes=1 << 20))
    assert r.values[0].shape == (1, 43691) and r.steps == [(3,)]  # 131072 / 2 = 65536 is one too many
    r = reduce_values([wide], ReduceSpec(max_bytes=1 << 20))
    assert r.values is None and "65535" in r.too_large


def test_too_large_is_reported_without_copying():
    import tracemalloc

    big = np.zeros((1, 5000), np.float32)
    tracemalloc.start()
    r = reduce_values([big], ReduceSpec(max_bytes=1024))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert r.values is None and r.nbytes == 20000
    assert r.too_large == "f32[1x5000]: 20000 bytes, more than max_bytes 1024 even reduced"
    assert peak < 4096  # no copy of the 20 KB value


def test_a_sample_is_one_copy_of_the_reduced_size_in_wire_order():
    import tracemalloc

    frame = np.ones((1, 720, 1280), np.float32)
    spec = ReduceSpec(auto_stride=[0, 1], max_bytes=256 * 1024)
    tracemalloc.start()
    r = reduce_values([frame], spec)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert r.values[0].dtype == np.dtype(">f4") and r.values[0].flags["C_CONTIGUOUS"]
    assert peak < r.values[0].nbytes + 4096
    assert not np.shares_memory(r.values[0], frame)


def test_owned_values_are_not_copied():
    rows = np.ones((6, 4), np.float32)
    r = reduce_values([rows], ReduceSpec(batch="all"), owned=True)
    assert np.shares_memory(r.values[0], rows)
    r = reduce_values([rows], ReduceSpec(batch="all", cast="f64"), owned=True)
    assert r.values[0].dtype == np.dtype(">f8")  # a cast is still a conversion
