# Runtime Authority Matrix — v0.6.5C

| Layer | May read external | May write external | May override acceptance |
|-------|-------------------|--------------------|-------------------------|
| Constitution | No | No | Yes (block) |
| Guardian | No | No | Yes (block) |
| Hermes canonical | No | Export preview only | No |
| CognitiveGovernor | Yes (advisory) | No | No |
| Runtime soak guards | Yes (scan) | No | **Never** |
| External skill mount | Source only | Mirror only | No |
| IDE (Cursor) | Export read | User-mediated | No |

## Observational wiring

`CognitiveGovernor._attach_runtime_observability()` adds `runtime_external_observability` after `external_advisory`. **Does not change** `accepted` or `governed_salience`.
