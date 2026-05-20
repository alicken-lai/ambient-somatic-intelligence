# Replay Boundary Integrity

Score evaluation for freeze does not ingest live replay windows. Replay-aligned metrics come from in-memory collectors (`collect_replay_*_metrics`) with deterministic fixtures.

No replay contamination observed in civilization regression path (consistent with `v07x_freeze/testing/runtime_contamination_report.md`).

**Replay boundary:** PASS
