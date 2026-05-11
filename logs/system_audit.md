# System Audit

Timestamp: 2026-05-11T12:53:37Z

## Host

- Architecture: arm64
- OS: macOS 15.5 (Build 24F74)

## Toolchain

- Python: Python 3.9.6 at `/usr/bin/python3`
- uv: missing from PATH
- Git: git version 2.39.5 (Apple Git-154)
- Homebrew: Homebrew 5.1.11
- Node: missing from PATH
- Docker: missing from PATH
- Hermes: Hermes Agent v0.13.0 (2026.5.7) at `/opt/homebrew/bin/hermes`

## Notes

- Hermes was missing at initial audit and installed during Night 0.
- `hermes-agent` was not available through PyPI under that package name.
- Homebrew installation required access to `/opt/homebrew` and the Homebrew cache.

