# DMN Governance Contracts

Phase: 1G.7 DMN Governance Contract Schemas  
Date: 2026-06-10  
Status: Backend-neutral contract schemas only.

## Purpose

Phase 1G.7 turns Phase 1G.6 examples into formal JSON Schema contracts.

These contracts govern how synthetic examples represent promotion, decay, consolidation, conflict, and sync without creating production behavior.

## Created Schemas

| Schema | Purpose |
| --- | --- |
| `schemas/governed_memory_wrapper.schema.json` | Validates governed memory wrappers around existing memory events. |
| `schemas/dmn_conflict_register.schema.json` | Validates unresolved or resolved DMN conflict register entries. |
| `schemas/dmn_sync_manifest.schema.json` | Validates dry-run or future governed cross-node sync manifests. |

## Updated Examples

The five memory wrapper examples were updated from informal Phase 1G.6 shape into the governed wrapper contract shape.

The sync manifest example was updated with:

- `schema_version`
- `sync_scope`
- replay pointers on allowed records
- `trust_model`
- `audit`
- top-level `no_mutation = true`

## Validation Results

Validation passed:

- Schemas are valid Draft 2020-12 JSON Schemas.
- Five governed memory wrapper examples validate against `governed_memory_wrapper.schema.json`.
- The sync manifest validates against `dmn_sync_manifest.schema.json`.
- The test suite validates unresolved conflict state against `dmn_conflict_register.schema.json`.
- All contract tests pass with existing dependencies.

## Schema Decisions

1. Governed memory wrappers use `memory_event` as the canonical event payload.
2. Governance metadata is a wrapper concern, not a replacement for memory event identity.
3. `no_mutation = true` is enforced in wrapper audit and sync manifests.
4. Conflict resolution explicitly allows unresolved state.
5. Sync manifests require replay pointers for allowed records.
6. Full-record sync remains prohibited by policy unless a future reviewed phase changes the contract.
7. No schema requires TurboVec or any vector backend.

## Remaining Governance Gaps

- No production validator is wired into DMN writes.
- No real historical DMN wrapper validation has been performed.
- No persisted conflict register exists.
- No real cross-node sync implementation exists.
- No human approval workflow is connected to sync manifests.
- No Guardian runtime integration is changed by these contracts.

## Updated Readiness

Previous DMN Governance Readiness Score: 20 / 30.

Updated DMN Governance Readiness Score: 23 / 30.

TurboVec remains paused.

## Recommended Next Phase

Run a non-production historical DMN wrapper validation dry run:

1. Select a small sample of historical DMN records.
2. Create governed wrappers without modifying `memory/dmn.jsonl`.
3. Validate wrappers against the new schemas.
4. Report metadata gaps, privacy gaps, replay gaps, and sync eligibility.
5. Keep TurboVec paused until historical wrapper validation passes.
