# DMN Memory Governance Review

Phase: 1G.5 DMN Memory Governance Review  
Date: 2026-06-09  
Status: Design review only. No DMN behavior, Guardian behavior, replay behavior, runtime behavior, dependencies, or APIs are changed by this document.

## Purpose

This review asks whether ASI has enough governance around long-term DMN memory evolution before any future compressed vector backend is considered.

The core question is:

```text
What turns accumulated events into governed experience?
```

The governed memory path must be:

```text
Raw Events
-> Memory
-> Experience
-> Knowledge
-> Governance-Aware Recall
```

TurboVec remains paused. This review does not implement TurboVec and does not create adapters.

## Repository Evidence

The repository already contains several partial mechanisms:

| Area | Evidence |
| --- | --- |
| Durable DMN records | `memory/dmn.jsonl` stores append-only records with `content`, `source`, `tags`, and `timestamp`. |
| Memory layer doctrine | `docs/MEMORY_LAYER_POLICY.md` defines short-term, working, DMN, replay, and governance memory. |
| Formal ontology | `memory/ontology/layer_definition.py` defines L1 episodic, L2 instinct, L3 skill, and L4 strategic memory. |
| Promotion rules | `memory/ontology/promotion_rules.py`, `promotion_engine.py`, `promotion_guard.py`, and `promotion_chain_validator.py` define sequential promotion and audit records. |
| Decay rules | `memory/ontology/decay_rules.py`, `decay_engine.py`, and `memory/memory_kernel.py` define time, inactivity, contradiction, failed reuse, TTL, and archive behavior. |
| Consolidation signals | `memory/evolution/pattern_miner.py` and `attention/consolidation/attention_memory_store.py` mine recurring patterns and consolidate attended targets. |
| Replay and lineage trace | `observability/cognitive_trace_v2/lineage_data/lineage.jsonl` preserves parent/root event chains for trace events. |
| Memory event contract | `docs/MEMORY_EVENT_SCHEMA.md` and `schemas/memory_event.schema.json` define record identity, replay pointers, privacy class, governance state, and lineage fields. |
| Conflict doctrine | Governance modules such as `governance/reality/truth_conflict_analysis.py` and `governance/temporal/continuity_conflict.py` surface divergence without forced merge. |
| Sync doctrine | `docs/ASI_GOVERNANCE_CONSTITUTION.md` requires local-first, minimum-disclosure, interruptible, replayable synchronization. |

## Current Governance Finding

ASI has strong local building blocks for governed memory, but the rules are not yet unified into one DMN-level lifecycle.

The strongest areas are promotion guardrails and decay primitives. The weakest areas are cross-node synchronization, conflict handling across memory records, and consolidation that preserves full replayability.

## How Events Become Experience

The approved governance model should treat memory evolution as a sequence of governed transformations:

1. Raw event capture creates append-only evidence.
2. Classification assigns layer, source, tags, privacy, retention, and governance state.
3. Working memory uses the evidence locally during a task.
4. Promotion proposes durable memory only when recurrence, anomaly value, governance value, replay value, human confirmation, or Guardian review justifies it.
5. Consolidation may summarize many related records into a learned pattern, but only with lineage and replay references preserved.
6. Decay reduces retrieval priority or recommends archive; governance memories decay more conservatively than sensor or scratchpad memories.
7. Conflict review allows contradictory records to coexist until confidence, source quality, or human/Guardian review resolves them.
8. Governance-aware recall returns memories with provenance, confidence, privacy, lineage, replay pointers, and no automatic authority to decide or act.

## DMN Governance Readiness Score

| Category | Score | Current State | Gap | Recommendation |
| --- | ---: | --- | --- | --- |
| Promotion | 4 / 5 | Sequential promotion rules, chain validation, governance approval IDs, verifier requirements, and audit trails exist in `memory/ontology`. | DMN append records do not consistently carry promotion rationale, source layer, target layer, or candidate IDs. | Adopt `docs/DMN_PROMOTION_POLICY.md` as the repository-level rule and require wrapper metadata before promoted DMN records are indexable. |
| Decay | 3 / 5 | Layer TTLs, decay half-lives, contradiction penalties, inactivity decay, failed reuse decay, archive recommendations, and reports exist. | Existing DMN records are append-only and do not consistently carry retention class, freshness score, or importance score. | Use decay as recall ranking and archive recommendation, not silent deletion; require retention metadata on future memory events. |
| Consolidation | 2 / 5 | Pattern mining and attention consolidation exist as local mechanisms. | No unified DMN policy defines how many raw records become one learned pattern while preserving replayability. | Consolidate into derived records with `consolidated_from`, replay pointers, and source sample manifests. |
| Lineage | 3 / 5 | Event traces have parent/root IDs; schemas require lineage fields; wrapper dry runs can preserve source pointers. | Historical DMN records lack universal `record_id`, `source_node`, `parent_record_ids`, and replay pointers. | Use stable wrapper IDs and require lineage fields for promotion, consolidation, synchronization, and recall. |
| Conflict Resolution | 2 / 5 | Reality, temporal, value, meaning, and intent modules surface conflicts without forced merge. Promotion validation blocks active contradictions. | No DMN-wide conflict record schema or review workflow exists for contradictory memories. | Allow coexistence by default; resolve with confidence/source weighting and human/Guardian review for governance-impacting conflicts. |
| Cross-Node Sync | 1 / 5 | Governance constitution states local-first, minimum-disclosure, replayable sync. Sync-sensitive fields exist in Phase 1B/1E contracts. | No reviewed Home Hermes / Office Hermes DMN sync policy or implementation exists. Historical records often lack source node identity. | Do not sync raw sensitive DMN content by default; define node trust, privacy classes, replay preservation, and conflict handling before implementation. |

Overall readiness: 17 / 30.

## Critical Gaps

| Priority | Gap | Risk | Complexity |
| --- | --- | --- | --- |
| Critical | Cross-node DMN sync is policy-only. | Home Hermes and Office Hermes could diverge, duplicate, overwrite, or over-disclose memory. | High |
| Critical | DMN-level conflict resolution is not unified. | Contradictory memories may be recalled without explanation or review status. | Medium |
| Major | Consolidation is not governed end to end. | Learned patterns could destroy replayability if raw lineage is lost. | High |
| Major | Historical DMN records lack stable metadata. | Old records need wrappers before governed recall, embedding, or sync. | Medium |
| Minor | Existing ontology and storage layer names differ. | Contributors may confuse cognitive layers with file storage layers. | Low |

## Highest-Risk Area

The highest-risk area is cross-node synchronization combined with conflict resolution.

Without source-node identity, privacy class, lineage, and replay pointers, synchronization can convert local experience into unreviewed shared belief. That would weaken governance and make future vector recall harder to audit.

## Future Roadmap

1. Adopt the Phase 1G.5 policies as review doctrine.
2. Extend future memory event wrappers with full lineage and conflict fields before indexing or sync.
3. Create a non-production DMN conflict register.
4. Create a dry-run-only cross-node sync manifest for Home Hermes and Office Hermes.
5. Add validation examples for promoted, decayed, consolidated, conflicted, and synced memory events.
6. Only after those policies are validated, resume TurboVec PoC planning.

## TurboVec Status

TurboVec remains paused.

This review improves governance readiness but does not authorize TurboVec implementation, adapters, production vector indexing, or cross-node embedding synchronization.
