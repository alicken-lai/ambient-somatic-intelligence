# Recall Backend Contract

Phase: 1E Backend-Neutral Recall Interface Specification  
Date: 2026-06-09

## Backend Responsibilities

Every backend must:

1. Accept memory records with stable ids.
2. Accept embedding sidecar metadata when embeddings are used.
3. Apply privacy filters before returning candidates.
4. Apply governance filters before returning candidates.
5. Return only candidate recall results.
6. Include provenance for every returned candidate.
7. Include replay pointers when available.
8. Export recall evidence through the shared contract.
9. Support tombstone semantics.
10. Report capabilities and unsupported filter behavior.

## Prohibited Backend Behavior

Backends must not:

- Authorize decisions.
- Authorize actions.
- Modify DMN records.
- Promote memories.
- Override Guardian.
- Rewrite replay logs.
- Hide excluded records when exclusion is safety-relevant.
- Return tombstoned records by default.

## Required Capabilities Response

`capabilities()` should return:

- Backend name.
- Supported filter types.
- Unsupported filter types.
- Whether embeddings are required.
- Whether tombstones are supported.
- Whether evidence export is supported.
- Failure behavior.

## Healthcheck

`healthcheck()` must be read-only and return:

- `ok`
- `backend`
- `status`
- `details`

Healthcheck must not repair, rebuild, delete, or mutate backend state.

## Evidence Compatibility

All backends must produce evidence compatible with `schemas/recall_evidence.schema.json`.

Backends may add internal telemetry elsewhere in later phases, but the recall evidence packet is the Guardian-visible contract.

