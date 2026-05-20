# Implicit Attention Memory Consolidation Flow — v0.5.2

**Audit date:** 2026-05-19  
**Base:** v0.5.1-alpha RUNTIME-ATTENTIVE

## Flow (read-only inventory)

```
Telemetry / Somatic → AttentionKernel.submit
        ↓
AttentionTrace.append (bounded)
        ↓
SalienceHistory.record → SalienceReinforcement (capped)
        ↓
PrecursorMemory.match → PrecursorWeighting
        ↓
NoiseClassifier → BenignPatternMemory (suppress repeat noise)
        ↓
AttentionMemoryStore.consolidate (evict oldest)
        ↓
ConsolidatedAttentionActivation → kernel (cap activations)
        ↓
RuntimeAttentionMemoryBridge → explainability + metrics
```

## Replay / telemetry patterns

- Telemetry ingest uses existing `TelemetryAttentionAdapter` (v051); consolidation reads kernel state post-tick.
- No rewrite of append-only audit logs; consolidation store is separate bounded in-memory index.
- `memory/somatic/sensor_episode_store.py` remains persistent SSOT for long somatic episodes; `attention/somatic/somatic_episode_store.py` is attention-layer bounded cache.

## Guards

| Guard | Mechanism |
|-------|-----------|
| Runaway reinforcement | `REINFORCEMENT_CEILING` in `salience_reinforcement.py` |
| Unbounded traces | `AttentionTrace.max_entries` |
| Memory growth | `AttentionMemoryStore.max_entries` + eviction |
| Anomaly persistence | `AnomalyDecay` half-life decay |

## Preserved

v0.5.0 kernel, v0.5.1 runtime pressure/recovery, Guardian bridge, replay semantics unchanged.
