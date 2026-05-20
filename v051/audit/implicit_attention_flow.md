# Implicit Attention Flow — v0.5.1 Runtime Audit (Read-Only)

**Base:** v0.5.0-alpha ATTENTIONALLY STABLE  
**Date:** 2026-05-19

## Flow

```
TelemetryRecord → TelemetryAttentionAdapter → AttentionTarget
       ↓
Guardian risk / governance event → GuardianAttentionBridge → escalation salience
       ↓
Somatic signal → SomaticRuntimeBridge → RuntimeSomaticAttention
       ↓
Memory tags → PrecursorMemoryBridge → RuntimeMemoryActivation (bounded)
       ↓
AttentionKernel.submit → SalienceCompetition → AttentionQueue
       ↓
AttentionKernel.tick → FocusAllocator → focused targets
       ↓
RuntimeAttentionExplainer + observability/v051 metrics
       ↓
RuntimeAttentionStabilityScore (gate ≥ 0.90)
```

## Implicit risks (documented, not introduced)

| Risk | Mitigation in v0.5.1 |
|------|----------------------|
| Unbounded telemetry → queue flood | `max_queue` on kernel + pressure controller |
| Opaque runtime salience | `runtime_attention_explainer` + hard-fail on opaque count |
| Memory activation without cap | `RuntimeMemoryActivation.max_activations` |
| Recursive attention loops | adapters do not re-submit focused targets |
| Governance bypass | `GuardianAttentionBridge` read-only; no policy mutation |

## Non-goals (frozen)

- Autonomous execution / skill generation
- Ontology doctrine changes
- TruthGraph / Entropy / Isolation / PatchRegistry redesign
