# DMN Sidecar Supersession Policy

Phase: 1G.11 DMN Metadata Sidecar Review and Approval Workflow  
Date: 2026-06-13  
Status: Policy only. No production supersession is performed.

## Purpose

Supersession lets a newer sidecar replace an older sidecar without deleting history or rewriting DMN memory.

## Rules

1. Supersession creates a review record; it does not edit the old sidecar.
2. The older sidecar remains audit-visible.
3. The newer sidecar must reference the old sidecar.
4. The old review must record `superseded_by_sidecar_id`.
5. The new review should record `supersedes_sidecar_id`.
6. Superseded sidecars must not be used for future sync or indexing.
7. Supersession does not imply the successor is approved.

## Valid Reasons

- More precise source node classification.
- Improved privacy classification.
- Replay pointer repaired.
- Lineage metadata improved.
- Earlier sidecar had a classification error.
- Policy changed and sidecar needs a new review context.

## Audit Requirement

Supersession must preserve:

- old sidecar ID;
- new sidecar ID;
- reason;
- reviewer;
- decision time;
- no-DMN-mutation audit flag.
