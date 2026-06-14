# DMN Metadata Sidecar Policy

Phase: 1G.10 Non-Mutating DMN Metadata Sidecar Proposal  
Date: 2026-06-10  
Status: Policy and proposal-only metadata. No DMN memory is mutated.

## Purpose

Historical DMN records lack governance metadata coverage. Metadata sidecars provide a way to propose missing metadata without rewriting `memory/dmn.jsonl`.

Sidecars are not approved truth. They are reviewable proposals attached by source reference.

## Attachment Model

Each sidecar attaches to one historical DMN record using:

- `source_file`
- `source_line`
- `source_hash`
- `source_record_id`

The original append-only DMN line remains unchanged.

## Sidecar Scope

Sidecars may propose:

- source node classification;
- record type;
- privacy class;
- retention policy;
- governance state;
- replay pointer status;
- lineage status;
- Guardian review status;
- sync eligibility;
- review priority.

Sidecars must not:

- rewrite historical content;
- approve themselves;
- authorize sync;
- authorize TurboVec indexing;
- claim Guardian approval unless the source record explicitly supports it.

## Source Node Classification

If no explicit source node exists, use a conservative unknown value:

- `unknown_local`
- `unknown_home`
- `unknown_office`
- `unknown_external`

The Phase 1G.10 proposals default to `unknown_local` for historical local DMN samples because the audit source is the local repository, but this is still a proposal requiring review.

## Privacy Classification

Privacy class must be conservative:

- telemetry and operational records default to `sensitive`;
- governance and phase summaries default to `internal`;
- uncertain records may use `unknown`;
- raw sensitive content must not be copied into reports.

## Review Rules

Human review is required when:

- privacy is sensitive or unknown;
- source node is unknown;
- replay pointer is missing or unknown;
- governance state requires review;
- Guardian status is derived rather than explicit;
- the record could become sync eligible.

Priority is high when a record is sync-relevant but replay or privacy is uncertain, when telemetry is sensitive, or when Guardian-related records lack explicit Guardian review IDs.

## Safety Defaults

Every sidecar must include:

- `audit.no_mutation = true`
- `audit.proposal_only = true`
- `review.approved = false`

This policy preserves append-only DMN doctrine while making metadata gaps visible and reviewable.

## TurboVec Status

TurboVec remains paused. Metadata sidecars improve governance readiness but do not authorize vector indexing, adapters, or compressed recall backends.
