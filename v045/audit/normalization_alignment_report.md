# Normalization Alignment Report (v0.4.5)

**Date:** 2026-05-19

## Shared normalizer

Both stability and operational paths use `observability.v04.metric_normalizer`:

| Function | Stability | Operational |
|----------|-----------|-------------|
| `clamp01` | dimension bounds | dimension bounds |
| `dimension_from_pressure` | entropy dimensions | indirect via custom dim fns |
| `pressure_max` | gate metric subsets | N/A (runtime evidence struct) |
| `metric_value` | entropy report lookup | N/A |

## Gate-aligned pressure selection (stability)

`stability_score._dimension_pressures` uses **max-of-named-metrics**, not kind-mean:

| Dimension | Metrics |
|-----------|---------|
| truth_consistency | truth_duplicate_nodes, truth_checksum_divergence, truth_conflict_pressure |
| patch_pressure | **patch_leakage**, **patch_unwire_failure** |
| mutation_pressure | mutation_rate, mutation_hook_pressure, mutation_denial_rate |

Non-gate patch metrics (`patch_churn`, `patch_age_pressure`, `patch_active_pressure`) do not enter patch_pressure after alignment.

## Patch leakage normalization fix

**Before:** `leakage = inactive_but_registered / total` → 1.0 on fully restored registry.  
**After:** `leakage = min(1, active_count/15)` if `active_count > 0` else `0.0`.

Aligns with `docs/doctrine/clean_graph_definition.md`: churn/age do not fail gate when restore health is zero.

## Operational path

`operational_stability_score` consumes `OperationalRuntimeEvidence` (simulation output), not live `EntropyReport`. No duplicate normalization of patch churn; patch gate uses integer `patch_leakage` and `patch_unwire_repro_rate` from phase simulators.

## Consistency check

| Check | Result |
|-------|--------|
| clean graph stability | 1.0 |
| clean graph operational | 1.0 |
| semantics alignment | 1.0 |
| `pressure_max` excludes churn when leakage=0 | PASS (`tests/v045/test_metric_normalizer.py`) |
