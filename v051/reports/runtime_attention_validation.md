# Runtime Attention Validation — v0.5.1

**Generated:** 2026-05-19  
**Base:** v0.5.0-alpha ATTENTIONALLY STABLE

## Summary

Accelerated simulations exercise telemetry → kernel → pressure → recovery across **1h / 6h / 24h / 72h** windows. All routes use `AttentionKernel` with bounded queue and domain budgets.

## Validation matrix

| Window | Telemetry samples | Tick cycles | Gate |
|--------|-------------------|-------------|------|
| 1h | 30 | 15 | PASS (sim) |
| 6h | 90 | 45 | PASS (sim) |
| 24h | 200 | 120 | PASS (sim) |
| 72h | 400 | 240 | PASS (sim) |

## Checks

- No recursive attention loops (duplicate submission guard)
- Overload triggers decay + cooldown recovery
- Explainability coverage = 1.0 in clean sim evidence
- `RuntimeAttentionStabilityScore` ≥ 0.90

## Artifacts

- `v051/reports/runtime_attention_timeseries.json` — window scores and pressure tails
- `pytest tests/v051/ tests/v050/ -q`

## Constraints honored

Guardian doctrine, TruthGraph, Entropy, Isolation, PatchRegistry, replay semantics unchanged.
