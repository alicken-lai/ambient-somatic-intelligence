# v0.7.5 Cognitive Intent Continuity Gate

**Version:** `0.7.5`  
**Date:** 2026-05-20  
**Base:** v0.7.4-alpha BOUNDED CIVILIZATION VALUE CONTINUITY (`CognitiveValueContinuityScore` ~0.946)

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Intent audit | Present | `v075/audit/` |
| 1 | Continuity + anchor | Advisory | `governance/intent/` (phase 1) |
| 2 | Drift + fragmentation | Bounded | `governance/intent/` (phase 2) |
| 3 | Provenance + lineage | Labeled / bounded | `governance/intent/` (phase 3) |
| 4 | Bounded objective + decay | No immutable goals | `governance/intent/` (phase 4) |
| 5 | Integrity guards | Rewrite blocked | `governance/intent/` (phase 5) |
| 6 | Explainability | 3 explainers | `attention/explainability/` |
| 7 | Observability v075 | 6 metrics + score | `observability/v075/` |
| 8 | Validation + timeseries | 6 horizons + 7 stress | `v075/reports/`, `v075_runtime/` |
| 9 | Tests | 10 areas | `tests/v075/` |
| 10 | CognitiveIntentContinuityScore | ≥ 0.90 | `cognitive_intent_continuity_score.py` |
| 11 | Release doc | This file | `docs/releases/v075_cognitive_intent_continuity_gate.md` |

## Intent dimensions (Phase 10)

| Dimension | Weight |
|-----------|--------|
| motivational_drift_containment | 0.024 |
| motivational_boundary | 0.022 |
| intent_lineage_integrity | 0.022 |
| intent_decay | 0.022 |
| intent_provenance | 0.022 |
| motivational_integrity | 0.021 |

**Gate threshold:** 0.90

## Governor wiring

`CognitiveGovernor._attach_intent_continuity_observability()` adds `intent_continuity_observability` **after** `value_continuity_observability`. **Observational only** — does not change `accepted`, `governed_salience`, constitution, or Guardian.

## Execution

```bash
python3 -m pytest tests/v075/ tests/v074/ tests/v073/ tests/v072/ tests/v071/ tests/v070/ tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
python3 -c "from observability.v075.cognitive_intent_continuity_score import evaluate_cognitive_intent_continuity as e; r=e(); print(r.intent_continuity_score, r.gate_pass)"
python3 -c "from v075_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v075/reports/civilization_intent_timeseries.json'))"
```

## Constraints honored

- No immutable goals, centralized intention authority, universal objective sync
- No autonomous motivational evolution, recursive goal repair, hidden intent override
- Guardian and constitutional cognition preserved
- Intent layer is advisory metadata only

## Overall Gate Verdict

Run `evaluate_cognitive_intent_continuity()` and pytest to confirm **PASS**.
