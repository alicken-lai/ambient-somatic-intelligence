# TurboVec Risk Register

Phase: 1G Vector Backend Proof-of-Concept Approval Packet  
Date: 2026-06-09

| # | Risk | Description | Severity | Likelihood | Mitigation | Detection Method | Rollback Trigger |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Vector recall treated as truth | Candidate similarity is mistaken for verified memory truth. | High | Medium | Evidence docs state candidate-only; safety defaults forbid decisions/actions. | Tests assert `decision_allowed=false` and `action_allowed=false`; PR review checks wording. | Any code or docs imply similarity authorizes truth or action. |
| 2 | Privacy filter bypass | Backend returns sensitive or restricted records despite filters. | High | Medium | Fail closed for privacy filters; require privacy filter tests. | Test restricted/sensitive records are excluded. | Any privacy filter failure returns candidates. |
| 3 | Governance filter bypass | Backend returns deleted, archived, or disallowed governance states. | High | Medium | Fail closed for governance filters; enforce tombstone and governance state tests. | Contract tests for excluded governance states. | Any governance filter failure returns candidates. |
| 4 | Anonymous vector ingestion | Vectors are stored without source record id or sidecar metadata. | High | Medium | Require stable `record_id`, `content_hash`, embedding sidecar, privacy class, retention policy. | Test ingestion rejects missing sidecar metadata. | Backend accepts anonymous vectors. |
| 5 | Backend lock-in | ASI starts depending directly on TurboVec APIs. | Medium | Medium | Keep backend behind `RecallBackend`; no runtime default. | Search for direct imports outside approved file. | Direct backend imports appear in runtime, Guardian, replay, kernel, or DMN paths. |
| 6 | Recall evidence drift | Backend output diverges from recall evidence schema. | High | Low | Validate evidence against schema in tests. | JSON Schema validation. | Evidence fails schema validation. |
| 7 | Schema mismatch | TurboVec sidecar metadata cannot map to memory event schema. | Medium | Medium | Use existing embedding sidecar schema; reject nonconforming records. | Tests for sidecar validation and missing fields. | Adapter requires schema changes to pass basic ingestion. |
| 8 | Performance obsession over auditability | Optimization pressure weakens replay, provenance, or filters. | High | Medium | Acceptance criteria prioritizes auditability over speed. | PR review checks audit fields and filters before benchmark claims. | Benchmark code bypasses evidence or filters. |
| 9 | Hidden dependency behavior | Dependency performs unexpected IO, persistence, or network access. | High | Low | Non-production only; document dependency; no production default; inspect behavior. | Dependency review and test sandbox observations. | Dependency requires network, service, or hidden persistence for tests. |
| 10 | Inconsistent similarity scores | Scores vary across runs and cannot be replayed. | Medium | Medium | Use deterministic test data; record model/backend/version. | Repeated test runs and evidence comparison. | Scores cannot be reproduced for the same fixed inputs. |
| 11 | Tombstone bypass | Tombstoned records are returned by vector index. | High | Medium | Tombstone checks before return; tests verify exclusion. | Tombstone test with otherwise high-similarity record. | Tombstoned candidate appears in recall results. |
| 12 | Replay reconstruction failure | Recall cannot be reconstructed from evidence. | High | Medium | Require replay references and provenance for every candidate. | Evidence audit checks record ids, scores, backend, timestamp, filters, provenance. | Candidate lacks provenance or replay reference. |

## Risk Posture

The future PoC is acceptable only if it reduces retrieval uncertainty without reducing governance control. Any increase in capability that reduces auditability or control is a regression.

