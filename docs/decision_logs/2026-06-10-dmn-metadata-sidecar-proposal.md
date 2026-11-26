# Decision Log: DMN Metadata Sidecar Proposal

Date: 2026-06-10  
Phase: 1G.10 Non-Mutating DMN Metadata Sidecar Proposal  
Status: Accepted as proposal-only artifact. No migration, sync, or implementation authorized.

## Decision

Create a metadata sidecar schema and generate proposal-only sidecars for the Phase 1G.9 historical DMN audit sample.

The sidecars attach by `source_line` and `source_hash` and do not rewrite `memory/dmn.jsonl`.

TurboVec remains paused.

## Created Files

- `schemas/dmn_metadata_sidecar.schema.json`
- `docs/DMN_METADATA_SIDECAR_POLICY.md`
- `tools/propose_dmn_metadata_sidecars.py`
- `reports/dmn_audit/dmn_metadata_sidecar_proposals.jsonl`
- `reports/dmn_audit/dmn_metadata_sidecar_coverage_report.md`
- `reports/dmn_audit/dmn_metadata_sidecar_review_queue.md`
- `tests/test_dmn_metadata_sidecar_proposals.py`

## Proposal Count

Generated 50 sidecar proposals from the Phase 1G.9 audit sample.

## Coverage Effect

Sidecars provide proposed coverage for:

- source node;
- privacy class;
- retention policy;
- replay pointer status;
- lineage status;
- Guardian review status;
- governance state;
- sync eligibility.

This improves governance metadata coverage as proposals only. It does not approve the metadata and does not mutate source records.

## Review Requirement

All generated sidecars remain unapproved by default.

High-priority review items include sensitive telemetry, Guardian-related records with derived status, sync-eligible governance records with missing replay pointers, and records with unknown source node.

## Readiness Score

Previous DMN Governance Readiness Score: 26 / 30.

Updated DMN Governance Readiness Score: 28 / 30.

The score increases because the repository now has a non-mutating proposal mechanism for historical metadata gaps. It does not reach production readiness because proposals still require human review and approval.

## Recommended Next Phase

Create a sidecar review and approval workflow specification:

1. approval states;
2. reviewer roles;
3. rejection/tombstone handling;
4. merge-free sidecar supersession;
5. validation gates before sync or indexing.
