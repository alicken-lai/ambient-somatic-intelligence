# Runtime State Audit

## State Classes

| Path | Class | Recommendation |
| --- | --- | --- |
| `logs/actions.jsonl` | audit/live log | append-only local runtime; avoid routine commits |
| `logs/checksums.jsonl` | audit/live log | append-only local runtime; avoid routine commits |
| `logs/dmn_reflection_cycle/` | generated execution logs | archive or ignore unless reviewing scheduler behavior |
| `state/system_state.json` | live state | do not commit routinely |
| `state/daemon/` | daemon runtime | do not commit routinely |
| `memory/dmn.jsonl` | append-only institutional memory | commit only for explicit operational snapshots |
| `reports/*.md/json` | generated evidence | commit selected release/audit snapshots |
| `.codex_*`, `_run.txt` | transient prompt/run files | ignore/delete locally, do not commit |

## Persistent

- Source code, schemas, docs, rules, tests.
- Selected report snapshots tied to release/audit milestones.

## Ephemeral

- Prompt scratch files.
- Local daemon locks and raw scheduler logs.
- Runtime stdout/stderr logs.

## Audit

- DMN append records.
- Action/checksum logs.
- Guardian reports when deliberately snapshotted.

## Rebuildable

- Most `reports/*.md/json` files can be regenerated from CLI commands.
- Human-readable `latest_*` Guardian reports are generally rebuildable.

## Recommendation

Adopt an explicit snapshot policy: code/docs/tests are tracked; live state is untracked; release/audit reports are tracked only when tied to a named review.
