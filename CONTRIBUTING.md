# Contributing to nonoha-core

Thank you for considering a contribution! This document covers how to
make changes to this repository (pull requests and issues). For
development setup and usage, see the [README](README.md).

## Issues

- Bug reports and feature requests: the issue templates will guide you.
- Security issues: do **not** open a public issue — see
  [SECURITY.md](SECURITY.md).

## Contributor License Agreement (CLA)

Your first pull request triggers a bot comment. Reply with:

> I have read the CLA Document and I hereby sign the CLA

— that's it. The signature covers all your future contributions.

Why a CLA? Parts of nonoha are dual-licensed to fund development. You
keep your copyright; you grant VIE a license that includes relicensing.
See [CLA.md](CLA.md) for the full text.

*Corporate contributors: if your employer requires a corporate
agreement, contact VIE before submitting.*

## Pull request flow

1. Fork the repository and create a branch.
2. Make your change and add tests.
3. Ensure `uv run pytest` passes.
4. Open a pull request (the template will guide you).

## Coding guidelines for changes

- Comments and docstrings are written in English.
- Changes must follow the Performance Guidelines in the
  [README](README.md#performance-guidelines).
- nonoha-core ships a pytest plugin that enforces the PortValue contract
  in your tests (opt out with `-p no:nonoha_core`).
