# Recall Tombstone Policy

Phase: 1E Backend-Neutral Recall Interface Specification  
Date: 2026-06-09

## Policy

Deletion should prefer tombstone semantics.

A tombstoned record must not be returned by default recall.

Physical deletion requires separate governance approval.

## Tombstone Requirements

A tombstone event must include:

- `record_id`
- `reason`
- `timestamp`
- `created_by`
- `source_backend`
- `replay_pointer` when available

## Backend Responsibilities

Backends must:

- Implement `tombstone(record_id, reason)`.
- Exclude tombstoned records by default.
- Keep tombstone events auditable.
- Report tombstone support in `capabilities()`.

## Recall Evidence

If a tombstoned record is excluded, recall evidence should list it in `excluded_records` when the record was otherwise a candidate.

## Physical Deletion

Physical deletion is not part of the backend-neutral recall interface.

Physical deletion requires:

- Explicit governance approval.
- Replay impact assessment.
- Memory integrity audit.
- Decision log entry.

