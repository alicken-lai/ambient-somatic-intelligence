# 2026-06-09 In-Memory Recall Proof Harness

## Decision

Create Phase 1F non-production in-memory recall backend proof harness.

This phase exercises the backend-neutral recall interface end-to-end using only process memory and synthetic embeddings. It does not implement TurboVec, create a vector adapter, or change production recall behavior.

## Findings

- `InMemoryRecallBackend` implements `RecallBackend`.
- Records can be added with synthetic embeddings.
- Query returns ranked candidates using standard-library cosine similarity.
- Required filters are supported for privacy class, governance state, event type, modality, and tags.
- Privacy and governance filters can fail closed when support is disabled.
- Tombstoned records are not returned by default recall.
- Exported evidence preserves Guardian-visible safety defaults and validates against `schemas/recall_evidence.schema.json`.

## Risks

- Backend is proof-only and not persistent.
- Synthetic embeddings are not representative of real embedding quality.
- Unsupported non-safety filters are documented but not enforced.
- No production recall path emits this backend's evidence.
- A real vector backend still needs privacy review, stale sidecar handling, benchmark evidence, and rollback policy.

## Readiness Score

Phase 1E estimate: 29 / 30.

After Phase 1F proof harness, estimated readiness is 30 / 30 for starting a strictly non-production vector proof-of-concept planning phase.

This does not mean production readiness. It means the governance/interface/schema prerequisites for a future replaceable backend proof of concept are satisfied.

## Recommended Next Phase

Phase 1G: Vector Backend Proof-of-Concept Approval Packet.

Recommended deliverables:

- Human-reviewed approval packet before any TurboVec adapter.
- Explicit PoC scope and rollback.
- Privacy review criteria.
- Stale sidecar handling requirements.
- Benchmark dataset rules using synthetic or non-sensitive examples.
- Evidence validation criteria.
- No production default.

## Rollback

Rollback is interface/proof-only. Remove or supersede the proof harness and tests with a new decision log entry. Do not delete this decision from history.

## Approval

User requested Phase 1F on 2026-06-09. Guardian classified the non-production proof harness action as `ALLOW` with boundary level `OBSERVE_ONLY`.

