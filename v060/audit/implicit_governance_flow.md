# Implicit Cognitive Governance Flow (v0.6.0 audit)

**Base:** v0.5.4-alpha CALIBRATED + ANTICIPATORY  
**Date:** 2026-05-19

## Flow

1. **CalibratedAttentionActivation** (v0.5.4) produces confidence-capped salience.
2. **CognitiveGovernor** arbitrates domain claims via **ArbitrationEngine** (single depth).
3. **SalienceArbitrator** applies fairness weighting; **SovereigntyLimits** blocks monopolization.
4. **SomaticAuthority** and **ReplayAuthority** apply bounded boosts (read-only replay).
5. **UncertaintyOverride** dampens salience when uncertainty exceeds threshold.
6. **GovernedAttentionActivation** submits governed targets to **AttentionKernel**.
7. **Observability v060** collects metrics; **CognitiveGovernanceStabilityScore** gates at 0.90.

## Invariants

- Advisory-only governance — no autonomous execution or deterministic authority.
- Guardian policy unchanged; no recursive governance loops.
- v0.5.0–v0.5.4 attention, calibration, and forecasting preserved.
