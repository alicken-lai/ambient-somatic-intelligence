# External Drift Surface Map — v0.6.5C

## Drift surfaces under soak

| Surface | Risk | Mitigation |
|---------|------|------------|
| Karpathy SKILL.md content | Medium | `DoctrineDriftDetector` + `DriftAccumulationDetector` |
| IDE export copies | Medium | `ExportContainment` + advisory headers |
| Runtime session persistence | High | `DoctrinePersistenceDecay` (weight decay) |
| Cursor rule injection | High | `CursorRuntimeGuard` |
| Provenance gaps | Medium | `RuntimeProvenanceValidator` |

## Soak horizons monitored

- 24h — smoke  
- 7d — weekly drift  
- 30d — monthly accumulation  
- 90d / 180d — long-horizon decay validation  

## Boundary

External content may inform advisory hints; it must not become canonical truth or override governance acceptance.
