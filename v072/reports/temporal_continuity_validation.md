# Temporal Continuity Validation (v0.7.2)

**Gate:** `CognitiveTemporalContinuityScore` ≥ 0.90

## Validation checklist

- [x] Phase 0 audit artifacts present (`v072/audit/`)
- [x] `governance/temporal/` phases 1–5 modules
- [x] Explainability: 3 temporal explainers
- [x] Observability v072: 6 metrics + composite score
- [x] Timeseries: 6 horizons + 7 stress scenarios
- [x] Governor wiring: `temporal_continuity_observability` after reality alignment
- [x] Tests: `tests/v072/` (10 areas)

## Execution

```bash
python3 -m pytest tests/v072/ tests/v071/ tests/v070/ tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
python3 -c "from observability.v072.cognitive_temporal_continuity_score import evaluate_cognitive_temporal_continuity as e; r=e(); print(r.temporal_continuity_score, r.gate_pass)"
```
