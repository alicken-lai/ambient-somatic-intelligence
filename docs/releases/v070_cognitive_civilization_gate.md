# v0.7.0 Cognitive Civilization Gate

**Version:** `0.7.0`  
**Date:** 2026-05-19  
**Base:** v0.6.5C-alpha RUNTIME-SAFE EXTERNAL COGNITION COEXISTENCE (`ExternalRuntimeGovernanceScore` ~0.937)

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Sovereign audit | Present | `v070/audit/` |
| 1 | Diplomacy + sovereign runtime | Advisory | `governance/civilization/` (phase 1) |
| 2 | Constitutional interop | No override | `governance/civilization/` (phase 2) |
| 3 | Non-interference + dominance | Blocked | `governance/civilization/` (phase 3) |
| 4 | Provenance exchange | Isolated identity | `governance/civilization/` (phase 4) |
| 5 | Federation advisory | No hive-mind | `governance/civilization/` (phase 5) |
| 6 | Explainability | 3 explainers | `attention/explainability/` |
| 7 | Observability v070 | 6 metrics + score | `observability/v070/` |
| 8 | Validation + timeseries | 5 horizons + 7 stress | `v070/reports/`, `v070_runtime/` |
| 9 | Tests | 10 areas | `tests/v070/` |
| 10 | CognitiveCivilizationStabilityScore | ≥ 0.90 | `cognitive_civilization_stability_score.py` |
| 11 | Release doc | This file | `docs/releases/v070_cognitive_civilization_gate.md` |

## Civilization dimensions (Phase 10)

| Dimension | Weight |
|-----------|--------|
| diplomacy_boundary | 0.024 |
| treaty_integrity | 0.024 |
| federation_stability | 0.022 |
| non_interference | 0.022 |
| provenance_exchange | 0.022 |
| sovereignty_alignment | 0.021 |

**Gate threshold:** 0.90

## Governor wiring

`CognitiveGovernor._attach_civilization_observability()` adds `civilization_observability` after runtime soak. **Observational only** — does not change `accepted`, `governed_salience`, constitution, or Guardian.

## Execution

```bash
python3 -m pytest tests/v070/ tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
python3 -c "from observability.v070.cognitive_civilization_stability_score import evaluate_cognitive_civilization_stability as e; r=e(); print(r.civilization_score, r.gate_pass)"
python3 -c "from v070_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v070/reports/inter_sovereign_timeseries.json'))"
```

## Constraints honored

- No hive-mind, cognition merging, shared identity, autonomous diplomacy, sovereignty absorption
- Guardian and constitutional cognition preserved
- No weakening of Guardian or constitutional override of Ambient/Hermes
- Civilization layer is advisory metadata only

## Overall Gate Verdict

Run `evaluate_cognitive_civilization_stability()` and pytest to confirm **PASS**.
