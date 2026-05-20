# v0.6.5 Recovery Pressure Map

Maps homeostatic pressure sources to advisory recovery modules.

| Pressure signal | Module | Advisory output |
|-----------------|--------|-----------------|
| focus_entropy / budget_overrun | `attention_stabilizer` | competition rebalance, defer submissions |
| salience oscillation | `salience_damping` | advisory damp factor (not applied) |
| coherence_gap | `coherence_recovery` | pause submissions, provenance pass |
| reflection_load | `reflection_balancer` | defer secondary reflection |
| calibration_gap | `calibration_recovery` | tighten cap observation window |
| uncertainty_skew | `uncertainty_rebalancer` | increase uncertainty weight |

## Composite stabilization

`StabilizationState.composite_pressure()` feeds `CognitiveHomeostasis.evaluate_after_reflection()`.

Hard failures for gate: stabilization_uncontained, salience_oscillation_high, coherence_recovery_unready.
