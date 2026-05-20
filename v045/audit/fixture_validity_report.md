# Fixture Validity Report (v0.4.5)

## tests/v042/conftest.py vs runtime

| Fixture | Runtime equivalent | Valid for clean graph? |
|---------|-------------------|------------------------|
| `truth_graph` | Single `TruthNode` baseline, no edges | **Yes** — edgeless orphans exempt per doctrine |
| `fresh_root` | Isolated `tmp_path` state + DMN | **Yes** — avoids production stale files |
| `entropy_controller` | `EntropyController(stale_detector=StaleStateDetector(fresh_root))` | **Yes** |

## Mismatches resolved

1. **Truth orphan on edgeless graph** — adapter returned all nodes as orphans; stability kind-mean amplified. Fixed in `truth_entropy_adapter._orphan_truth_nodes`.
2. **Stale detector default root** — `StaleStateDetector()` defaults to repo root; tests without `fresh_root` read production `state/` and `memory/`. v042 tests always inject `fresh_root`.
3. **Patch registry singleton** — clean fixture has empty registry; leakage=0. Operational patch metrics no longer affect stability dimension.
4. **Module orphan inventory** — `collect_metrics(orphan_modules=None)` yields zero orphan metrics; full-repo scans are not part of clean-graph tests.

## boot_stabilization()

Uses default repo root for stale detection. Production score ~0.99 with warning-level stale pressure only. Gate tests should prefer `fresh_root` isolation.

## Recommendation

v045 tests assert: clean fixture + semantics alignment ≥ 0.95 + stability gate PASS.
