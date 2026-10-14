from nonoha_core.nodes.bit_wise_operation_nodes import PackbitsNode

import numpy as np
import pytest


def test_packbits_default():
    """Default: u8[8], axis=1 -> u8[1], pack 8 bits into 1 byte"""
    node = PackbitsNode("test")

    assert node.inputs["in"].value_type_list[0].name == "u8[8]"
    assert node.outputs["out"].value_type_list[0].name == "u8[1]"

    # 10101110 = 0xAE
    data = np.array([[1, 0, 1, 0, 1, 1, 1, 0]], dtype=np.uint8)
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    assert out[0].shape == (1, 1)
    assert out[0][0, 0] == 0xAE


def test_packbits_non_multiple():
    """Non-multiple of 8: u8[10] -> u8[2], zero-padded"""
    node = PackbitsNode("test")
    node.set_properties({"in_type": "u8[10]"})

    assert node.outputs["out"].value_type_list[0].name == "u8[2]"

    # 10 bits: [1]*10 -> 0xFF, 0xC0 (padded with 6 zeros)
    data = np.ones((1, 10), dtype=np.uint8)
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    assert out[0].shape == (1, 2)
    assert out[0][0, 0] == 0xFF
    assert out[0][0, 1] == 0xC0


def test_packbits_multidim():
    """Multidim: u8[2x8], axis=2 -> u8[2x1]"""
    node = PackbitsNode("test")
    node.set_properties({"in_type": "u8[2x8]", "axis": 2})

    assert node.inputs["in"].value_type_list[0].name == "u8[2x8]"
    assert node.outputs["out"].value_type_list[0].name == "u8[2x1]"

    data = np.zeros((1, 2, 8), dtype=np.uint8)
    data[0, 0] = [1, 0, 1, 0, 1, 0, 1, 0]  # 0xAA
    data[0, 1] = [1, 1, 1, 1, 0, 0, 0, 0]  # 0xF0
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    assert out[0].shape == (1, 2, 1)
    assert out[0][0, 0, 0] == 0xAA
    assert out[0][0, 1, 0] == 0xF0


def test_packbits_bitorder_little():
    """bitorder='little' reverses bit order within each byte"""
    node = PackbitsNode("test")
    node.set_properties({"bitorder": "little"})

    # [1, 0, 1, 0, 1, 1, 1, 0] big=0xAE, little=0x75
    data = np.array([[1, 0, 1, 0, 1, 1, 1, 0]], dtype=np.uint8)
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    assert out[0][0, 0] == 0x75


def test_packbits_set_properties_changes_ports():
    """set_properties updates input/output port types"""
    node = PackbitsNode("test")
    assert node.inputs["in"].value_type_list[0].name == "u8[8]"
    assert node.outputs["out"].value_type_list[0].name == "u8[1]"

    node.set_properties({"in_type": "u8[16]"})
    assert node.inputs["in"].value_type_list[0].name == "u8[16]"
    assert node.outputs["out"].value_type_list[0].name == "u8[2]"


def test_packbits_bool_input():
    """Bool input: bool[8] -> u8[1]"""
    node = PackbitsNode("test")
    node.set_properties({"in_type": "bool[8]"})

    assert node.inputs["in"].value_type_list[0].name == "bool[8]"
    assert node.outputs["out"].value_type_list[0].name == "u8[1]"

    data = np.array([[True, False, True, False, True, True, True, False]])
    node.inputs["in"].dispatch([data])

    out = node.outputs["out"].current_values
    assert out is not None
    assert out[0][0, 0] == 0xAE


def test_packbits_invalid_dtype():
    """Non u8/bool dtype raises ValueError"""
    node = PackbitsNode("test")
    with pytest.raises(ValueError, match="u8 or bool"):
        node.set_properties({"in_type": "f32[8]"})
