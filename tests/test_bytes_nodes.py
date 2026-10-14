import sys

import numpy as np

from nonoha_core.nodes.bytes_nodes import (
    BytesInplaceInsertNode,
    ToBytesNode,
    ToBytesStringNode,
)


def test_bytes_inplace_insert_node():
    node = BytesInplaceInsertNode("test")

    node.set_properties(
        {
            "length": 16,
            "offset": 4,
            "insert_length": 4,
        }
    )

    input_in = node.inputs["in"]
    output_bytes = node.outputs["bytes"]

    test_bytes = np.array(
        [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]], dtype=np.uint8
    )

    input_in.dispatch(
        [
            test_bytes,
            np.array([[100, 101, 102, 103]], dtype=np.uint8),
        ]
    )

    assert output_bytes.current_values is not None
    result = output_bytes.current_values[0]
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.uint8
    assert result.shape == (1, 16)
    assert result is test_bytes  # Inplace update
    assert np.array_equal(
        result,
        np.array(
            [[0, 1, 2, 3, 100, 101, 102, 103, 8, 9, 10, 11, 12, 13, 14, 15]],
            dtype=np.uint8,
        ),
    )

    # ---

    input_in.dispatch(
        [
            np.array(
                [
                    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
                ],
                dtype=np.uint8,
            ),
            np.array([[100, 101, 102, 103]], dtype=np.uint8),
        ]
    )

    assert output_bytes.current_values is not None
    result = output_bytes.current_values[0]
    assert result.shape == (2, 16)
    assert np.array_equal(
        result,
        np.array(
            [
                [0, 1, 2, 3, 100, 101, 102, 103, 8, 9, 10, 11, 12, 13, 14, 15],
                [10, 11, 12, 13, 100, 101, 102, 103, 18, 19, 20, 21, 22, 23, 24, 25],
            ],
            dtype=np.uint8,
        ),
    )

    # ---

    input_in.dispatch(
        [
            np.array(
                [
                    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
                ],
                dtype=np.uint8,
            ),
            np.array([[100, 101, 102, 103], [104, 105, 106, 107]], dtype=np.uint8),
        ]
    )

    assert output_bytes.current_values is not None
    result = output_bytes.current_values[0]
    assert result.shape == (2, 16)
    assert np.array_equal(
        result,
        np.array(
            [
                [0, 1, 2, 3, 100, 101, 102, 103, 8, 9, 10, 11, 12, 13, 14, 15],
                [10, 11, 12, 13, 104, 105, 106, 107, 18, 19, 20, 21, 22, 23, 24, 25],
            ],
            dtype=np.uint8,
        ),
    )


def test_to_bytes_node_big_endian():
    """Test ToBytesNode with big-endian output (default, network byte order)."""
    node = ToBytesNode("test")

    # Default: is_little_endian = False (big-endian)
    assert node.properties["is_little_endian"] is False

    input_in = node.inputs["in"]
    output_bytes = node.outputs["bytes"]

    # Test with float32 array: [1.0, 2.0, 3.0, 4.0]
    # IEEE 754 float32 big-endian:
    # 1.0 = 0x3F800000, 2.0 = 0x40000000, 3.0 = 0x40400000, 4.0 = 0x40800000
    test_input = np.array([[1.0, 2.0, 3.0, 4.0]], dtype=np.float32)
    input_in.dispatch([test_input])

    assert output_bytes.current_values is not None
    result = output_bytes.current_values[0]

    assert result.dtype == np.uint8
    assert result.shape == (1, 16)  # 4 floats * 4 bytes

    # Verify big-endian byte order
    expected_big_endian = np.array(
        [
            [
                0x3F, 0x80, 0x00, 0x00,  # 1.0
                0x40, 0x00, 0x00, 0x00,  # 2.0
                0x40, 0x40, 0x00, 0x00,  # 3.0
                0x40, 0x80, 0x00, 0x00,  # 4.0
            ]
        ],
        dtype=np.uint8,
    )
    assert np.array_equal(result, expected_big_endian)


