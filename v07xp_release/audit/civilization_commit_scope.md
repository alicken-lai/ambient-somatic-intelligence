# Civilization Commit Scope

**Generated:** 2026-05-20T13:16:55.635620+00:00

## Release intent

Single freeze commit for v0.7 civilization governance lineage (v070–v077) plus v07x_freeze and v07xp stabilization artifacts.

## In scope (must_commit_release): 128 paths

- Governance layers: civilization → agency (`governance/civilization` … `governance/agency`)
- Observability v070–v077, v07x_freeze, v07xp_freeze
- Tests v060–v065c, v070–v077
- Release gates `docs/releases/v070`–`v077`, v07x, v07xp
- Per-version audit/report/runtime-simulation trees `v070/`–`v077/`, `v07x_freeze/`, `v07xp/`
- Kernel: `kernel/wiring/patch_registry.py` (PatchRegistry `clear_inactive` teardown hygiene)
- Hermes external rules/skills mounts (v065b lineage)
- This hygiene bundle: `v07xp_release/`

## Out of scope

| Bucket | Count | Rationale |
|--------|-------|-----------|
| runtime_excluded | 7 | Daemon/audit append-only state |
| hygiene_excluded | 14 | Attention v05x WIP (separate release train) |
| unrelated_wip | 1 | None after v*_runtime reclassification |

## Code fixes in this release

1. v070 `CIVILIZATION_PARENT_RETENTION = 0.88` (retention alignment)
2. PatchRegistry `clear_inactive()` on `restore_all` teardown
