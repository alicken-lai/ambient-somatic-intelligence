# DMN Sidecar Review Workflow

Phase: 1G.11 DMN Metadata Sidecar Review and Approval Workflow  
Date: 2026-06-13  
Status: Workflow design only. No production approval is performed.

## Purpose

This workflow defines how proposal-only DMN metadata sidecars can become reviewed, approved, rejected, superseded, revoked, or archived without mutating `memory/dmn.jsonl`.

Sidecar reviews do not approve real sidecars in this phase. The examples are synthetic dry runs.

## Approval States

| State | Meaning |
| --- | --- |
| `proposed` | Sidecar exists as proposal-only metadata. |
| `under_review` | A reviewer is evaluating the sidecar. |
| `approved` | Required gates passed for a specific future use. |
| `rejected` | Sidecar must not be used. |
| `requires_revision` | Sidecar needs changes before a decision. |
| `superseded` | Sidecar is replaced by a newer proposal or review. |
| `revoked` | Prior approval is withdrawn. |
| `archived` | Sidecar is retained for audit but not active. |

Only `approved` sidecars may be used by future indexing or sync proposals, and only for the use explicitly allowed by gates.

## Reviewer Roles

| Role | Responsibility |
| --- | --- |
| `owner` | Human project owner or delegated human authority. |
| `guardian_reviewer` | Observes safety and governance implications; may recommend, but does not authorize action alone. |
| `privacy_reviewer` | Reviews privacy class, redaction, and disclosure risk. |
| `sync_reviewer` | Reviews cross-node sync eligibility and trust model. |
| `technical_reviewer` | Reviews schema fit, hashes, source references, and replay/lineage metadata. |

## Required Reviewers

- Sensitive or sync-eligible records require `owner`.
- Privacy uncertainty requires `privacy_reviewer`.
- Cross-node sync requires `sync_reviewer`.
- Guardian reviewer may observe and recommend, but must not be the only authority.
- Technical reviewer is required when source hash, replay, lineage, or schema fit is uncertain.

## Workflow

1. Sidecar is generated as proposal-only metadata.
2. Review record is created with `review_state = under_review` or final dry-run state.
3. Reviewers record decisions, confidence, and conditions.
4. Approval gates are evaluated.
5. If gates pass, sidecar may be approved for a specific future use.
6. If gates fail, sidecar is rejected or marked `requires_revision`.
7. If a better sidecar replaces it, mark the older review `superseded`.
8. If later evidence invalidates approval, create a revocation review.

## Safety Rules

- Review records never mutate DMN memory.
- Review records never mutate proposal JSONL.
- Approval for indexing does not imply approval for sync.
- Approval for sync requires stricter gates than indexing.
- Rejected, superseded, revoked, and archived sidecars remain audit-visible.
- TurboVec remains paused.

## Non-Production Boundary

Phase 1G.11 defines static workflow artifacts only. It does not approve real sidecars, perform production indexing, perform cross-node sync, change Guardian behavior, or copy raw DMN content into review examples.
