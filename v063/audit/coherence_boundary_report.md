# v0.6.3 Coherence Boundary Report

**Version:** 0.6.3  
**Base:** v0.6.2 identity-bounded cognition

## Boundaries

| Boundary | Module | Rule |
|----------|--------|------|
| Contradiction | `contradiction_detector.py` | Conflicting confidence clusters raise pressure |
| Replay narrative | `replay_coherence.py` | Replay share capped vs live cognition |
| Constitutional | `constitutional_coherence.py` | Non-compliant verdicts raise pressure |
| Identity drift | `identity_drift.py` | Signature sprawl bounded per window |
| Fragmentation | `fragmentation_pressure.py` | Origin/signature sprawl contained |
| Decay | `coherence_decay.py` | Gentle score reduction at scale |

## Governor integration

`CognitiveGovernor` evaluates coherence **after** arbitration and identity checks, **before** final `GovernanceDecision` output. Low coherence dampens salience; severe incoherence may reject acceptance.

## Non-goals (preserved)

- No consciousness or personality simulation claims
- No autonomous execution or recursive identity mutation
- Guardian and constitutional immutability unchanged
