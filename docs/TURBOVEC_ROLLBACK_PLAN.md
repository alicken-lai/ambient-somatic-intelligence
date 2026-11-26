# TurboVec Rollback Plan

Phase: 1G Vector Backend Proof-of-Concept Approval Packet  
Date: 2026-06-09

## Rollback Principle

TurboVec must be removable without changing DMN memory, Guardian behavior, Replay behavior, runtime behavior, kernel behavior, or governance doctrine.

## Rollback Actions

Rollback must be possible by:

1. Removing `memory/vector/turbovec_backend.py`.
2. Removing `tests/test_turbovec_backend.py`.
3. Removing `examples/recall_evidence/turbovec_recall_evidence.example.json`.
4. Removing `docs/TURBOVEC_EXPERIMENTAL_BACKEND.md`.
5. Removing optional dependency declaration if added in a later approved phase.
6. Keeping memory event records untouched.
7. Keeping DMN memory untouched.
8. Keeping Guardian untouched.
9. Keeping runtime untouched.
10. Keeping replay artifacts untouched unless the later phase creates explicit experimental artifacts.

## Rollback Triggers

Rollback is triggered when:

- TurboVec becomes required for tests outside its experimental test file.
- Evidence export fails schema validation.
- Privacy or governance filters do not fail closed.
- Tombstoned records can be returned.
- Anonymous vectors are accepted.
- TurboVec is imported outside approved experimental files.
- Any production behavior changes.
- Any protected zone is modified without approval.

## Post-Rollback Verification

After rollback:

- Backend-neutral tests must still pass.
- Existing in-memory proof harness tests must still pass.
- No TurboVec imports remain.
- DMN memory remains unchanged by the rollback.
- Guardian, runtime, replay, and kernel files remain unchanged.

