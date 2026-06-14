# Backend-Neutral Recall Interface

Phase: 1E Backend-Neutral Recall Interface Specification  
Status: Non-production interface specification.

This directory is reserved for backend-neutral candidate recall contracts.

It does not define a production default backend. It does not implement a vector engine. It does not alter DMN memory, Guardian, Replay, runtime, kernel, or existing recall behavior.

## Boundary

Recall backends may produce candidate records and evidence. They must not authorize decisions or actions.

Required safety defaults:

- `guardian_visible = true`
- `decision_allowed = false`
- `action_allowed = false`
- `no_decision_made = true`

## Interface

`base.py` defines:

- `RecallFilter`
- `RecallQueryContext`
- `RecallProvenance`
- `RecallResult`
- `RecallBackend`

Backends are expected to:

1. Accept governed memory records and embedding sidecar metadata.
2. Apply privacy and governance filters before returning candidates.
3. Return candidate results with provenance and replay pointers.
4. Export recall evidence packets compatible with `schemas/recall_evidence.schema.json`.
5. Fail closed for privacy and governance filters.
6. Tombstone records instead of physically deleting by default.

## Non-Goals

- No backend implementation.
- No adapter implementation.
- No dependency installation.
- No production integration.
- No runtime behavior change.

