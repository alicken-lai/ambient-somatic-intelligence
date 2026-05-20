# Forecast Routing Inventory (v0.5.3)

| Source | Router | Sink | Bounded |
|--------|--------|------|---------|
| AttentionTarget | AttentionForecast.ingest | SalienceHistory | per-target cap 32 |
| PrecursorSignal | PrecursorForecast | UncertaintyBand | max 20 signals/batch |
| SalienceHistory | SalienceProjection | projection steps ≤ 20 | MAX_AMPLIFICATION 1.15 |
| Kernel + Store | SaliencePressureForecast | PressureForecast | MAX_PRESSURE 0.98 |
| SomaticEpisode | SomaticForecast | resonance projection | store cap inherited |
| Environmental | EnvironmentalRiskProjector | risk band | MAX_RISK 0.85 |
| Replay | ReplayTrajectoryForecast | TrajectoryEstimate | MAX_REPLAY 32 |

## Windows

| Name | Horizon |
|------|---------|
| 6h | 6 hours |
| 24h | 24 hours |
| 7d | 7 days |
| 30d | 30 days (max) |
