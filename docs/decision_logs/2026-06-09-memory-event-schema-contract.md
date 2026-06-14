# 2026-06-09 Memory Event Schema Contract

## Decision

Create Phase 1B schema and contract artifacts before any TurboVec adapter or vector backend integration.

Artifacts define:

- Unified memory event schema.
- Recall evidence packet contract.
- Embedding sidecar metadata.
- Stable record id policy.
- Replay pointer policy.

## Reason

Phase 1A found that ASI has layered memory and replay infrastructure, but lacks the identity, provenance, embedding metadata, and replay semantics required for safe vector candidate recall.

These contracts allow a future vector backend to be implemented without inventing memory identity, recall provenance, embedding metadata, or replay semantics during implementation.

## Alternatives

- Implement TurboVec immediately. Rejected because readiness blockers remain.
- Store vectors anonymously. Rejected because Guardian and replay could not inspect provenance.
- Modify DMN append schema now. Rejected because Phase 1B is contract-only and must not change production behavior.
- Make TurboVec the default backend. Rejected because contracts must remain backend-neutral.

## Risks

- Schemas are not yet enforced by runtime.
- Existing historical records do not yet have stable ids, embedding sidecars, or replay pointers.
- Future implementation could diverge unless PR gates require schema compliance.
- JSON Schema can validate shape but not all semantic constraints, such as privacy class inheritance.

## Updated Readiness Estimate

Phase 1A score was 17 / 30.

After Phase 1B contract creation, estimated readiness is 21 / 30:

| Category | Estimate |
| --- | ---: |
| Architecture | 3 / 5 |
| Memory Schema | 4 / 5 |
| Replay Compatibility | 4 / 5 |
| Guardian Compatibility | 4 / 5 |
| Governance Compatibility | 4 / 5 |
| Synchronization Compatibility | 2 / 5 |

The score remains below implementation-ready because the contracts are not yet validated against examples, mapped to existing records, or enforced by runtime/replay/Guardian paths.

## Rollback

Rollback is documentation-only: remove or supersede the added docs and schemas with a new decision log entry. Do not delete this decision from history; preserve an audit-safe supersession record.

## Approval

User requested Phase 1B on 2026-06-09. Guardian classified the documentation-only/schema-only action as `ALLOW` with boundary level `OBSERVE_ONLY`.

## Recommended Next Phase

Phase 1C: Schema Validation Examples and Compatibility Mapping.

Recommended deliverables:

- Example valid memory events for text, sensor, somatic, system, agent, Guardian, governance, and replay events.
- Example recall evidence packet using `vector_backend = none`.
- Example embedding sidecar metadata with no real vector payload.
- Mapping from existing DMN/layered memory records to memory event wrappers.
- Validation commands that do not modify production behavior.
