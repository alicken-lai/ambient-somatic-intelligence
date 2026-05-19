# Stability Scoring Formula Report (v0.4.5)

## Composite

```
stability_score = Σ (dimension[d] × DIMENSION_WEIGHTS[d])
```

All dimensions and weights are clamped to `[0, 1]`. `GATE_THRESHOLD = 0.85`.

## Dimension derivation (post-reconciliation)

Each dimension is `1 - pressure`, where **pressure** is the **maximum** of gate-aligned metrics (not kind-mean):

| Dimension | Pressure = max(…) | Weight |
|-----------|-------------------|--------|
| truth_consistency | truth_duplicate_nodes, truth_checksum_divergence, truth_conflict_pressure | 0.22 |
| patch_pressure | patch_leakage, patch_unwire_failure | 0.18 |
| mutation_pressure | mutation_rate, mutation_hook_pressure, mutation_denial_rate | 0.14 |
| orphan_pressure | orphan_pressure | 0.12 |
| circular_coupling | circular_coupling | 0.14 |
| stale_state | stale_state_critical, stale_state_pressure | 0.12 |
| runtime_reproducibility | explicit or `1 - min(1, patch_p + mutation_p×0.3)` | 0.08 |

## Gate pass (boolean)

```
gate_pass =
  score >= 0.85
  AND truth_duplicate_nodes == 0
  AND patch_leakage == 0
  AND circular_coupling == 0
  AND stale_state_critical == 0
```

## Previous bug (pre-v0.4.5)

- `truth_pressure` included `_kind_mean(DRIFT) × 0.5` → false penalty from `truth_orphan_nodes` on edgeless graphs.
- `patch_pressure` included `_kind_mean(PATCH)` → operational churn penalized clean leakage=0 graphs.
- `mutation_pressure` kind-mean → denied attempts inflated score when `mutation_rate` was 0.

## Explainability

- `build_stability_breakdown()` — weighted tree with per-metric children.
- `explain_stability()` — dominant failure by weighted gap to 1.0.
- `evaluate_semantics_alignment()` — checks evidence vs dimension consistency.
