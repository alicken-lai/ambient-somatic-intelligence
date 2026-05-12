# Night 35 Persistent Nervous System

Route: persistent-nervous-system-build
Mode: recommendations only; local telemetry only; external actions disabled; interactive CUA disabled.

## Components

- Hermes MCP shim reload target: `~/.hermes/mcp_shim/mcp_serve.py`
- Autonomous DMN tick loop: `scripts/dmn_tick_loop.py`
- Health check: `scripts/persistent_nervous_system_health.py`
- Installer/reloader: `scripts/install_persistent_nervous_system.py`
- LaunchAgent source: `launchd/ai.ambient-os.dmn-tick.plist`
- Runtime status: `state/daemon/dmn_tick_status.json`

## Tick Behavior

Every 60 seconds the LaunchAgent runs a local tick loop that:

- collects local telemetry with `sense_local.collect_snapshot`;
- records a telemetry snapshot under `observability/snapshots`;
- classifies the tick through Guardian route `persistent-nervous-system-build`;
- appends a compact telemetry summary to DMN;
- rebuilds `state/system_state.json` so counters reflect DMN growth;
- writes a daemon status file for health checks.

## Safety Constraints

- No external actions are enabled.
- No interactive CUA is enabled.
- Guardian must return `ALLOW` for each autonomous tick before append.
- Existing fragmented memory tools remain intact.

## Verification

- Hermes MCP shim was copied to `~/.hermes/mcp_shim/mcp_serve.py`.
- Installed shim contains `memory_recall`.
- Ambient DMN tick LaunchAgent was installed at `/Users/alicken/Library/LaunchAgents/ai.ambient-os.dmn-tick.plist`.
- `launchctl` reports `ai.ambient-os.dmn-tick` loaded and running.
- Tick process observed as PID `53183` with parent PID `1`, which confirms launchd ownership rather than Codex terminal ownership.
- Health check reports:
  - Hermes gateway: loaded, `spawn scheduled`, last exit code `1`.
  - Ambient DMN tick: loaded, running.
  - Last tick timestamp: `2026-05-12T14:08:17.312459+00:00`.
  - Last DMN append timestamp: `2026-05-12T14:08:23.665114+00:00`.
  - system_state counter consistency: true, `dmn_append_count=95`, actual DMN count `95`.

## Hermes Gateway Separation

`ai.hermes.gateway` was not modified. Its runtime issue is documented separately in `logs/night35_hermes_gateway_issue.md`.
