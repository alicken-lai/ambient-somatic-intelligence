# Provenance Conflict Map

## Known mixing paths

| Path A | Path B | Risk | Mitigation |
|--------|--------|------|------------|
| Replay salience | Runtime submit | Impersonation | `replay_identity_boundary` |
| Forecast projection | Live telemetry | Synthetic bleed | `synthetic_projection_boundary` |
| Memory recall | Runtime focus | Ambiguous owner | `memory_provenance_guard` |
| Inherited context | Fresh runtime | Lineage drift | `cognition_lineage` + anchors |

## Resolution order

1. Constitutional guard (v0.6.1)
2. Provenance registration (v0.6.2)
3. Identity decision / damping
4. Cognitive arbitration
