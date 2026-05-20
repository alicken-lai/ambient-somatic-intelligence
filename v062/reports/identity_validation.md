# v0.6.2 Identity Stress Validation

**Version:** 0.6.2  
**Date:** 2026-05-19

## Scenarios exercised

1. Replay impersonation attempts — blocked at identity layer (`replay_impersonation`)
2. Synthetic cognition injection — salience capped at 0.65
3. Cross-runtime identity drift — continuity anchors verified
4. Provenance corruption — authority multiplier 0.0
5. Cognition fragmentation — signature sprawl guard
6. Unstable replay inheritance — replay bounded multiplier
7. Continuity breakdown — lineage chain verification

## Verification

- Provenance remains traceable via `ProvenanceRecord`
- Replay distinguishable from runtime (`CognitionOrigin`)
- Fragmentation bounded (`FragmentationGuard`)
- Continuity anchors stable (`ContinuityAnchor`)
- Synthetic cognition bounded (`SyntheticProjectionBoundary`)
- Identity coherence preserved (`IdentityCoherence`)
- Identity reasoning explainable (`IdentityReasoning`, `ProvenanceExplainer`)

## Gate

See `provenance_timeseries.json` for 24h/7d/30d/90d window scores.
