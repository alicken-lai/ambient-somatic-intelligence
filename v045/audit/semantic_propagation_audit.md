# Semantic Propagation Audit (v0.4.5)

**Date:** 2026-05-19

## Propagation chain (stability)

```
EntropyController.compute()
  → PatchEntropyAdapter.observe(registry)
  → stability_score._dimension_pressures()  [pressure_max gate subsets]
  → compute_stability()                     [weighted dimensions + evidence]
  → explainable_stability / semantics_alignment
```

## Propagation chain (operational)

```
v045_runtime.simulations.run_all_phases()
  → OperationalRuntimeEvidence
  → compute_operational_stability()
  → test_simulated_phases_integrate_with_semantic_stability
        also calls evaluate_stability()  ← must not contradict operational PASS
```

## Failure propagation (pre-repair)

1. **Source:** `PatchRegistry.entropy_snapshot()` mis-reported leakage/unwire on restored handles.
2. **Adapter:** `patch_leakage=1.0`, `patch_unwire_failure=0.5` emitted into entropy snapshot.
3. **Stability:** `patch_pressure` dimension → 0.0; `runtime_reproducibility` → 0.0; score → 0.74.
4. **Evidence gate:** `patch_leakage` in evidence blocked `gate_pass` even when no active patches.
5. **Semantics alignment:** `critical_evidence_clean=False` → score 0.8.
6. **Explainability:** dominant_failure=`patch_pressure`.
7. **Runtime integration test:** `semantic.gate_pass is False`.

## Propagation after repair

| Stage | Clean graph | After v04 wiring + conftest teardown |
|-------|-------------|--------------------------------------|
| patch_leakage | 0.0 | 0.0 |
| patch_unwire_failure | 0.0 | 0.0 |
| stability score | 1.0 | 1.0 |
| gate_pass | true | true |
| semantics alignment | 1.0 | 1.0 |
| operational score | 1.0 | 1.0 |

## Files changed

- `kernel/entropy/patch_entropy_adapter.py`
- `kernel/wiring/patch_registry.py`
- `tests/v04/conftest.py`

## Non-changes (confirmed correct)

- `observability/v04/stability_score.py` — max-of-gate-metrics already correct
- `observability/v04/operational_stability_score.py` — no semantic drift vs stability for these failures
- Thresholds unchanged (stability 0.85, semantics 0.95, operational 0.90)
