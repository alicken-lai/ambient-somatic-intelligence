# v0.6.3 Contradiction Conflict Map

**Version:** 0.6.3

## Pressure sources

| Source | Detector | Typical trigger |
|--------|----------|-----------------|
| Confidence spread | `ContradictionDetector` | max-min confidence > 0.45 |
| Domain sprawl | `ContradictionDetector` | >3 domains in short window |
| Replay dominance | `ReplayCoherence` | replay share > 55% |
| Constitutional mismatch | `ConstitutionalCoherence` | violations in verdict |
| Signature drift | `IdentityDrift` | >12 unique signatures / 20 records |
| Fragmentation | `FragmentationPressure` | signature guard breach |

## Resolution (advisory)

1. Damp governed salience via `CognitiveCoherence.damp_salience`
2. Surface reasons in `CoherenceVerdict.reasons`
3. Explain via `CoherenceReasoning` / `ContradictionExplainer` / `DriftBreakdown`
