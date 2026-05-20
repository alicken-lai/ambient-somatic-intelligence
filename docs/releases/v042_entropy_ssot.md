# v0.4.2 Entropy SSOT Declaration

**Version:** `0.4.2-alpha`  
**Date:** 2026-05-18  
**Base:** v0.4.1-alpha (Truth Unification PASS)

## Canonical Location

```
kernel/entropy/EntropyController
```

All stabilization entropy metrics (truth, patch, coupling, mutation, orphan, stale) aggregate through this class.

## Package Layout

| Module | Responsibility |
|--------|----------------|
| `entropy_controller.py` | SSOT aggregator |
| `truth_entropy_adapter.py` | TruthGraph integrity |
| `patch_entropy_adapter.py` | PatchRegistry pressure |
| `mutation_tracker.py` | Mutation / hook pressure |
| `coupling_pressure.py` | Bus/callback/patch coupling |
| `orphan_pressure.py` | Module lifecycle classification |
| `stale_state_detector.py` | system_state / DMN / bus recency |
| `drift_detector.py` | Legacy drift (retained) |

## Runtime Adapter

`runtime/entropy_controller/` remains for **context economy** (compression, damping, load).

- `runtime/entropy_controller/kernel_adapter.py` — re-exports `kernel.entropy.EntropyController`
- `runtime/entropy_controller/__init__.py` — documents SSOT; exports `KernelEntropyController`

Do **not** use `EntropyScorer` for v0.4 stabilization gates.

## Integration Points

- `kernel/v04_stabilization.py` — boots `EntropyController`
- `integration/v04_kernel_adapter.py` — feeds coupling edges from wiring
- `observability/v04/stability_score.py` — gate-oriented stability composite

## Invariants

- Observable only — no auto-delete, no autonomous repair
- Guardian / ontology / telemetry scoring unchanged
- PatchRegistry remains reversible (v0.4.1)
