# Civilization Memory Drift Map (v0.7.2)

## Bounded memory zones

| Zone | Retention cap | Decay |
|------|---------------|-------|
| Epoch anchor | 168h default | `MemoryDecayGovernor` |
| Civilization store | 128 records max | FIFO eviction |
| Federation peer | Advisory only | No permanent federation memory |

## Drift controls

- `BoundedCivilizationMemory` caps in-process records
- `ContinuityRetention` blocks retention beyond one year
- `ContinuityContaminationGuard` blocks false lineage bleed
