# Self-Model Query Interface

`scripts/query_state.py` is the stable CLI for reading Ambient OS self-model state from `state/system_state.json`.

- corrective_actions: none
- response_mode: recommendations only
- source of truth: `state/system_state.json`
- writes: query action logs and checksum-chain metadata only

## Queries

| Query | Purpose |
| --- | --- |
| `health` | Health score, trend, subsystem scores, and baseline deviation. |
| `incidents` | Incident count and repeated anomaly memory. |
| `memory` | DMN append count, memory pressure, Docker context, and latest telemetry link. |
| `reflex` | Reflex confidence, risk class, display risk, and recommendations. |
| `dashboard` | Dashboard path and state-backed values rendered by the dashboard. |
| `digest` | Daily digest path and state-backed digest values. |
| `summary` | Compact system overview across health, incidents, memory, reflex, and validation. |

## Usage

Human-readable output:

```sh
python3 scripts/query_state.py summary
python3 scripts/query_state.py health
python3 scripts/query_state.py memory
```

JSON output:

```sh
python3 scripts/query_state.py summary --json
python3 scripts/query_state.py reflex --json
```

Guardian-routed read-only query:

```sh
python3 scripts/action_router.py state-query summary
python3 scripts/action_router.py state-query incidents --json
```

The Guardian route is `state-query`. It allows only the supported query names and `--json`; unsupported arguments are blocked by the router before execution.

## Contract

The CLI does not recompute dashboard or digest values. It reads `state/system_state.json` and reports values from that state file. To refresh the self-model first, run:

```sh
python3 scripts/action_router.py system-state-build
```

Use `summary` to check `stale_state_detection` before relying on derived dashboard or digest metadata.
