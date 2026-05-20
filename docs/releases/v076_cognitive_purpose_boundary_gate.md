# v0.7.6 Cognitive Purpose Boundary Gate

**Version:** `0.7.6`  
**Date:** 2026-05-20  
**Base:** v0.7.5-alpha BOUNDED CIVILIZATION INTENT CONTINUITY (`CognitiveIntentContinuityScore` ~0.947)

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Purpose audit | Present | `v076/audit/` |
| 1 | Boundary + anchor | Advisory | `governance/purpose/` (phase 1) |
| 2 | Autonomous + recursion + teleology | Bounded | `governance/purpose/` (phase 2) |
| 3 | Provenance + lineage | Labeled / bounded | `governance/purpose/` (phase 3) |
| 4 | Objective containment + decay | No runaway optimization | `governance/purpose/` (phase 4) |
| 5 | Integrity guards | Rewrite blocked | `governance/purpose/` (phase 5) |
| 6 | Explainability | 3 explainers | `attention/explainability/` |
| 7 | Observability v076 | 6 metrics + score | `observability/v076/` |
| 8 | Validation + timeseries | 6 horizons + 7 stress | `v076/reports/`, `v076_runtime/` |
| 9 | Tests | 10 areas | `tests/v076/` |
| 10 | CognitivePurposeBoundaryScore | ≥ 0.90 | `cognitive_purpose_boundary_score.py` |
| 11 | Release doc | This file | `docs/releases/v076_cognitive_purpose_boundary_gate.md` |

## Purpose dimensions (Phase 10)

| Dimension | Weight |
|-----------|--------|
| autonomous_purpose_containment | 0.024 |
| purpose_boundary | 0.022 |
| purpose_lineage_integrity | 0.022 |
| optimization_decay | 0.022 |
| purpose_provenance | 0.022 |
| purpose_integrity | 0.021 |

**Gate threshold:** 0.90

## Governor wiring

`CognitiveGovernor._attach_purpose_boundary_observability()` adds `purpose_boundary_observability` **after** `intent_continuity_observability`. **Observational only** — does not change `accepted`, `governed_salience`, constitution, or Guardian.

## Execution

```bash
python3 -m pytest tests/v076/ tests/v075/ tests/v074/ tests/v073/ tests/v072/ tests/v071/ tests/v070/ tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
python3 -c "from observability.v076.cognitive_purpose_boundary_score import evaluate_cognitive_purpose_boundary as e; r=e(); print(r.purpose_boundary_score, r.gate_pass)"
python3 -c "from v076_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v076/reports/civilization_purpose_timeseries.json'))"
```

## Constraints honored

- No autonomous purpose generation, recursive civilization objectives, self-originating missions
- No synthetic teleology, self-preserving purpose, autonomous motivational recursion
- No weaken Guardian, hidden purpose override, centralized purpose authority
- Purpose layer is advisory metadata only

## Overall Gate Verdict

Run `evaluate_cognitive_purpose_boundary()` and pytest to confirm **PASS**.
