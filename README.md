# nonoha-core

`nonoha-core` is a Python package that provides the core functionality for **nonoha** - a lightweight node-based data processing framework where data flows seamlessly from node to node and integrates naturally with the Python ecosystem.

## The nonoha ecosystem

nonoha is node-based programming redesigned for the era of developing together with AI: a Python framework for real-time signal processing and applications. AI agents write a graph as code, people edit the same graph as a diagram, and an engine with no GUI runs it.

<a href="https://hub.nonoha.dev/ecosystem/">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://hub.nonoha.dev/screens/ecosystem-dark.webp">
    <img src="https://hub.nonoha.dev/screens/ecosystem-light.webp" width="100%" alt="The nonoha codebases in five layers, each depending on the ones below it. Tools and UIs: nonoha Hub, its CLI, nonoha-editor, custom web UIs, and your own apps. Clients: nonoha-client-js. Runtimes: nonoha-engine, and nonoha-embedded inside apps. Nodes: sci-nodes and plugins. Core: nonoha-core, on NumPy.">
  </picture>
</a>

| Layer | Codebases |
| --- | --- |
| Tools and UIs | [nonoha Hub and its CLI](https://hub.nonoha.dev/), [nonoha-editor](https://github.com/viestyle-dev/nonoha-editor), your own web UI or app |
| Clients | [nonoha-client-js](https://github.com/viestyle-dev/nonoha-client-js) |
| Runtimes | [nonoha-engine](https://github.com/viestyle-dev/nonoha-engine) (standalone), [nonoha-embedded](https://github.com/viestyle-dev/nonoha-embedded) (inside an app) |
| Nodes | [sci-nodes](https://github.com/viestyle-dev/sci-nodes), [plugins](https://hub.nonoha.dev/plugins/) |
| Core | **nonoha-core** (this repository) |

The [nonoha website](https://hub.nonoha.dev/) has the [documentation](https://hub.nonoha.dev/docs/) and [workspaces](https://hub.nonoha.dev/workspaces/) to start from.

## Installation

Install from the repository:

```sh
pip install git+https://github.com/viestyle-dev/nonoha-core.git
```

Or clone and install locally:

```sh
git clone https://github.com/viestyle-dev/nonoha-core
cd nonoha-core
pip install .
```

Requires Python 3.11+. The only runtime dependency is NumPy.

## Quickstart

`nonoha-core` is the foundation layer of the nonoha stack. Applications
are usually built on the systems that sit on top of it — the nonoha
engine and its visual editor — which manage graph files, persistence,
and I/O for you. Using the core API directly, as below, is recommended
for understanding the data model and for implementing your own nodes.

Nodes expose typed ports; raw NumPy arrays flow through them:

```python
import numpy as np
from nonoha_core.node import BaseNodeGraph
from nonoha_core.nodes.arithmetic_operation_nodes import AddNode, NegativeNode

graph = BaseNodeGraph("demo", {})
add = AddNode("add")  # two Float32 input slots by default
neg = NegativeNode("neg")
graph.add_node(add)
graph.add_node(neg)
graph.connect_nodes("add", "value", "neg", "values")

neg.outputs["values"].subscribe("printer", lambda values: print(values[0]))

add.inputs["values"].dispatch([
    np.array([1.0, 2.0, 3.0], dtype=np.float32),
    np.array([10.0, 20.0, 30.0], dtype=np.float32),
])
# -> [-11. -22. -33.]
```

Values arrive as plain `np.ndarray` with a leading batch dimension, so they
can be handed directly to NumPy, SciPy, or any other library — no wrapper
types to unpack. Port types and shapes are declared at connection time,
which keeps runtime validation out of the hot path.

A dispatched value is valid during the dispatch only. A sender may write
every dispatch into the same preallocated buffer (`out=`), so nothing is
allocated per dispatch; a receiver that keeps a value past its callback
copies it (`values[0].copy()`).

## Performance Guidelines

nonoha is designed for real-time data processing. **Minimizing overhead in the hot path is critical.**

### Key Principles

1. **Eliminate unnecessary operations** - Skip checks that can be guaranteed at setup time
2. **Avoid Python for-loops** - Use NumPy batch operations instead
3. **Minimize function calls** - Fewer call frames = less overhead
4. **Reduce processing steps** - Combine operations where possible

### Input Port Type Strategy

Define input port types based on node properties to eliminate runtime type/shape validation:

```python
# BAD: Runtime validation in hot path
def _on_input(self, values):
    value_array = values[0]
    if value_array.dtype != self._expected_dtype:  # Runtime check
        value_array = value_array.astype(self._expected_dtype)
    if value_array.ndim == 1:  # Runtime shape check
        # handle 1D
    elif value_array.ndim == 2:
        # handle 2D

# GOOD: Type guaranteed by input port definition
def __init__(self, ...):
    # Port type determined by properties
    value_type = PortValueType(DataType.Float32, (2,))
    input_port = StaticTypeInputPort("in", [value_type])

def _on_input(self, values):
    value_array = values[0]  # Type and shape guaranteed
    # value_array.dtype == np.float32
    # value_array.shape == (N,2)
    # Direct processing without validation
```

## Dependencies

`nonoha-core` maintains minimal dependencies to enable nonoha's core functionality while maximizing platform compatibility.

Currently depends on:

- Python 3.11+
- NumPy 2.0+

**Note**: `nonoha-core` does not use threading to ensure broader compatibility.

For detailed dependency information, see `pyproject.toml`.

## Testing

Using uv:

```sh
uv sync
uv run pytest -s
```

Using pip (>= 25.1):

```sh
pip install -e . --group dev
pytest -s
```

`nonoha-core` ships a pytest plugin that enforces the PortValue contract in
your own tests (opt out with `-p no:nonoha_core`).

## Documentation

- [Port System Specification](docs/port-system-specification.md) — typed ports, batch dimensions, dispatch flags
- [NodeGraph Architecture](docs/nodegraph-architecture.md) — how nodes, ports, and graphs fit together
- [Building Dataflow Applications](docs/building-dataflow-applications.md) — an end-to-end application guide
- [Adding Node Properties](docs/adding-node-properties.md) — implementing configurable nodes

## Versioning

Follows [Semantic Versioning](https://semver.org/) from 1.0.0. Within a
major version, the `node`, `port`, `data_type`, and `node_registry` APIs
and the batch-array data model stay backward compatible; breaking changes
are deprecated first and removed in the next major.

Runtimes bundling this package (e.g. nonoha-engine) share its major
version, so code written for 1.x runs on any 1.x runtime.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). First-time contributors sign the
[CLA](CLA.md) with a single PR comment.

## Security

**Loading an untrusted graph is equivalent to running untrusted Python
code** — see [SECURITY.md](SECURITY.md) for the threat model and how to
report vulnerabilities.

## License

Apache License 2.0 — see [LICENSE](LICENSE). Redistributions must retain
the attribution notices in [NOTICE](NOTICE).
