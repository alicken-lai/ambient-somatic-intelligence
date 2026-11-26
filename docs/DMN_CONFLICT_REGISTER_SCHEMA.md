# DMN Conflict Register Schema

Phase: 1G.7 DMN Governance Contract Schemas  
Date: 2026-06-10  
Status: Contract schema only. No conflict register implementation is created.

## Purpose

`schemas/dmn_conflict_register.schema.json` defines a backend-neutral record for unresolved or resolved DMN memory conflicts.

The schema prevents automatic conflict resolution by making unresolved state valid and explicit.

## Required Sections

| Section | Purpose |
| --- | --- |
| `conflict_id` | Stable conflict identity. |
| `conflict_type` | Observation, interpretation, source, time, governance, or sync conflict. |
| `status` | Open, under review, resolved, or archived. |
| `claims` | Competing claims with record IDs, source nodes, confidence, evidence, and replay pointers. |
| `affected_record_ids` | Records affected by the conflict. |
| `source_nodes` | Nodes that contributed conflicting claims. |
| `confidence_summary` | Confidence range and explanatory summary. |
| `resolution` | Resolution state, method, chosen claim, rationale, time, and reviewer. |
| `audit` | Decision log, validation status, and `no_mutation`. |

## Conflict Types

Allowed values:

- `observation_conflict`
- `interpretation_conflict`
- `source_conflict`
- `time_conflict`
- `governance_conflict`
- `sync_conflict`

## Resolution Model

`resolution.resolution_status = unresolved` is valid.

The schema does not force a winner. A conflict can remain open while both claims stay recallable with provenance.

## Safety Default

`audit.no_mutation` must be `true`.

This schema does not implement a conflict register or modify memory behavior.
