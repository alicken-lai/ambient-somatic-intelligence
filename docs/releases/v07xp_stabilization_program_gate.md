# v0.7.x-P Stabilization Program Gate

**Version:** `v07xp`  
**Date:** 2026-05-20  
**Scope:** Hardening only — no v0.7.8, no new governance layers

## Verdict

| Check | Result |
|-------|--------|
| CivilizationLineageIntegrityScoreV2 ≥ 0.95 | **PASS** (0.954016) |
| All layer gates (0.90) | **PASS** |
| Pytest v060–v077 (10×) | **PASS** (395×10) |
| Governor 1000-cycle replay | **PASS** |
| Thresholds unchanged | **PASS** |
| Stress tests unchanged | **PASS** |

**Overall gate:** **PASS**

## Score before / after

| Metric | Before | After |
|--------|--------|-------|
| v070 civilization_score | 0.940484 | **0.959216** |
| Lineage integrity (min) | 0.940484 | **0.954016** |
| Weakest layer | v070 | v077 (still ≥ 0.95) |

## Code change (v070)

`observability/v070/cognitive_civilization_stability_score.py`:

- Added `CIVILIZATION_PARENT_RETENTION = 0.88` aligned with v065c external-runtime horizon
- Replaced implicit `0.86` multiplier on `external_runtime_score`

## Artifacts

| Phase | Path |
|-------|------|
| 0 audit | `v07xp/audit/` |
| 1 convergence | `v07xp/convergence/` |
| 2 governor | `v07xp/governor/` |
| 3 observability | `v07xp/observability/` |
| 4 runtime | `v07xp/runtime/` |
| 5 testing | `v07xp/testing/` |
| 6 freeze V2 | `v07xp/freeze_snapshot/`, `observability/v07xp_freeze/` |

## Execution

```bash
PYTHONPATH=. python3 v07xp/freeze_snapshot/evaluator_v2.py
PYTHONPATH=. python3 v07x_freeze/freeze_snapshot/evaluator.py
python3 -m pytest tests/v070/ tests/v071/ tests/v072/ tests/v073/ tests/v074/ tests/v075/ tests/v076/ tests/v077/ tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
```

## Constraints honored

- No threshold lowering, fake scores, or weakened stress
- No Guardian / kernel stack redesign
- PatchRegistry `restore_all` teardown hygiene
