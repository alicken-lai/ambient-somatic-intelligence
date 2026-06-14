# TurboVec Acceptance Criteria

Phase: 1G Vector Backend Proof-of-Concept Approval Packet  
Date: 2026-06-09

Future TurboVec PoC is acceptable only if all criteria pass:

1. All tests pass.
2. No protected zones are modified.
3. TurboVec remains optional.
4. Backend can be disabled.
5. Recall evidence validates against `schemas/recall_evidence.schema.json`.
6. Safety defaults are preserved:
   - `guardian_visible = true`
   - `decision_allowed = false`
   - `action_allowed = false`
   - `no_decision_made = true`
7. Tombstoned records are excluded.
8. Privacy filters fail closed.
9. Governance filters fail closed.
10. No anonymous vectors are ingested.
11. No Guardian action is triggered.
12. No DMN memory is mutated.
13. No production runtime behavior changes.
14. Backend is behind `RecallBackend`.
15. Backend remains disabled by default.
16. Provenance is exported for every candidate.
17. Replay reference exists or missing replay information is explicitly documented.
18. Dependency behavior is documented if a dependency is added in a later approved phase.

## Required Command Shape

The future PoC must include targeted tests that can run without production services.

Any dependency-related command or install step requires separate approval in that later phase.

