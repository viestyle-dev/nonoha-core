import os
import threading

import pytest

from nonoha_core import environment
from nonoha_core.node import BaseNode, EnvDoc, NodeDoc
from nonoha_core.node_registry import NodeRegistry


def test_get_falls_back_to_the_process_environment(monkeypatch):
    monkeypatch.setenv("NONOHA_TEST_ENV_A", "from-os")
    with environment.using({}):
        assert environment.get("NONOHA_TEST_ENV_A") == "from-os"
        assert environment.get("NONOHA_TEST_ENV_MISSING") is None


def test_update_wins_and_never_touches_os_environ(monkeypatch):
    monkeypatch.setenv("NONOHA_TEST_ENV_A", "from-os")
    with environment.using({}):
        environment.update({"NONOHA_TEST_ENV_A": "runtime", "NONOHA_TEST_ENV_B": "b"})
        assert environment.get("NONOHA_TEST_ENV_A") == "runtime"
        assert environment.get("NONOHA_TEST_ENV_B") == "b"
        assert os.environ["NONOHA_TEST_ENV_A"] == "from-os"
        assert "NONOHA_TEST_ENV_B" not in os.environ


def test_removed_names_read_as_unset_even_if_os_has_them(monkeypatch):
    monkeypatch.setenv("NONOHA_TEST_ENV_A", "stale")
    with environment.using({}):
        environment.update({"NONOHA_TEST_ENV_A": None})
        assert environment.get("NONOHA_TEST_ENV_A") is None
        environment.update({"NONOHA_TEST_ENV_A": "again"})
        assert environment.get("NONOHA_TEST_ENV_A") == "again"


def test_using_restores_the_previous_state():
    with environment.using({"NONOHA_TEST_ENV_C": "outer"}):
        with environment.using({"NONOHA_TEST_ENV_C": "inner"}):
            assert environment.get("NONOHA_TEST_ENV_C") == "inner"
        assert environment.get("NONOHA_TEST_ENV_C") == "outer"


def test_readers_never_see_a_half_applied_update():
    """A name that is always set never reads as missing while others change."""
    stop = threading.Event()
    bad = []

    def reader():
        while not stop.is_set():
            value = environment.get("NONOHA_TEST_STEADY")
            if value is None or not value.isdigit():
                bad.append(value)

    with environment.using({"NONOHA_TEST_STEADY": "0"}):
        threads = [threading.Thread(target=reader) for _ in range(4)]
        for t in threads:
            t.start()
        for i in range(1, 2000):
            # Re-set the steady name and churn another one in the same update
            environment.update({"NONOHA_TEST_STEADY": str(i), "NONOHA_TEST_CHURN": None if i % 2 else "x"})
        stop.set()
        for t in threads:
            t.join()
    assert bad == []


def test_concurrent_writers_do_not_lose_updates():
    with environment.using({}):
        def writer(prefix):
            for i in range(200):
                environment.update({f"NONOHA_TEST_{prefix}_{i}": "x"})

        threads = [threading.Thread(target=writer, args=(p,)) for p in ("W1", "W2", "W3")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert all(
            environment.get(f"NONOHA_TEST_{p}_{i}") == "x" for p in ("W1", "W2", "W3") for i in range(200)
        )


@pytest.mark.parametrize("name", ["GEMINI_API_KEY", "MY_KEY_2", "_PRIVATE"])
def test_writable_names(name):
    assert environment.name_refusal(name) is None


@pytest.mark.parametrize(
    "name",
    [
        "gemini_api_key",
        "1KEY",
        "KEY-NAME",
        "",
        "PATH",
        "HOME",
        "TMPDIR",
        "LD_PRELOAD",
        "DYLD_INSERT_LIBRARIES",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "HTTPS_PROXY",
        "NO_PROXY",
        "SSL_CERT_FILE",
        "REQUESTS_CA_BUNDLE",
        "NONOHA_ANYTHING",
    ],
)
def test_reserved_or_malformed_names(name):
    assert environment.name_refusal(name) is not None


def test_values_must_be_single_line_and_bounded():
    assert environment.value_refusal("abc") is None
    assert environment.value_refusal("a\nPATH=/evil") is not None
    assert environment.value_refusal("a\rb") is not None
    assert environment.value_refusal("a\0b") is not None
    assert environment.value_refusal("x" * environment.MAX_VALUE_BYTES) is None
    assert environment.value_refusal("x" * (environment.MAX_VALUE_BYTES + 1)) is not None


class _KeyNode(BaseNode):
    PROPERTIES = {"key_env": {"description": "Variable holding the key", "default_value": "DEMO_KEY"}}

    def __init__(self, name):
        super().__init__(name, "KeyNode")

    @classmethod
    def describe(cls, properties=None):
        name = str((properties or {}).get("key_env") or "DEMO_KEY")
        return NodeDoc(description="Uses a key", env=(EnvDoc(name, "Demo key", "https://example.com/key"),))


def test_env_declarations_reach_the_catalog_metadata():
    registry = NodeRegistry()
    registry.register_node("KeyNode", _KeyNode)
    env = registry.node_definitions["KeyNode"].metadata.env
    assert [(e.name, e.description, e.url) for e in env] == [("DEMO_KEY", "Demo key", "https://example.com/key")]
    # The declaration follows the properties (e.g. a renamed variable)
    assert _KeyNode.describe({"key_env": "OTHER_KEY"}).env[0].name == "OTHER_KEY"  # type: ignore[union-attr]
