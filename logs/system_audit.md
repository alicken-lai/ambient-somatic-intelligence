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

## Night 1 Update

- uv: uv 0.11.13 (Homebrew 2026-05-11 aarch64-apple-darwin)
- Node: v26.0.0
- npm: 11.12.1
- Docker CLI: Docker version 29.4.3, build 055a478ea9
- Docker daemon: not running at `unix:///var/run/docker.sock`

## Notes

- Hermes was missing at initial audit and installed during Night 0.
- `hermes-agent` was not available through PyPI under that package name.
- Homebrew installation required access to `/opt/homebrew` and the Homebrew cache.
