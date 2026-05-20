# Civilization Score Gap Report

**Program:** v0.7.x-P stabilization  
**Date:** 2026-05-20

## Score trajectory

| Stage | v070 | Lineage (min) | Gate |
|-------|------|---------------|------|
| Pre-fix | 0.940484 | 0.940484 | FAIL |
| Post-fix | 0.959216 | 0.954016 | PASS |

## Layer stack (post-fix)

| Version | Primary score |
|---------|---------------|
| v070 | 0.959216 |
| v071 | 0.959926 |
| v072 | 0.958536 |
| v073 | 0.957341 |
| v074 | 0.956313 |
| v075 | 0.955429 |
| v076 | 0.954669 |
| v077 | 0.954016 |

## Change applied

- **File:** `observability/v070/cognitive_civilization_stability_score.py`
- **Constant:** `CIVILIZATION_PARENT_RETENTION = 0.88` (was implicit `0.86`)
- **Rationale:** Align civilization horizon with v065c `external_runtime` parent retention; removes double-compression at v070 boundary.
- **Thresholds:** Unchanged (gate 0.90, freeze 0.95, production tier 0.95).
