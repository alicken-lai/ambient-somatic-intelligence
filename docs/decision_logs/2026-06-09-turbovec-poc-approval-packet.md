# 2026-06-09 TurboVec PoC Approval Packet

## Decision

Create Phase 1G TurboVec proof-of-concept approval packet documents.

This phase approves only future planning for a strictly non-production TurboVec experimental backend. It does not implement, install, import, or configure TurboVec.

## Findings

- Phases 1A through 1F established schema, evidence, wrapper, interface, and in-memory proof harness prerequisites.
- A future TurboVec PoC can now be evaluated against written acceptance and rejection criteria.
- TurboVec must remain optional, disabled by default, backend-neutral, Guardian-visible, replay-aware, and removable.

## Risks

See `docs/TURBOVEC_RISK_REGISTER.md`.

Top risks:

- Vector recall treated as truth.
- Privacy or governance filter bypass.
- Anonymous vector ingestion.
- Recall evidence drift.
- Tombstone bypass.
- Replay reconstruction failure.

## Approved Future Scope

The next phase may create only:

- `memory/vector/turbovec_backend.py`
- `tests/test_turbovec_backend.py`
- `examples/recall_evidence/turbovec_recall_evidence.example.json`
- `docs/TURBOVEC_EXPERIMENTAL_BACKEND.md`

Any expansion requires new review.

## Rejected Current-Scope Actions

This phase did not and must not:

- Implement TurboVec.
- Install TurboVec.
- Import TurboVec.
- Create a TurboVec adapter.
- Change production recall behavior.
- Modify DMN, Guardian, Replay, runtime, kernel, or governance behavior.

## Readiness

Phase 1F reached 30 / 30 for starting a strictly non-production vector proof-of-concept planning phase.

Phase 1G converts that readiness into written approval criteria. This is still not production readiness.

## Recommended Next Phase

Phase 1H: TurboVec Experimental Backend PoC, only if the user explicitly approves implementation under the Phase 1G packet.

Before Phase 1H begins, confirm whether dependency installation is allowed or whether the PoC must use a stubbed/import-optional path.

## Rollback

Use `docs/TURBOVEC_ROLLBACK_PLAN.md`.

## Approval

User requested Phase 1G on 2026-06-09. Guardian classified the documentation-only approval packet action as `ALLOW` with boundary level `OBSERVE_ONLY`.