def test_to_bytes_node_little_endian():
    """Test ToBytesNode with little-endian output."""
    node = ToBytesNode("test")
    node.set_properties({"is_little_endian": True})

    assert node.properties["is_little_endian"] is True

    input_in = node.inputs["in"]
    output_bytes = node.outputs["bytes"]

    # Test with float32 array
    test_input = np.array([[1.0, 2.0, 3.0, 4.0]], dtype=np.float32)
    input_in.dispatch([test_input])

    assert output_bytes.current_values is not None
    result = output_bytes.current_values[0]

    # Verify little-endian byte order
    expected_little_endian = np.array(
        [
            [
                0x00, 0x00, 0x80, 0x3F,  # 1.0
                0x00, 0x00, 0x00, 0x40,  # 2.0
                0x00, 0x00, 0x40, 0x40,  # 3.0
                0x00, 0x00, 0x80, 0x40,  # 4.0
            ]
        ],
        dtype=np.uint8,
    )
    assert np.array_equal(result, expected_little_endian)


def test_to_bytes_node_batch():
    """Test ToBytesNode with batched input."""
    node = ToBytesNode("test")

    input_in = node.inputs["in"]
    output_bytes = node.outputs["bytes"]

    # Batch of 2
    test_input = np.array(
        [
            [1.0, 2.0, 3.0, 4.0],
            [5.0, 6.0, 7.0, 8.0],
        ],
        dtype=np.float32,
    )
    input_in.dispatch([test_input])

    assert output_bytes.current_values is not None
    result = output_bytes.current_values[0]

    assert result.shape == (2, 16)  # 2 batches * 4 floats * 4 bytes


def test_to_bytes_node_set_properties_in_type():
    """Test ToBytesNode in_type property change."""
    node = ToBytesNode("test")

    # Change to int16 with shape (8,)
    node.set_properties({"in_type": "i16[8]"})

    assert node.properties["in_type"] == "i16[8]"

    input_in = node.inputs["in"]
    output_bytes = node.outputs["bytes"]

    # int16[8] = 16 bytes output
    test_input = np.array([[1, 2, 3, 4, 5, 6, 7, 8]], dtype=np.int16)
    input_in.dispatch([test_input])

    assert output_bytes.current_values is not None
    result = output_bytes.current_values[0]

    assert result.shape == (1, 16)  # 8 int16 * 2 bytes


def test_to_bytes_string_node():
    """Test ToBytesStringNode with UTF-8 encoding."""
    node = ToBytesStringNode("test")

    input_in = node.inputs["in"]
    output_bytes = node.outputs["bytes"]

    # Test ASCII string (using StringDType)
    test_input = np.array(["Hello"], dtype=np.dtypes.StringDType)  # type: ignore
    input_in.dispatch([test_input])

    assert output_bytes.current_values is not None
    result = output_bytes.current_values[0]

    assert result.dtype == np.uint8
    assert result.shape == (1, 5)  # "Hello" = 5 bytes with batch dimension
    expected = np.array([[72, 101, 108, 108, 111]], dtype=np.uint8)  # H, e, l, l, o
    assert np.array_equal(result, expected)


def test_to_bytes_string_node_utf8():
    """Test ToBytesStringNode with multibyte UTF-8 characters."""
    node = ToBytesStringNode("test")

    input_in = node.inputs["in"]
    output_bytes = node.outputs["bytes"]

    # Test Japanese string (UTF-8 multibyte, using StringDType)
    test_input = np.array(["あ"], dtype=np.dtypes.StringDType)  # type: ignore
    input_in.dispatch([test_input])

    assert output_bytes.current_values is not None
    result = output_bytes.current_values[0]

    # "あ" in UTF-8 = 0xE3, 0x81, 0x82 (3 bytes) with batch dimension
    assert result.shape == (1, 3)
    expected = np.array([[0xE3, 0x81, 0x82]], dtype=np.uint8)
    assert np.array_equal(result, expected)


def test_to_bytes_string_node_batch():
    """Test ToBytesStringNode with batched strings - dispatches per string."""
    node = ToBytesStringNode("test")

    input_in = node.inputs["in"]
    output_bytes = node.outputs["bytes"]

    # Test batch of strings - each string dispatches separately
    test_input = np.array(["AB", "CDEF"], dtype=np.dtypes.StringDType)  # type: ignore
    input_in.dispatch([test_input])

    # After batch dispatch, current_values contains the LAST dispatched string
    assert output_bytes.current_values is not None
    result = output_bytes.current_values[0]

    # Last string "CDEF" = 4 bytes with batch dimension
    assert result.shape == (1, 4)
    expected = np.array([[67, 68, 69, 70]], dtype=np.uint8)  # C, D, E, F
    assert np.array_equal(result, expected)
