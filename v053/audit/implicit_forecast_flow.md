# Implicit Attention Forecast Flow (v0.5.3 audit)

## Flow

1. **Ingest** — `RuntimeAttentionMemoryBridge.ingest_target` → salience history + precursor memory
2. **Project** — `SalienceProjection.project` from bounded `SalienceHistory`
3. **Trajectory** — `TrajectoryEstimator.estimate` (rising | stable | falling)
4. **Precursor** — `PrecursorForecast.forecast_from_signal` (memory match, no action)
5. **Pressure** — `SaliencePressureForecast.forecast` (runtime + memory composite)
6. **Replay** — `ReplayTrajectoryForecast.forecast` over `ForecastWindow`
7. **Explain** — `ForecastExplainer`, `PrecursorChainExplainer`, `UncertaintyExplainer`

## Non-goals (frozen)

- No autonomous planning or RL
- No deterministic predictions
- No recursive forecast amplification
- Guardian / ontology / TruthGraph unchanged

## SSOT references

- `memory/somatic/precursor_matcher.py` — detection-only precursor patterns
- `attention/consolidation/` — v0.5.2 memory layer
- `attention/runtime/` — v0.5.1 runtime bridge
