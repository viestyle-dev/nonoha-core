from nonoha_core.node_registry import NodeRegistry
from nonoha_core.node import BaseNode


def test_node_registry_register():
    registry = NodeRegistry()

    class TestNode(BaseNode):
        def __init__(self, name: str):
            super().__init__(name, "Test")

    registry.register_node("Test", TestNode)

    # Registering a duplicate type name must raise
    try:
        registry.register_node("Test", TestNode)
    except ValueError as e:
        assert str(e) == "Node type Test already registered"
    else:
        assert False, "Expected ValueError not raised"

    node = registry.create_node("Test", "test_node")
    assert isinstance(node, TestNode)
