# Replay Stability Report

## Observability replay

Triple invocation of `evaluate_civilization_lineage_integrity_v2()` yields identical `lineage_integrity_score` (0.954016).

## Governor replay

1000-cycle `govern_target` sequence repeated twice — governed salience vectors **bit-identical** (`replay_deterministic: true`).

**Replay stability:** PASS
