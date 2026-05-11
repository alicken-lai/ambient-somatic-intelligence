# Hermes Installation

Timestamp: 2026-05-11T12:53:37Z

## Initial State

- `hermes` was missing from PATH.
- `python3 -m pip show hermes-agent` did not find a package.
- `python3 -m pip install --user hermes-agent` failed because PyPI has no matching `hermes-agent` distribution.

## Install Path

- Homebrew search found `hermes-agent`.
- Installed with `brew install hermes-agent`.

## Verification

```text
Hermes Agent v0.13.0 (2026.5.7)
Project: /opt/homebrew/Cellar/hermes-agent/2026.5.7/libexec/lib/python3.14/site-packages
Python: 3.14.4
OpenAI SDK: 2.35.0
```

