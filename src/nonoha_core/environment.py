"""Environment values: per-deployment settings and secrets that nodes read by name.

The graph only names what a node needs (``api_key_env = "GEMINI_API_KEY"``);
the value comes from the deployment, never from shared content. Where it
comes from is the host's business (a runtime may load a ``.env`` file into
the process environment at start, or receive values from its app):

- :func:`get` returns a value changed at run time through :func:`update`,
  otherwise the process environment (``os.environ``).
- Hosts call :func:`update` for changes made while running. It swaps one
  immutable snapshot (copy-on-write), so readers never lock and never see a
  half-applied update, from any thread. It never calls ``setenv``: changing
  the C environment while native threads may read it is unsafe on POSIX.

Nodes read a value when they use it and do not keep it: a request-sending
node sees a new key on its next request, a connection-keeping node on its
next reconnect. There is no change notification.

Values are process-wide: any code in the process (scripts included) can
read them, as with environment variables. Hosts must never send values back
to clients or write them to logs.
"""

from __future__ import annotations

import os
import re
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager

# (values set at run time, names removed at run time); replaced, never mutated
_State = tuple[dict[str, str], frozenset[str]]
_state: _State = ({}, frozenset())
_write_lock = threading.Lock()

NAME_PATTERN = re.compile(r"[A-Z_][A-Z0-9_]*")
MAX_VALUE_BYTES = 4096

# Names that steer the process, child processes or libraries (code
# execution, traffic interception), and the runtime's own settings. Writing
# them from a client is refused even when a node declares them.
_RESERVED_NAMES = frozenset({"PATH", "HOME", "TMP", "TEMP", "TMPDIR"})
_RESERVED_PREFIXES = ("LD_", "DYLD_", "PYTHON", "SSL_", "NONOHA_")
_RESERVED_SUFFIXES = ("_PROXY", "_CA_BUNDLE")


def get(name: str) -> str | None:
    """The value of ``name``, or None when it is not set."""
    values, removed = _state
    value = values.get(name)
    if value is not None:
        return value
    if name in removed:
        return None
    return os.environ.get(name)


def update(changes: Mapping[str, str | None]) -> None:
    """Host side: set (str) or remove (None) values at run time."""
    global _state
    with _write_lock:  # writers only: two hosts' updates must not lose each other
        values, removed = _state
        new_values = dict(values)
        new_removed = set(removed)
        for name, value in changes.items():
            if value is None:
                new_values.pop(name, None)
                new_removed.add(name)
            else:
                new_values[name] = value
                new_removed.discard(name)
        _state = (new_values, frozenset(new_removed))


@contextmanager
def using(changes: Mapping[str, str | None]) -> Iterator[None]:
    """Tests: apply ``changes`` on top of nothing, then restore the previous state."""
    global _state
    with _write_lock:
        previous = _state
        _state = ({}, frozenset())
    update(changes)
    try:
        yield
    finally:
        with _write_lock:
            _state = previous


def name_refusal(name: str) -> str | None:
    """Why a client may not write ``name`` (None when it may)."""
    if not NAME_PATTERN.fullmatch(name):
        return "Use upper-case letters, digits and underscores (e.g. GEMINI_API_KEY)"
    if (
        name in _RESERVED_NAMES
        or name.startswith(_RESERVED_PREFIXES)
        or name.endswith(_RESERVED_SUFFIXES)
    ):
        return f"{name} controls the process or its libraries; set it in the OS environment or the .env file"
    return None


def value_refusal(value: str) -> str | None:
    """Why ``value`` cannot be stored (None when it can)."""
    if "\n" in value or "\r" in value or "\0" in value:
        return "The value must be a single line"
    if len(value.encode("utf-8")) > MAX_VALUE_BYTES:
        return f"The value must be at most {MAX_VALUE_BYTES} bytes"
    return None
