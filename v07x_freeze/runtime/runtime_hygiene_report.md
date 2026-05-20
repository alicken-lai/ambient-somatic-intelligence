# Runtime Hygiene Report

**Audit date:** 2026-05-20

## Git working tree (runtime paths)

Modified tracked runtime files present (expected during active development, **excluded from freeze artifacts**):

| Path | Status |
|------|--------|
| `logs/actions.jsonl` | Modified |
| `logs/checksums.jsonl` | Modified |
| `memory/dmn.jsonl` | Modified |
| `state/daemon/dmn_tick_status.json` | Modified |
| `state/system_state.json` | Modified |
| `governance/audit/decisions.jsonl` | Modified |
| `governance/audit/incidents.jsonl` | Modified |
| `agents/skillify/pending_registrations.jsonl` | Modified |

## Freeze policy compliance

Freeze audit artifacts under `v07x_freeze/` do **not** embed runtime log/state/dmn content. Snapshot JSON contains score aggregates only.

## Recommendation

Do not commit runtime dirty files with freeze PR. Stage only `v07x_freeze/`, `observability/v07x_freeze/`, and `docs/releases/v07x_civilization_freeze_gate.md`.

**Runtime hygiene (freeze bundle): PASS** — dirty runtime files documented, not included in freeze outputs.
