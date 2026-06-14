# In-Memory Recall Proof Harness

Phase: 1F Non-Production In-Memory Recall Backend Proof Harness  
Date: 2026-06-09  
Status: Non-production proof harness only.

## Purpose

This phase exercises the backend-neutral recall interface end-to-end without implementing TurboVec or any external vector backend.

The proof harness demonstrates:

```text
memory_event wrapper
-> embedding sidecar or synthetic embedding
-> backend-neutral add_record
-> query
-> recall result
-> recall evidence export
-> safety defaults
-> schema validation
```

## Backend

The backend lives at `memory/vector/in_memory_backend.py`.

Backend name:

```text
in_memory_proof_harness
```

It stores records only in process memory. It uses Python standard library cosine similarity over synthetic embeddings. It does not persist state, does not mutate existing memory, and is not imported by production recall paths.

## Supported Filters

Implemented filters:

- `privacy_class`
- `governance_state`
- `event_type`
- `modality`
- `tags`

Unsupported non-safety filters:

- `source_node`
- `retention_policy`
- `time_range`

Unsupported non-safety filters are documented in `capabilities()` and may fail open. Privacy and governance filters fail closed when backend support is disabled.

## Safety Defaults

Recall evidence preserves:

- `guardian_visible = true`
- `decision_allowed = false`
- `action_allowed = false`
- `no_decision_made = true`

The backend does not authorize action, does not trigger Guardian, does not modify DMN memory, and does not modify replay logs.

## Tombstones

The backend supports in-process tombstones. Tombstoned records are not returned by default recall.

This is not a deletion mechanism. It is proof of tombstone semantics only.

## Evidence

Static example evidence:

- `examples/recall_evidence/in_memory_recall_evidence.example.json`

Test-generated evidence is validated against:

- `schemas/recall_evidence.schema.json`

## Validation

Required targeted command:

```powershell
python -m pytest tests/test_recall_backend_contract.py tests/test_in_memory_recall_backend.py -q
```

## Non-Goals

- No TurboVec implementation.
- No TurboVec import.
- No vector adapter.
- No dependency installation.
- No production default.
- No runtime, Guardian, governance, replay, kernel, or DMN behavior change.

## Remaining Blocker

The interface has now been exercised in a non-production proof harness. The remaining blocker before a real vector proof of concept is a reviewed backend readiness gate that defines privacy review, stale sidecar handling, and acceptable benchmark evidence.

