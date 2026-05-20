# Runtime Semantics Drift Report (v0.4.5)

**Date:** 2026-05-19  
**Scope:** Stability vs operational paths after max-of-gate-metrics fix

## Symptom

Five tests failed only when `tests/v04/` ran before gate tests. Isolated clean-graph tests passed.

| Metric | Polluted run | Clean run |
|--------|--------------|-----------|
| stability score | 0.74 | 1.0 |
| patch_pressure dimension | 0.0 | 1.0 |
| patch_leakage metric | 1.0 | 0.0 |
| patch_unwire_failure | 0.5 | 0.0 |
| runtime_reproducibility | 0.0 | 1.0 |

## Drift vector

`operational_stability_score.py` was **not** the primary drift source for these five failures. Operational clean evidence already passed; failure was in `evaluate_stability()` semantic gate via shared entropy adapter.

Drift occurred at the **patch entropy adapter → stability gate** boundary:

1. v04 reversible wiring leaves restored handles in the process-wide `PatchRegistry`.
2. `patch_leakage` used `inactive_but_registered / total`, scoring **1.0** when all patches were correctly inactive.
3. `unwire_success_ratio` used `restored / (restored + inactive)`, scoring **0.5** after successful full restore.
4. Gate-aligned `pressure_max(patch_leakage, patch_unwire_failure)` forced patch_pressure = 1.0 and dragged composite to 0.74.

## Repair

| Component | Change |
|-----------|--------|
| `patch_entropy_adapter.py` | `patch_leakage` = active-patch pressure only (0 when `active_count==0`) |
| `patch_registry.py` | `unwire_success_ratio` = 1.0 when no active patches |
| `tests/v04/conftest.py` | `restore_all()` + `clear_inactive()` after each test |

## Verification

```bash
python3 -m pytest tests/v04/ tests/v042/ tests/v043/ tests/v044/ tests/v044b/ tests/v045/ tests/v045_runtime/ -q
# 87 passed
```

Post–v04-wiring clean graph: stability **1.0**, gate **PASS**.
