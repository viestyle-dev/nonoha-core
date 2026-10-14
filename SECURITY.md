# Security Policy

## Reporting a Vulnerability

Please use GitHub's **Private Vulnerability Reporting**
(Security tab → "Report a vulnerability") on this repository.
Do not open public issues for security reports.

## Threat model: graph definitions can execute code

nonoha-core includes script nodes that compile and execute Python code
embedded in graph definitions (`src/nonoha_core/nodes/script_nodes.py`).
**Loading an untrusted graph (.vnf / graph.json) is equivalent to running
untrusted Python code.** Only load graphs from sources you trust. If you
must run untrusted graphs, isolate the process at the OS level.

## Supported versions

Security fixes target the latest minor release.
