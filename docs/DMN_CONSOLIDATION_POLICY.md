# DMN Consolidation Policy

Phase: 1G.5 DMN Memory Governance Review  
Date: 2026-06-09  
Status: Policy only. No DMN behavior is changed by this document.

## Purpose

Consolidation turns many related observations into a smaller learned pattern without destroying replayability.

The target question is:

```text
How do 1000 similar observations become 1 learned pattern?
```

The answer must never be "by deleting the 1000 observations and keeping only a summary."

## Existing Consolidation Evidence

The repository has local consolidation primitives:

- `memory/evolution/pattern_miner.py` mines recurring success and failure patterns from agent histories and memory layers.
- `attention/consolidation/attention_memory_store.py` consolidates attended targets into bounded memory records with salience and trace counts.
- `memory/memory_kernel.py` deduplicates recall results and can archive expired records.

These are useful building blocks, but they are not yet a full DMN consolidation policy.

## Consolidation Model

Consolidation creates a new derived record.

The derived record must preserve:

- summary of the learned pattern;
- sample count;
- source record IDs;
- source query or grouping criteria;
- confidence and confidence rationale;
- contradiction count;
- privacy class;
- replay pointers;
- source node set;
- governance state;
- reviewer or creator;
- creation timestamp.

## Required Lineage Fields

Every consolidated record should include:

- `consolidated_from`
- `parent_record_ids`
- `derived_from`
- `root_record_id`
- `source_node`
- `source_record_count`
- `sample_manifest_ref`
- `replay_pointer`
- `transformation`

## Replayability Requirements

Consolidation must be replayable at three levels:

| Level | Requirement |
| --- | --- |
| Summary replay | Explain the derived pattern and why it was created. |
| Sample replay | Provide representative source records or references. |
| Full lineage replay | Preserve enough source IDs, hashes, and manifests to reconstruct the source set. |

If full source replay is not possible, the derived record must state why and must not be used as governance memory without review.

## Consolidation Rules

1. Consolidation creates a derived memory; it does not rewrite historical records.
2. Raw source records may be archived after consolidation, but archive pointers must survive.
3. Consolidated records must not hide disagreement among source records.
4. Consolidation must preserve negative examples and failed cases when they are material.
5. Governance-impacting consolidation requires human or governance review.
6. Sensor-heavy consolidation should prefer summaries, statistics, and references over raw payload replication.
7. Consolidated memories are candidates for recall, not decision authority.

## Consolidation Risks

| Risk | Mitigation |
| --- | --- |
| Overgeneralization | Preserve sample size, scope, confidence, and known exceptions. |
| Lost replayability | Require lineage and replay pointers before archive. |
| Hidden conflict | Store contradiction count and conflict references. |
| Privacy leakage | Consolidate sensitive data into minimum-disclosure summaries. |
| False authority | Mark consolidated output as derived and candidate-only. |

## Approved Output Shape

```json
{
  "record_id": "mem_1.0.0_home-hermes_text_<hash>",
  "event_type": "text",
  "governance_state": "promoted",
  "summary": "Repeated observation: schema validation failures cluster around missing replay pointers.",
  "confidence": 0.82,
  "lineage": {
    "parent_record_ids": ["mem_a", "mem_b"],
    "root_record_id": "mem_a",
    "derived_from": ["memory/dmn.jsonl:100", "memory/dmn.jsonl:241"],
    "transformation": "consolidation"
  }
}
```

This example is illustrative only and does not create runtime behavior.
