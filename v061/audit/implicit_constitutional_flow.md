# Implicit Constitutional Flow (v0.6.1 audit)

**Base:** v0.6.0-alpha GOVERNED COGNITIVE RUNTIME  
**Date:** 2026-05-19

## Flow

1. **ConstitutionalGuard** evaluates frozen rules (immutable at load).
2. **CognitiveGovernor** arbitrates only if constitutional verdict is compliant.
3. **ArbitrationEngine** (v0.6.0) coordinates salience, somatic, replay, uncertainty.
4. **GovernedAttentionActivation** submits governed targets to **AttentionKernel**.
5. **Observability v061** collects constitutional metrics; **ConstitutionalStabilityScore** gates at 0.90.

## Invariants

- Constitutional rules frozen at load — no runtime mutation.
- Guardian supremacy preserved; no autonomous execution or certainty claims.
- v0.5.x + v0.6.0 attention, calibration, forecasting, and governance preserved.
