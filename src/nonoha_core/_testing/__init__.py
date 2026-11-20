"""nonoha-core pytest plugin: auto-validates dispatch shape consistency.

Registered via pytest11 entry point. Active in any environment where
nonoha-core is installed and pytest is run. No-op if pytest is not installed.

Module scope does NOT import pytest (follows numpy._pytesttester pattern).
"""


def _checked_dispatch(original, self, values):
    """Validate that dispatched values have correct batch + shape dimensions."""
    for i, (value, vtype) in enumerate(
        zip(values, self._value_type_list)
    ):
        if value is None:
            # None is only the "not yet received" sentinel inside
            # values_store; dispatching it as a value violates the
            # PortValue contract (PortValue = np.ndarray) and would
            # corrupt the input port's fill tracking.
            raise AssertionError(
                f"Port '{self._name}' value[{i}]: dispatched None. "
                f"PortValue must be an ndarray; None is reserved for "
                f"unfilled values_store slots."
            )
        if hasattr(value, "ndim"):
            actual_ndim = value.ndim - 1
            if actual_ndim != vtype.ndim:
                raise AssertionError(
                    f"Port '{self._name}' value[{i}]: "
                    f"shape mismatch: expected batch_dim + {vtype.ndim}D "
                    f"(e.g. (batch, {', '.join('?' for _ in range(vtype.ndim))})), "
                    f"got shape {value.shape}. "
                    f"Hint: add [np.newaxis] to prepend batch dimension."
                )
    return original(self, values)


def assert_all_ports_documented(node_registry):
    """Assert all non-property ports have descriptions via describe().

    Usage in plugin tests::

        from nonoha_core._testing import assert_all_ports_documented

        def test_all_ports_documented(node_registry_fixture):
            assert_all_ports_documented(node_registry_fixture)
    """
    errors = []
    for defn in node_registry.node_definitions.values():
        for port in defn.metadata.inputs:
            if not port.name.startswith("@"):
                if not port.description:
                    errors.append(f"{defn.type_name} input '{port.name}'")
        for port in defn.metadata.outputs:
            if not port.description:
                errors.append(f"{defn.type_name} output '{port.name}'")
    if errors:
        raise AssertionError(
            f"Undocumented ports ({len(errors)}):\n"
            + "\n".join(f"  - {e}" for e in errors)
        )


def assert_all_properties_declared(node_registry):
    """Assert every property of every registered node is declared in PROPERTIES.

    A declared property has a description, a data_type and its default_value,
    and so an input port (``@name``) that sets it.

    Usage in plugin tests::

        from nonoha_core._testing import assert_all_properties_declared

        def test_all_properties_declared(node_registry_fixture):
            assert_all_properties_declared(node_registry_fixture)
    """
    from nonoha_core.data_type import name_to_port_value_type

    errors = []
    for defn in node_registry.node_definitions.values():
        node = defn.factory(f"_check_{defn.type_name}")
        try:
            declared = type(node).PROPERTIES
            for key in node.properties.keys() - declared.keys():
                errors.append(f"{defn.type_name} property '{key}': not in PROPERTIES")
            for key, desc in declared.items():
                where = f"{defn.type_name} property '{key}'"
                if not desc.get("description"):
                    errors.append(f"{where}: no description")
                if "data_type" not in desc:
                    errors.append(f"{where}: no data_type")
                else:
                    try:
                        name_to_port_value_type(desc["data_type"])
                    except (KeyError, ValueError):
                        errors.append(f"{where}: unknown data_type {desc['data_type']!r}")
                    if node.PROPERTY_PORT_PREFIX + key not in node.inputs:
                        errors.append(f"{where}: no input port")
                if "default_value" not in desc:
                    errors.append(f"{where}: no default_value")
                elif node.properties.get(key) != desc["default_value"]:
                    errors.append(
                        f"{where}: starts as {node.properties.get(key)!r}, "
                        f"default_value is {desc['default_value']!r}"
                    )
        finally:
            node.finalize()
    if errors:
        raise AssertionError(
            f"Undeclared properties ({len(errors)}):\n"
            + "\n".join(f"  - {e}" for e in errors)
        )


def assert_property_ports_apply(node_registry, skip=()):
    """Assert each property accepts the value its input port hands over.

    A port delivers a numpy scalar, not a Python value. Each node must take
    its own default that way: without raising, keeping the property a plain
    int, float, bool or str (properties are saved as JSON), and keeping its
    property ports.

    ``skip``: node types whose properties cannot be applied in a test.
    """
    import numpy as np

    from nonoha_core.data_type import data_type_to_numpy_dtype

    errors = []
    for defn in node_registry.node_definitions.values():
        if defn.type_name in skip:
            continue
        node = defn.factory(f"_check_{defn.type_name}")
        try:
            prefix = node.PROPERTY_PORT_PREFIX
            ports = [name for name in node.inputs if name.startswith(prefix)]
            for name in ports:
                key = name[len(prefix):]
                where = f"{defn.type_name} property '{key}'"
                before = node.properties[key]
                dtype = data_type_to_numpy_dtype(node.inputs[name].value_type_list[0].data_type)
                arrived = np.array([before], dtype=dtype)[-1]
                try:
                    node.set_properties({key: arrived})
                except Exception as e:
                    errors.append(f"{where}: refuses its default from the port ({type(e).__name__}: {e})")
                    continue
                after = node.properties.get(key)
                if not isinstance(after, (bool, int, float, str)):
                    errors.append(f"{where}: becomes {type(after).__name__} (convert with int(), float(), bool() or str())")
                elif after != before:
                    errors.append(f"{where}: {before!r} becomes {after!r}")
                missing = [port for port in ports if port not in node.inputs]
                if missing:
                    errors.append(f"{where}: setting it removes the ports {missing}")
                    break
        finally:
            node.finalize()
    if errors:
        raise AssertionError(
            f"Property ports that do not apply ({len(errors)}):\n"
            + "\n".join(f"  - {e}" for e in errors)
        )


try:
    import pytest

    @pytest.fixture(autouse=True)
    def _validate_dispatch_shapes(monkeypatch):
        from nonoha_core.port import StaticTypeOutputPort

        original = StaticTypeOutputPort.dispatch
        monkeypatch.setattr(
            StaticTypeOutputPort,
            "dispatch",
            lambda self, values: _checked_dispatch(original, self, values),
        )
except ImportError:
    # pytest not installed (production environment) - no-op
    pass
