"""Every built-in node declares its properties, and each property port sets its property."""

from nonoha_core._testing import (
    assert_all_properties_declared,
    assert_property_ports_apply,
)
from nonoha_core.node_registry import NodeRegistry
from nonoha_core.nodes import register_nodes


def _registry() -> NodeRegistry:
    registry = NodeRegistry()
    register_nodes(registry)
    return registry


def test_all_properties_are_declared():
    assert_all_properties_declared(_registry())


def test_property_ports_apply():
    assert_property_ports_apply(_registry())
