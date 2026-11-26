# DMN Sidecar Revocation Policy

Phase: 1G.11 DMN Metadata Sidecar Review and Approval Workflow  
Date: 2026-06-13  
Status: Policy only. No production revocation is performed.

## Purpose

Revocation withdraws a prior approval when later evidence shows the sidecar should not be used.

## Revocation Triggers

- Privacy classification was too permissive.
- Replay pointer was invalid.
- Source hash no longer matches the intended record.
- Conflict discovered after approval.
- Sync risk changed.
- Human owner withdraws approval.
- Guardian reviewer identifies a safety issue.

## Rules

1. Revocation must be represented by a review record.
2. Revocation must not delete the old sidecar or DMN record.
3. `review_state` should be `revoked`.
4. `revocation.revoked` must be true.
5. `approved_for_indexing` and `approved_for_sync` must be false.
6. Revoked sidecars must be blocked from future indexing and sync proposals.

## Audit Requirement

Revocation must preserve:

- revocation reason;
- revocation time;
- revoking reviewer;
- affected sidecar ID;
- decision log reference;
- no-DMN-mutation flag.
