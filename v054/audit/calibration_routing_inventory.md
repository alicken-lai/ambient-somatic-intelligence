# Calibration Routing Inventory (v0.5.4)

| Source | Router | Sink |
|--------|--------|------|
| `AttentionForecast.projections` | `ForecastConfidenceCalibrator` | Calibrated bands |
| `AttentionMemory` | `CalibratedAttentionActivation` | `AttentionKernel.submit` |
| `SomaticEpisode` | `SomaticConfidenceCalibrator` | Somatic confidence report |
| `PrecursorSignal` | `PrecursorReliability` | Reliability score |
| Bridge evidence | `evidence_from_calibrated_forecaster` | `CalibrationStabilityScore` |

## Preserved (unchanged)

- Guardian, TruthGraph, Entropy controller, PatchRegistry
- v0.5.0 kernel, v0.5.1 runtime, v0.5.2 consolidation, v0.5.3 forecasting
