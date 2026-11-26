# Governed Memory Wrapper Schema

Phase: 1G.7 DMN Governance Contract Schemas  
Date: 2026-06-10  
Status: Contract schema only. No production behavior is changed.

## Purpose

`schemas/governed_memory_wrapper.schema.json` defines a backend-neutral wrapper around an existing `memory_event` object.

The wrapper makes DMN governance metadata enforceable without rewriting historical memory records or changing DMN append behavior.

## Required Sections

| Section | Purpose |
| --- | --- |
| `wrapper_id` | Stable wrapper identity. |
| `wrapper_type` | Promotion, decay, consolidation, conflict, sync, archive, or review state. |
| `memory_event` | Existing Phase 1B memory event object. |
| `governance_metadata` | Governance state, scores, privacy, retention, Guardian review, and review requirement. |
| `lineage` | Promotion, consolidation, derivation, sync, conflict, and parent record references. |
| `audit` | Replay pointer, decision log reference, validation state, and `no_mutation`. |

## Wrapper Types

Allowed values:

- `promoted`
- `decayed`
- `consolidated`
- `conflicted`
- `synced`
- `archived`
- `reviewed`

## Safety Default

`audit.no_mutation` is required and must be `true`.

This preserves Phase 1G.7 as non-production contract work. The schema does not authorize writes, sync, TurboVec, adapters, runtime changes, or Guardian behavior changes.

## Validation Scope

The Phase 1G.6 synthetic examples were updated to the new wrapper contract and validate against this schema:

- `promoted_memory.example.json`
- `decayed_memory.example.json`
- `consolidated_memory.example.json`
- `conflicted_memory_a.example.json`
- `conflicted_memory_b.example.json`

## Design Decision

The schema requires common governance fields even when they are not active for a wrapper type. Inactive fields may be empty strings or null scores. This makes validation simple and keeps downstream review logic predictable.
