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
