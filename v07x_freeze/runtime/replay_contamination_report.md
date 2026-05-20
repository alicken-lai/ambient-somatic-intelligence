# Replay Contamination Report

**Audit date:** 2026-05-20

## Replay hint handling

- `CognitiveGovernor.govern_target()` passes `replay_hint` to constitutional guard and arbitration
- v07x observability uses `scope="advisory"` — replay hints do not bypass constitution
- `governance/reality/replay_alignment.py` and `observability/v071/replay_alignment_metrics.py` bound replay influence

## Test isolation

- Replay impersonation tests live in v062 (`tests/v062/test_replay_impersonation.py`) — passed in regression stack
- v07x score tests use controlled replay hints; no cross-test replay state

## Historical P1 continuity

Union replay continuity ≥0.95 remains **UNPROVEN** at P1 level (see `freeze/unproven_claims.md`). This does **not** block v07x civilization layer gates, which use synthetic/advisory evaluation paths.

**Replay contamination (v07x layer): PASS**
