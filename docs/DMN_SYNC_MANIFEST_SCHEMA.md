# DMN Sync Manifest Schema

Phase: 1G.7 DMN Governance Contract Schemas  
Date: 2026-06-10  
Status: Contract schema only. No synchronization is authorized.

## Purpose

`schemas/dmn_sync_manifest.schema.json` defines a backend-neutral manifest for dry-run or future governed cross-node DMN synchronization.

The schema describes what would be allowed, excluded, filtered, conflicted, replay-referenced, and reviewed. It does not perform sync.

## Required Sections

| Section | Purpose |
| --- | --- |
| `manifest_id` | Stable manifest identity. |
| `source_node` and `target_node` | Node boundary for Home Hermes / Office Hermes review. |
| `sync_mode` | Dry run, proposal, approved transfer, rejected, or archived. |
| `sync_scope` | Summary, evidence, governance, embedding sidecar, or full-record-prohibited scope. |
| `allowed_records` | Records that would be eligible, with replay pointers. |
| `excluded_records` | Records blocked by privacy or governance filters. |
| `conflict_candidates` | Conflicts that must not be auto-resolved. |
| `privacy_filters_applied` | Privacy filters used during evaluation. |
| `governance_filters_applied` | Governance filters used during evaluation. |
| `trust_model` | Source/target trust and review requirements. |
| `audit` | Decision log, validation status, mutation count. |

## Sync Modes

Allowed values:

- `dry_run`
- `proposal`
- `approved_transfer`
- `rejected`
- `archived`

Phase 1G.7 validates only `dry_run`.

## Safety Default

Top-level `no_mutation` is required and must be `true`.

`audit.actual_records_mutated` must be `0`.

## Validation Scope

`examples/dmn_governance/sync_manifest_home_to_office.example.json` validates against this schema.

The manifest remains synthetic and does not authorize real Home Hermes to Office Hermes synchronization.
