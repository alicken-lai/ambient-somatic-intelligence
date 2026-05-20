# v0.7.4 Cognitive Value Continuity Gate

**Version:** `0.7.4`  
**Date:** 2026-05-20  
**Base:** v0.7.3-alpha BOUNDED CIVILIZATION SEMANTIC CONTINUITY (`CognitiveMeaningContinuityScore` ~0.945)

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Value audit | Present | `v074/audit/` |
| 1 | Continuity + anchor | Advisory | `governance/value/` (phase 1) |
| 2 | Drift + fragmentation | Bounded | `governance/value/` (phase 2) |
| 3 | Provenance + lineage | Labeled / bounded | `governance/value/` (phase 3) |
| 4 | Bounded normative + decay | No immutable ethics | `governance/value/` (phase 4) |
| 5 | Integrity guards | Rewrite blocked | `governance/value/` (phase 5) |
| 6 | Explainability | 3 explainers | `attention/explainability/` |
| 7 | Observability v074 | 6 metrics + score | `observability/v074/` |
| 8 | Validation + timeseries | 6 horizons + 7 stress | `v074/reports/`, `v074_runtime/` |
| 9 | Tests | 10 areas | `tests/v074/` |
| 10 | CognitiveValueContinuityScore | ≥ 0.90 | `cognitive_value_continuity_score.py` |
| 11 | Release doc | This file | `docs/releases/v074_cognitive_value_continuity_gate.md` |

## Value dimensions (Phase 10)

| Dimension | Weight |
|-----------|--------|
| ethical_drift_containment | 0.024 |
| normative_boundary | 0.022 |
| value_lineage_integrity | 0.022 |
| value_decay | 0.022 |
| normative_provenance | 0.022 |
| normative_integrity | 0.021 |

**Gate threshold:** 0.90

## Governor wiring

`CognitiveGovernor._attach_value_continuity_observability()` adds `value_continuity_observability` **after** `semantic_continuity_observability`. **Observational only** — does not change `accepted`, `governed_salience`, constitution, or Guardian.

## Execution

```bash
python3 -m pytest tests/v074/ tests/v073/ tests/v072/ tests/v071/ tests/v070/ tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
python3 -c "from observability.v074.cognitive_value_continuity_score import evaluate_cognitive_value_continuity as e; r=e(); print(r.value_continuity_score, r.gate_pass)"
python3 -c "from v074_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v074/reports/civilization_value_timeseries.json'))"
```

## Constraints honored

- No universal morality, immutable ethics, centralized value authority, forced ethical sync
- No autonomous moral evolution, recursive value correction, hidden value override
- Guardian and constitutional cognition preserved
- Value layer is advisory metadata only

## Overall Gate Verdict

Run `evaluate_cognitive_value_continuity()` and pytest to confirm **PASS**.
