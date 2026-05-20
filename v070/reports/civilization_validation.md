# Civilization Validation (v0.7.0)

**Version:** `0.7.0`  
**Date:** 2026-05-19  
**Base:** v0.6.5C-alpha RUNTIME-SAFE EXTERNAL COGNITION COEXISTENCE

## Scope

Phases 0–11: audit, `governance/civilization/`, explainability, observability, reports, tests, gate score, release doc.

## Validation checklist

| Area | Status |
|------|--------|
| Phase 0 audit artifacts | Present under `v070/audit/` |
| Civilization governance modules | `governance/civilization/` |
| Explainability (3) | `attention/explainability/` |
| Observability (6 metrics + score) | `observability/v070/` |
| Governor wiring | Observational `civilization_observability` only |
| Stress scenarios (7) | `v070_runtime/simulations.py` |
| Horizons (5) | 24h / 7d / 30d / 90d / 180d |

## Gate

Run:

```bash
python3 -m pytest tests/v070/ tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
python3 -c "from observability.v070.cognitive_civilization_stability_score import evaluate_cognitive_civilization_stability as e; r=e(); print(r.civilization_score, r.gate_pass)"
python3 -c "from v070_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v070/reports/inter_sovereign_timeseries.json'))"
```

**Target:** `CognitiveCivilizationStabilityScore >= 0.90`

## Constraints honored

- No hive-mind, cognition merge, shared identity, autonomous diplomacy, sovereignty absorption
- Guardian and constitutional cognition preserved
- Civilization metadata does not override governor acceptance or salience
