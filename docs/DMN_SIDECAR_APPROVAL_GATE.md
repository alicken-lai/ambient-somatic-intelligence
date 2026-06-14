# DMN Sidecar Approval Gate

Phase: 1G.11 DMN Metadata Sidecar Review and Approval Workflow  
Date: 2026-06-13  
Status: Gate specification only. No production gate is installed.

## Purpose

This document defines when a reviewed sidecar can be used by future indexing or sync proposals.

## Indexing Gate

A sidecar may be used for future indexing only when all are true:

- `review_state = approved`
- `privacy_gate_passed = true`
- `retention_gate_passed = true`
- `replay_gate_passed = true` or `replay_not_applicable = true`
- `lineage_gate_passed = true` or `lineage_not_applicable = true`
- `indexing_gate_passed = true`
- `audit.approved_for_indexing = true`
- `audit.no_dmn_mutation = true`
- `audit.production_indexing_performed = false` during this dry run
- `audit.turbo_vec_paused = true`

Indexing approval does not approve TurboVec. It only means a future indexing proposal may cite the sidecar as reviewed metadata.

## Sync Gate

A sidecar may be used for future cross-node sync only when all are true:

- `review_state = approved`
- `privacy_gate_passed = true`
- `sync_gate_passed = true`
- `guardian_gate_passed = true`
- `audit.approved_for_sync = true`
- `approval_gates.unresolved_conflict_exists = false`
- human owner approval exists in `reviewer_roles`
- sync reviewer approval exists in `reviewer_roles`
- `audit.production_sync_performed = false` during this dry run

## Guardian Boundary

Guardian reviewer may observe and recommend. Guardian review alone must not authorize sync or indexing.

## Gate Notes

All required gate booleans must be present even when a gate is not applicable. Non-applicability is represented by explicit conditions such as `replay_not_applicable`, `lineage_not_applicable`, or decision conditions explaining why the gate remains false.

## Failure Handling

If any required gate fails:

- indexing use must be blocked;
- sync use must be blocked;
- review state should be `rejected` or `requires_revision`;
- reason and remediation conditions must be recorded.

## Dry-Run Example Outcomes

- Approved governance sidecar: approved for indexing only, not sync.
- Rejected telemetry sidecar: rejected for sync and indexing due to sensitivity and missing replay.
- Requires revision sidecar: cannot be used until source/privacy/replay gaps are addressed.
- Superseded sidecar: replaced by a newer proposal and inactive for future use.
