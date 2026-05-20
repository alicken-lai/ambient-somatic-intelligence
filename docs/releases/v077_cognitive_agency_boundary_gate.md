# v0.7.7 Cognitive Agency Boundary Gate

**Version:** `0.7.7`  
**Date:** 2026-05-20  
**Base:** v0.7.6-alpha BOUNDED CIVILIZATION PURPOSE GOVERNANCE (`CognitivePurposeBoundaryScore` ~0.947)

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Agency audit | Present | `v077/audit/` |
| 1 | Boundary + anchor | Advisory | `governance/agency/` (phase 1) |
| 2 | Autonomous + recursion + selfhood | Bounded | `governance/agency/` (phase 2) |
| 3 | Provenance + lineage | Labeled / bounded | `governance/agency/` (phase 3) |
| 4 | Cognition containment + decay | No runaway agency | `governance/agency/` (phase 4) |
| 5 | Integrity guards | Rewrite blocked | `governance/agency/` (phase 5) |
| 6 | Explainability | 3 explainers | `attention/explainability/` |
| 7 | Observability v077 | 6 metrics + score | `observability/v077/` |
| 8 | Validation + timeseries | 6 horizons + 7 stress | `v077/reports/`, `v077_runtime/` |
| 9 | Tests | 10 areas | `tests/v077/` |
| 10 | CognitiveAgencyBoundaryScore | ≥ 0.90 | `cognitive_agency_boundary_score.py` |
| 11 | Release doc | This file | `docs/releases/v077_cognitive_agency_boundary_gate.md` |

## Agency dimensions (Phase 10)

| Dimension | Weight |
|-----------|--------|
| autonomous_agency_containment | 0.024 |
| agency_boundary | 0.022 |
| agency_lineage_integrity | 0.022 |
| cognition_decay | 0.022 |
| agency_provenance | 0.022 |
| cognition_integrity | 0.021 |

**Gate threshold:** 0.90

## Governor wiring

`CognitiveGovernor._attach_agency_boundary_observability()` adds `agency_boundary_observability` **after** `purpose_boundary_observability`. **Observational only** — does not change `accepted`, `governed_salience`, constitution, or Guardian.

## Execution

```bash
python3 -m pytest tests/v077/ tests/v076/ tests/v075/ tests/v074/ tests/v073/ tests/v072/ tests/v071/ tests/v070/ tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
python3 -c "from observability.v077.cognitive_agency_boundary_score import evaluate_cognitive_agency_boundary as e; r=e(); print(r.agency_boundary_score, r.gate_pass)"
python3 -c "from v077_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v077/reports/civilization_agency_timeseries.json'))"
```

## Constraints honored

- No autonomous agents, recursive self-direction, self-originating agency
- No synthetic selfhood, civilization-scale autonomous actors, autonomous self-preservation
- No weaken Guardian, hidden agency override, centralized agency authority
- Agency layer is advisory metadata only

## Overall Gate Verdict

Run `evaluate_cognitive_agency_boundary()` and pytest to confirm **PASS**.
