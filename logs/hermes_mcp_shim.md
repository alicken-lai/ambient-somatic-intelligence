# Hermes MCP Shim Reproducibility

Timestamp: 2026-05-12

## Goal

Move the custom Hermes MCP memory tools out of hidden local-only configuration
and into repo-managed infrastructure.

## Change

Added `tools/hermes_mcp_shim/` with:

- `mcp_serve.py`, mirrored from the active Hermes MCP shim.
- `README.md`, covering installation, usage, registration, and exposed tools.
- `codex_mcp_config.example.toml`, showing Codex MCP server registration.
- `install.sh`, an optional copy helper for installing the repo-managed shim
  into a Hermes runtime home.

## Exposed Ambient OS Tools Documented

- `dmn_search`
- `dmn_append`
- `mempalace_query`
- `guardian_check`
- `system_state_read`
- `night_log_search`

## Path And Secret Hygiene

The repo-managed docs avoid secrets and use placeholder paths in configuration
examples. The shim resolves runtime locations through `HERMES_HOME` and
`AMBIENT_OS_ROOT`, with home-relative fallbacks for local operation.

