# TurboVec PoC Approval Packet

Phase: 1G Vector Backend Proof-of-Concept Approval Packet  
Date: 2026-06-09  
Status: Approval packet only. TurboVec is not implemented, installed, imported, or configured by this document.

## Approval Recommendation

Recommendation: approve planning for a strictly non-production TurboVec experimental backend proof of concept, subject to the acceptance criteria in `docs/TURBOVEC_ACCEPTANCE_CRITERIA.md`.

This is not approval for production use. This is not approval to make TurboVec the default backend. This is not approval to modify DMN memory, Guardian logic, Replay logic, runtime behavior, kernel behavior, or governance behavior.

## Why A Real Compressed Vector Backend Is Justified

Phases 1A through 1F established the prerequisites for a replaceable candidate recall backend:

- Memory architecture was reviewed.
- Memory event and recall evidence schemas were defined.
- Embedding sidecar metadata was specified.
- Existing memory wrapper feasibility was validated.
- Backend-neutral recall interface was specified.
- In-memory proof harness exercised the interface end-to-end.

A real compressed vector backend is now justified only to test candidate recall quality and operational fit behind the backend-neutral interface.

## Approved Future Scope

The next phase may create only:

- `memory/vector/turbovec_backend.py`
- `tests/test_turbovec_backend.py`
- `examples/recall_evidence/turbovec_recall_evidence.example.json`
- `docs/TURBOVEC_EXPERIMENTAL_BACKEND.md`

The next phase must remain non-production, optional, disabled by default, and removable.

## What TurboVec May Do

TurboVec may:

- Act as an optional candidate recall backend.
- Ingest records only when stable `record_id` and embedding sidecar metadata exist.
- Return candidate record ids and similarity scores.
- Export recall evidence through the existing schema.
- Respect privacy filters, governance filters, and tombstones.
- Run only in tests or explicit non-production examples.

## What TurboVec Must Not Do

TurboVec must not:

- Become the default backend.
- Modify DMN append behavior.
- Bypass recall evidence.
- Bypass privacy filters.
- Bypass governance filters.
- Trigger Guardian action.
- Modify runtime behavior.
- Modify replay behavior.
- Create autonomous decisions.
- Store anonymous vectors.
- Ingest records without embedding sidecar metadata.

## Required Guardian Boundary

Guardian boundary must remain:

```text
ALLOW / OBSERVE_ONLY
```

If Guardian state is unavailable, assume:

```text
OBSERVE_ONLY
```

No action authorization is allowed.

## Required Tests

Future PoC tests must verify:

- Backend implements `RecallBackend`.
- Backend remains optional and disabled by default.
- Recall evidence validates against `schemas/recall_evidence.schema.json`.
- Safety defaults are preserved.
- Tombstoned records are excluded.
- Privacy and governance filters fail closed.
- Anonymous vector ingestion is rejected.
- No Guardian action is triggered.
- No DMN memory is mutated.
- No production runtime behavior changes.

## Approval Boundary

Approval is limited to an experimental proof of concept. Any expansion beyond the approved files or behavior requires a new decision log and Guardian/human review.

