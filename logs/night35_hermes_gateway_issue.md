# Night 35 Hermes Gateway Runtime Issue

Route: persistent-nervous-system-build
Mode: read-only diagnostics only.

## Status

- `ai.hermes.gateway` exists at `/Users/alicken/Library/LaunchAgents/ai.hermes.gateway.plist`.
- `launchctl` reports the job is loaded but in `spawn scheduled` state.
- Observed runs: 542 at inspection time.
- Last exit code: 1.
- No destructive changes, credential changes, reinstall, or plist replacement were performed.

## Plist Observations

- Program path exists: `/opt/homebrew/Cellar/hermes-agent/2026.5.7/libexec/bin/python`.
- Command: `python -m hermes_cli.main gateway run --replace`.
- Working directory: `/opt/homebrew/Cellar/hermes-agent/2026.5.7/libexec/lib/python3.14/site-packages`.
- `HERMES_HOME` is set to `/Users/alicken/.hermes`.
- Stdout log: `/Users/alicken/.hermes/logs/gateway.log`.
- Stderr log: `/Users/alicken/.hermes/logs/gateway.error.log`.

## Log Evidence

Recent stderr repeats:

- `No user allowlists configured. All unauthorized users will be denied.`
- `Discord: discord.py not installed`
- `No adapter available for discord`
- `Gateway failed to connect any configured messaging platform: all configured messaging platforms failed to connect`

Recent stdout shows the gateway starts, reads `/Users/alicken/.hermes/sessions`, then exits after failing to connect a configured platform.

## Likely Causes To Investigate Separately

- Missing environment variables or allowlist configuration for enabled platforms.
- Stale Hermes config enabling a platform whose adapter is unavailable.
- Missing optional dependency, specifically `discord.py` for the configured Discord adapter.
- Working directory and command path appear present, but should be revalidated under the exact launchd environment before repair.
- MCP shim path mismatch is not the primary error shown by gateway logs, but should remain on the checklist because the MCP shim was separately refreshed to `~/.hermes/mcp_shim/mcp_serve.py`.
- Permission issue is possible but not directly indicated by the current log evidence.

## Blocked Actions

- Did not edit `/Users/alicken/Library/LaunchAgents/ai.hermes.gateway.plist`.
- Did not change credentials or allowlists.
- Did not reinstall Hermes.
- Did not replace gateway runtime files.
