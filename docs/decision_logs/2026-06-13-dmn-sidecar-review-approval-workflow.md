# Decision Log: DMN Sidecar Review and Approval Workflow

Date: 2026-06-13  
Phase: 1G.11 DMN Metadata Sidecar Review and Approval Workflow  
Status: Accepted as workflow and dry-run validation artifact. No real sidecars approved.

## Decision

Create a schema, policy documents, and synthetic dry-run examples for reviewing, approving, rejecting, revising, superseding, and revoking DMN metadata sidecars without mutating `memory/dmn.jsonl` or sidecar proposal JSONL files.

TurboVec remains paused.

## Created Files

- `schemas/dmn_sidecar_review.schema.json`
- `docs/DMN_SIDECAR_REVIEW_WORKFLOW.md`
- `docs/DMN_SIDECAR_APPROVAL_GATE.md`
- `docs/DMN_SIDECAR_SUPERSESSION_POLICY.md`
- `docs/DMN_SIDECAR_REVOCATION_POLICY.md`
- `examples/dmn_sidecar_review/approved_sidecar_review.example.json`
- `examples/dmn_sidecar_review/rejected_sidecar_review.example.json`
- `examples/dmn_sidecar_review/requires_revision_sidecar_review.example.json`
- `examples/dmn_sidecar_review/superseded_sidecar_review.example.json`
- `tests/test_dmn_sidecar_review_workflow.py`

## Review States

Defined states:

- proposed
- under_review
- approved
- rejected
- requires_revision
- superseded
- revoked
- archived

## Reviewer Roles

Defined roles:

- owner
- guardian_reviewer
- privacy_reviewer
- sync_reviewer
- technical_reviewer

## Gate Decisions

Only approved sidecars may be used by future indexing or sync proposals.

Indexing and sync gates are separate. Approval for indexing does not imply approval for sync.

Guardian reviewer may recommend and observe, but cannot authorize action alone.

Dry-run review records require explicit audit flags showing that no production sync, production indexing, TurboVec work, or raw DMN content copying occurred.

## Validation Results

Four dry-run review examples validate against `schemas/dmn_sidecar_review.schema.json`.

Existing sidecar proposal, historical audit, historical wrapper, and governance contract tests should remain passing because this phase adds static schema, docs, examples, and an optional static validation test only.

## Readiness Score

Previous DMN Governance Readiness Score: 28 / 30.

Updated DMN Governance Readiness Score: 29 / 30.

The score increases because proposal metadata can now be distinguished from reviewed, approved, rejected, superseded, and revoked metadata. It remains below production readiness because no real approval workflow is wired into runtime or sync.

## Recommended Next Phase

Phase 1G.12 - Cross-Node DMN Sync Contract Dry Run.

Still not TurboVec.
