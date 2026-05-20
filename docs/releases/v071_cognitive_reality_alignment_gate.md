# v0.7.1 Cognitive Reality Alignment Gate

**Version:** `0.7.1`  
**Date:** 2026-05-19  
**Base:** v0.7.0-alpha SOVEREIGN COGNITIVE CIVILIZATION (`CognitiveCivilizationStabilityScore` ~0.9405)

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Reality audit | Present | `v071/audit/` |
| 1 | Alignment + exchange | Advisory | `governance/reality/` (phase 1) |
| 2 | Divergence + conflict | Bounded | `governance/reality/` (phase 2) |
| 3 | Provenance + replay | Labeled / bounded | `governance/reality/` (phase 3) |
| 4 | Bounded consensus | No forced merge | `governance/reality/` (phase 4) |
| 5 | Integrity guards | Override blocked | `governance/reality/` (phase 5) |
| 6 | Explainability | 3 explainers | `attention/explainability/` |
| 7 | Observability v071 | 6 metrics + score | `observability/v071/` |
| 8 | Validation + timeseries | 5 horizons + 7 stress | `v071/reports/`, `v071_runtime/` |
| 9 | Tests | 10 areas | `tests/v071/` |
| 10 | CognitiveRealityAlignmentScore | ≥ 0.90 | `cognitive_reality_alignment_score.py` |
| 11 | Release doc | This file | `docs/releases/v071_cognitive_reality_alignment_gate.md` |

## Reality dimensions (Phase 10)

| Dimension | Weight |
|-----------|--------|
| divergence_containment | 0.024 |
| bounded_consensus | 0.024 |
| truth_boundary | 0.022 |
| replay_alignment | 0.022 |
| contamination_guard | 0.022 |
| reality_integrity | 0.021 |

**Gate threshold:** 0.90

## Governor wiring

`CognitiveGovernor._attach_reality_alignment_observability()` adds `reality_alignment_observability` **after** `civilization_observability`. **Observational only** — does not change `accepted`, `governed_salience`, constitution, or Guardian.

## Execution

```bash
python3 -m pytest tests/v071/ tests/v070/ tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
python3 -c "from observability.v071.cognitive_reality_alignment_score import evaluate_cognitive_reality_alignment as e; r=e(); print(r.reality_alignment_score, r.gate_pass)"
python3 -c "from v071_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v071/reports/cross_runtime_reality_timeseries.json'))"
```

## Constraints honored

- No forced consensus, sovereign reality merge, centralized truth authority, hidden truth override
- Guardian and constitutional cognition preserved
- Kernel TruthGraph read/compare only — no sovereign override redesign
- Reality layer is advisory metadata only

## Overall Gate Verdict

Run `evaluate_cognitive_reality_alignment()` and pytest to confirm **PASS**.
