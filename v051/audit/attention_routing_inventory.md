# Attention Routing Inventory — v0.5.1 (Read-Only)

| Route | Source | Adapter | Kernel op | Domain cap |
|-------|--------|---------|-----------|------------|
| R1 | `telemetry` category=attention | `TelemetryAttentionAdapter` | submit/tick | 0.10 external |
| R2 | `telemetry` category=governance | `GovernanceAttention` | submit | 0.25 governance |
| R3 | `telemetry` category=somatic | `SomaticRuntimeBridge` | submit | 0.30 somatic |
| R4 | Guardian BLOCK/REVIEW | `GuardianAttentionBridge` | submit (boost) | 0.25 governance |
| R5 | Memory recall tags | `PrecursorMemoryBridge` | submit (capped) | 0.15 memory |
| R6 | Overload recovery | `OverloadRecovery` | tick + decay | budget release |

## Kernel wiring

All runtime routes delegate to **`AttentionKernel`** (`attention/kernel/attention_kernel.py`) with:

- `KernelSalienceEngine` for scoring
- `SalienceCompetition` for winner selection
- `AttentionRouter` + `FocusAllocator` for focus slots

Legacy root modules (`salience_engine.py`, `priority_allocator.py`) remain backward-compatible; runtime paths use kernel only.
