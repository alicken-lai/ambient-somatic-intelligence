# v0.6.3 Coherence Validation Report

**Version:** 0.6.3  
**Generated:** 2026-05-19

## Scope

Long-horizon coherence stress across simulated windows: **24h, 7d, 30d, 90d, 180d**.

## Components validated

- `CognitiveCoherence` post-governance evaluation
- Contradiction, replay, constitutional, drift, fragmentation pressures
- `CognitiveCoherenceStabilityScore` gate (threshold **0.90**)
- Explainability: `coherence_reasoning`, `contradiction_explainer`, `drift_breakdown`

## Execution

```bash
python3 -m pytest tests/v063/ tests/v062/ tests/v061/ tests/v060/ tests/v054/ tests/v053/ tests/v052/ tests/v051/ tests/v050/ -q
python3 -c "from v063_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v063/reports/long_horizon_coherence_timeseries.json'))"
```

## Verdict

Run pytest and `evaluate_cognitive_coherence_stability()` to confirm gate **PASS**.
