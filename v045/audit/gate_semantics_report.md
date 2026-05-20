# Gate Semantics Report (v0.4.5)

## Stability gate

| Signal | Role | Fails gate when |
|--------|------|-----------------|
| Composite score | Weighted sum of 7 dimensions | `< 0.85` |
| duplicate_truth_count | Evidence | `> 0` |
| patch_leakage | Evidence | `> 0` |
| circular_recursion | Evidence | `> 0` |
| stale_state_critical | Evidence | `> 0` |

## Semantics alignment gate (v0.4.5)

| Check | Meaning |
|-------|---------|
| critical_evidence_clean | All four critical evidence fields at zero |
| score_matches_critical_evidence | If critical clean, score must be ≥ 0.85 |
| patch_dimension_matches_leakage | patch_pressure ≈ 1 iff patch_leakage = 0 |
| truth_dimension_matches_duplicates | truth_consistency ≈ 1 iff no duplicates |
| explainability_consistent | No dominant failure when gate passes |

**PASS** when alignment score ≥ 0.95 and no mismatches.

## Clean graph doctrine

See `docs/doctrine/clean_graph_definition.md`.

Edgeless truth graphs (test baseline) must not emit orphan truth pressure. Module inventory orphan scans are out of scope for the clean-graph fixture (`orphan_modules=None` → zero pressure).

## Fixture validity

`tests/v042/conftest.py` provides:

- `fresh_root` — timestamps for state/DMN within OK window
- `truth_graph` — single immutable baseline node
- `entropy_controller` — stale detector bound to `fresh_root`

Gate tests must use all three; default `EntropyController()` without `fresh_root` can add stale **warning** pressure (non-critical) but previously also skewed dimensions via kind-mean.
