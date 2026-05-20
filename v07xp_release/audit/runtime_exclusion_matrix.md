# Runtime Exclusion Matrix

**Generated:** 2026-05-20T13:16:55.635620+00:00
**Branch:** ken-dev

## Policy

Runtime daemon state MUST NOT enter the v0.7.x civilization freeze commit.

| Category | Paths | Count |
|----------|-------|-------|
| runtime_excluded | logs/, state/, memory/dmn.jsonl, governance/audit/*.jsonl | 7 |
| dangerous_runtime_state | Same as runtime_excluded (append-only audit) | 7 |

## Excluded paths

- `governance/audit/decisions.jsonl`
- `governance/audit/incidents.jsonl`
- `logs/actions.jsonl`
- `logs/checksums.jsonl`
- `memory/dmn.jsonl`
- `state/daemon/dmn_tick_status.json`
- `state/system_state.json`

## Allowed simulation trees

`*_runtime/` directories under `v050`–`v077` contain **release simulation modules** (e.g. `simulations.py`), not daemon persistence. These are staged as `must_commit_release`.

## .git/info/exclude

Local push-hygiene audit artifacts under `freeze/audit/` are excluded from tracking (documented only; no git config changes).
