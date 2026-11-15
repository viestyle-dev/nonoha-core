# Environment values

`nonoha_core.environment` is how nodes read per-deployment values (API keys,
provider URLs) by name. A graph stores only the name; the value never enters
graph files, ports, properties or catalogs.

## For node authors

```python
from nonoha_core import environment
from nonoha_core.node import EnvDoc, NodeDoc

@classmethod
def describe(cls, properties=None):
    name = str((properties or {}).get("api_key_env") or "MY_API_KEY")
    return NodeDoc(env=(EnvDoc(name, "API key for My Service", "https://example.com/keys"),))

def _send(self):
    key = environment.get(str(self.properties["api_key_env"]) or "MY_API_KEY")
```

- `environment.get(name) -> str | None`: read at the moment of use (each
  request, each reconnect); do not keep the value. There is no change
  notification: the next use sees a new value.
- Declare every name in `NodeDoc.env` (`describe(properties)` may follow
  the properties, e.g. a renamed key). Hosts accept values only for
  declared names, and tools list them.
- Never log, dispatch or store a value; mask it in error texts.

## For hosts (runtimes)

- `get` returns a value set through `update`, otherwise `os.environ`.
- `update({name: value | None})` (None removes) swaps an immutable snapshot
  (copy-on-write): readers never lock and never see half an update, from any
  thread. It never calls `setenv`, which is unsafe while native threads may
  read the C environment.
- A host loads its configuration (e.g. a `.env` file) into `os.environ`
  once at start, before plugins load and threads start; later changes go
  through `update`, so libraries and child processes see them after a
  restart.
- `name_refusal(name)` and `value_refusal(value)` say why a client may not
  write a name (format, or names that steer processes and libraries: `PATH`,
  `*_PROXY`, `PYTHON*`, `SSL_*`, `NONOHA_*`, ...) or a value (multi-line,
  over 4 KiB). They return None when it may.
- Hosts never return values to clients.
- `using(values)` replaces the state for a test and restores it afterwards.
