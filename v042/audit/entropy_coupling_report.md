# Entropy Coupling Report — v0.4.2

**Date:** 2026-05-18  
**Canonical SSOT:** `kernel.entropy.EntropyController`

## Implementation Overlap

| Layer | Path | Role | Overlap with SSOT |
|-------|------|------|-------------------|
| Kernel | `kernel/entropy/` | Truth/patch/coupling/mutation/orphan/stale observability | **Canonical** |
| Runtime | `runtime/entropy_controller/` | Context/memory dimension scoring, damping | 0.55 — different domain |
| Observability | `observability/drift_detection/` | Architecture drift remediation proposals | 0.25 — audit-time |
| Architecture | `graph_truth_layer/orphan_module_detector` | Static reachability orphans | 0.40 — feeds `OrphanPressure` |

## Coupling Edges (v0.4 wiring → entropy)

```
integration.v04_wiring
  └─► adapt_v04_wiring_connections()
        └─► kernel.entropy.CouplingPressure.record()
              └─► EntropyController.collect_metrics()
```

```
kernel.v04_stabilization
  └─► EntropyController + TruthGraph
        └─► kernel.integration_bus (health patch → compute())
```

## Deprecation Plan

1. **Keep** `kernel/entropy/EntropyController` as SSOT.
2. **Shim** `runtime/entropy_controller/kernel_adapter.py` re-exports canonical controller.
3. **Do not merge** runtime `EntropyScorer` into kernel — different metrics (memory growth vs truth integrity).
4. **Delegate** duplicate drift paths: `DriftDetector` retained; `TruthEntropyAdapter` is authoritative for truth-specific signals.

## Circular Coupling Risks

| Mechanism | Detection | Auto-fix |
|-----------|-----------|----------|
| Callback loops | `CouplingPressure.record_callback_loop()` | No |
| Patch recursion | `CouplingPressure.record_patch_recursion()` | No |
| Event feedback | `CouplingPressure.record_event_feedback()` | No |
| Import cycles | `record_circular_import()` + edge cycle DFS | No |

## Gate Dependencies

- Patch leakage observed via `PatchRegistry.entropy_snapshot()`
- Truth duplicates via `TruthEntropyAdapter` + `TruthGraph.detect_conflicts()`
- Stability score via `observability/v04/stability_score.py`
