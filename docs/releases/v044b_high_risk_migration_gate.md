# v0.4.4B High-Risk Mutation Migration — Release Gate

**Version:** `0.4.4b`  
**Date:** 2026-05-18  
**Base:** v0.4.4-alpha (7.2% overall coverage, score 0.570)

## Verdict: **PARTIAL**

High-risk in-scope migration and score gate **PASS**. Full legacy surface (500 catalogued / 857 metadata) and overall coverage target **not** met — by design this gate reports honest metrics.

## Gate Criteria

| Criterion | Target | Result |
|-----------|--------|--------|
| Phase 0 reconciliation | 857/857 accounted OR honest explanation | **PASS** — `PASS_honest`; 500 catalogued, 357 metadata rollup explained |
| High-risk file coverage | 100% (in-scope) | **PASS** — **100%** (52/52, ontology excluded) |
| Overall coverage | ≥ 35% | **FAIL** — **20.6%** (103/500) |
| Trace coverage | ≥ 0.70 | **PASS** — **1.00** |
| HighRiskMigrationScore | ≥ 0.75 | **PASS** — **0.841** |
| pytest `tests/v044b/` | Green | **PASS** — 14 passed |
| pytest `tests/v044/` regression | Green | **PASS** — 12 passed |
| pytest `tests/v043/` regression | Green | **PASS** — 22 passed |

## Phase 0 — Surface Reconciliation

| Metric | Value |
|--------|-------|
| v043 metadata scanned | 857 |
| v043/v044 catalogued detail | 500 |
| Metadata gap | 357 (rollup, not missing JSON rows) |
| Live rescan unique | 279 |
| Accounting verdict | `PASS_honest` |

Artifacts: `v044b/audit/mutation_surface_reconciliation.json`, `missing_mutation_paths.json`, `inventory_gap_report.md`

## Governed Coverage (Phase 6)

```json
{
  "high_risk_coverage": 1.0,
  "overall_coverage": 0.206,
  "trace_coverage": 1.0,
  "high_risk_gate_pass": true,
  "overall_gate_pass": false,
  "trace_gate_pass": true
}
```

## HighRiskMigrationScore (Phase 8)

```json
{
  "score": 0.8412,
  "classification": "ready",
  "gate_pass": true,
  "gate_threshold": 0.75,
  "dimensions": {
    "high_risk_coverage": 1.0,
    "overall_coverage": 0.206,
    "trace_coverage": 1.0,
    "infrastructure": 1.0,
    "regression_stability": 1.0
  }
}
```

Probe:

```bash
python3 v044b/audit/reconcile_mutations.py
python3 -c "
from observability.v04.governed_coverage import compute_governed_coverage
from observability.v04.high_risk_migration_score import evaluate_high_risk_migration
print(compute_governed_coverage().to_dict())
print(evaluate_high_risk_migration().to_dict())
"
pytest tests/v044b/ tests/v044/ tests/v043/ -q
```

## Out of scope (unchanged)

- Ontology / promotion / verifier / Guardian / telemetry scoring
- Auto-delete legacy paths or historical log rewrite

## Next steps

1. Raise overall coverage toward 35%+ (broader FILE_WRITE call-site migration).
2. Expand v043 audit detail rows if claiming full 857-path catalog.
3. v0.4.4C: strict `require_context=True` on production registries.
