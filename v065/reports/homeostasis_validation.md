# v0.6.5 Homeostasis Validation Report

**Version:** 0.6.5  
**Generated:** 2026-05-19

## Scope

Phases 0–11: audit, homeostasis core, stabilizers, explainability, observability v065, stress windows, tests, gate score.

## Validation checklist

- [x] `v065/audit/` — 3 artifacts
- [x] `governance/homeostasis/` — orchestrator + subsystems
- [x] `attention/explainability/` — homeostasis_reasoning, stabilization_explainer, recovery_breakdown
- [x] `observability/v065/` — 5 metrics + stability score
- [x] Governor wiring — post-metacognition advisory only
- [x] Simulated horizons — 24h/7d/30d/90d/180d

## Gate

Run:

```bash
python3 -m pytest tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ tests/v054/ tests/v053/ tests/v052/ tests/v051/ tests/v050/ -q
python3 -c "from v065_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v065/reports/stabilization_timeseries.json'))"
```

Confirm `evaluate_cognitive_homeostasis_stability().gate_pass` and `homeostasis_score >= 0.90`.

## Constraints

No autonomous self-repair, recursive self-modification, consciousness claims, or Guardian weakening.
