# DMN Lineage Policy

Phase: 1G.5 DMN Memory Governance Review  
Date: 2026-06-09  
Status: Policy only. No DMN behavior is changed by this document.

## Purpose

Lineage is the memory system's ability to answer:

```text
Where did this memory come from, how did it change, and why is it being recalled?
```

Lineage must survive promotion, consolidation, synchronization, and recall.

## Existing Lineage Evidence

The repository already has partial lineage support:

- `observability/cognitive_trace_v2/lineage_data/lineage.jsonl` stores event IDs, parent event IDs, root event IDs, generations, source subsystems, and actions.
- `schemas/memory_event.schema.json` requires `lineage.parent_record_ids`, `root_record_id`, `derived_from`, and `transformation`.
- `docs/STABLE_RECORD_ID_POLICY.md` defines stable record IDs for wrapped historical records.
- `docs/RECALL_EVIDENCE_CONTRACT.md` requires recall provenance and source metadata.

Historical `memory/dmn.jsonl` records usually do not contain this full lineage.

## Required Lineage Fields

Future DMN wrappers and memory events should preserve:

| Field | Meaning |
| --- | --- |
| `parent_record_ids` | Immediate source records. |
| `root_record_id` | Earliest known root memory or event. |
| `derived_from` | Source paths, logs, files, decision logs, or records used to derive the memory. |
| `consolidated_from` | Source set used by consolidation. |
| `promoted_from` | Candidate or lower-layer record that led to promotion. |
| `synced_from` | Source node and sync manifest that introduced the record. |
| `replay_pointer` | Replay source for reconstruction. |
| `content_hash` | Stable evidence hash. |
| `source_node` | Origin node such as Home Hermes or Office Hermes. |
| `transformation` | Classification, promotion, consolidation, decay, archive, sync, or recall. |

## Lineage Rules

1. Promotion must add `promoted_from` and preserve all parent lineage.
2. Consolidation must add `consolidated_from` and a sample manifest.
3. Synchronization must add `synced_from` and never overwrite origin node identity.
4. Recall evidence must include record IDs and source metadata for every returned candidate.
5. Archive and tombstone records must preserve lineage.
6. If lineage is unknown, use an explicit `unknown` marker and explain the missing source.
7. Lineage gaps lower readiness for embedding, sync, and governance recall.

## Lineage Across Lifecycle

```text
Raw Event
-> Memory Event Wrapper
-> Promotion Candidate
-> Promoted DMN Record
-> Consolidated Pattern
-> Synced Summary
-> Recall Evidence
```

At each step, the next artifact must reference the prior artifact rather than replace it.

## Historical DMN Handling

Historical DMN records should not be rewritten. They may be wrapped with:

- synthetic stable `record_id`;
- source file and line pointer;
- content hash;
- source node placeholder if unknown;
- replay-unavailable reason when no replay pointer exists.

These wrappers can improve governance without violating append-only memory doctrine.
