# 2026-06-09 Backend Neutral Recall Interface

## Decision

Create Phase 1E backend-neutral recall interface specification artifacts.

This phase adds documentation, a non-production interface stub at `memory/vector/base.py`, and contract tests. It does not implement a backend adapter or change production recall behavior.

## Findings

- A backend-neutral interface can represent candidate recall without binding ASI to a specific vector engine.
- Evidence export can preserve Phase 1B safety defaults.
- Tombstone, filter, failure, and capabilities semantics can be expressed without production integration.
- Tests can verify importability, safety defaults, evidence shape, method existence, and backend neutrality without external services.

## Risks

- The interface is not yet integrated with existing recall paths.
- No production backend emits this evidence yet.
- Privacy and governance filters are specified but not enforced by a real backend in this phase.
- Tombstone semantics are specified but not backed by persistent storage in this phase.

## Readiness Score

Phase 1D estimate: 27 / 30.

After Phase 1E interface specification, estimated readiness is 29 / 30.

| Category | Estimate |
| --- | ---: |
| Architecture | 5 / 5 |
| Memory Schema | 5 / 5 |
| Replay Compatibility | 5 / 5 |
| Guardian Compatibility | 5 / 5 |
| Governance Compatibility | 5 / 5 |
| Synchronization Compatibility | 4 / 5 |

The score remains below proof-of-concept-ready because no backend-neutral dry-run implementation has executed against wrapped records through the interface.

## Recommended Next Phase

Phase 1F: Non-Production In-Memory Recall Backend Proof Harness.

Recommended constraints:

- No external vector engine.
- No TurboVec adapter.
- Use only in-memory synthetic/wrapped examples.
- Validate evidence export against schema.
- Validate privacy/governance fail-closed behavior.
- Do not alter production recall.

## Rollback

Rollback is documentation/interface-only. Remove or supersede the added files with a new decision log entry. Do not delete this decision from history.

## Approval

User requested Phase 1E on 2026-06-09. Guardian classified the backend-neutral interface/specification action as `ALLOW` with boundary level `OBSERVE_ONLY`.

