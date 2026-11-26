# TurboVec Readiness Assessment

Phase: 1A Memory Architecture Design Review  
Date: 2026-06-09  
Assessment type: Design readiness only. No implementation performed.

## Readiness Summary

Overall readiness: 17 / 30

TurboVec is suitable for a controlled proof of concept as an optional candidate recall layer. It is not ready for production adoption until ASI standardizes memory event metadata, recall provenance, replay pointers, and Guardian recall evidence review.

## Category Scores

| Category | Score | Current State | Gap | Recommendation |
| --- | ---: | --- | --- | --- |
| Architecture | 3 / 5 | Layered memory exists (`dmn`, episodic, semantic, procedural, governance, scratchpad, archive). Memory kernel, layered store, recall script, index script, and agent memory all exist. | Recall/storage responsibilities are split across multiple paths with no single candidate recall contract. | Define a recall interface contract where TurboVec can provide candidates while existing lexical recall remains fallback and final ranking remains governed. |
| Memory Schema | 2 / 5 | DMN schema requires only `timestamp`, `source`, `tags`, `content`. Recall schema returns source, source type, content, tags, timestamp, confidence. Agent memory has richer metadata. | No universal `event_id`, `record_id`, `embedding_reference`, `replay_pointer`, `governance_state`, schema version, or privacy class. | Create a memory event schema and a sidecar embedding metadata schema before adapter work. |
| Replay Compatibility | 3 / 5 | Replay manifest maps DMN, layer files, action logs, Guardian records, governance audit, and cognitive lineage. Checksum chain exists. | Replay is source-level and phase-level, not guaranteed per recalled memory. Recall outputs lack replay pointers and checksum references. | Require every candidate recall result to include a replay reference or explicit `replay_reference_missing` reason. |
| Guardian Compatibility | 3 / 5 | Guardian classifies actions via policy and decision boundary routes. Approval/reflex logs are replayable. | Guardian does not receive a standardized recall evidence packet and cannot inspect vector backend details by contract. | Define Guardian-readable recall evidence with source record id, vector backend, embedding model, similarity, confidence, and `no_decision_made=true`. |
| Governance Compatibility | 4 / 5 | Governance constitution, memory policy, PR gate, Guardian change policy, and TurboVec boundaries exist. Promotion rules require governance and independent verifier for high layers. | Governance docs are new and not yet enforced by automation. Memory layer and ontology layer naming can confuse contributors. | Treat TurboVec work as medium risk until schemas are approved; require PR gate and decision log for all vector-related changes. |
| Synchronization Compatibility | 2 / 5 | Governance policy allows minimum-disclosure sync of summaries, embeddings/references, anomaly tags, confidence, replay references, and governance metadata. | No inspected implementation of `dmn_sync/heartbeat.py` or `docs/DMN_HEARTBEAT_SYNC.md`. Cross-node embedding sync is an assumption. | Design heartbeat sync separately and do not couple initial TurboVec PoC to cross-node sync. |

## Placement Decision

TurboVec should sit here:

```text
Durable Memory Corpus
-> Embedding Sidecar
-> TurboVec Candidate Recall
-> Governed Recall Ranking
-> Recall Evidence Packet
-> Guardian Review / Context Injection
-> Replay Log
```

TurboVec should not sit here:

- Inside DMN append.
- Inside memory promotion.
- Inside Guardian decision logic.
- Inside replay gate scoring.
- Inside runtime action execution.
- As a replacement for source records.

## Required Preconditions Before TurboVec Implementation

1. Define an ASI memory event schema.
2. Define a recall evidence packet schema.
3. Define stable record ids for existing and future memory records.
4. Define replay pointer format.
5. Define embedding sidecar metadata:
   - `record_id`
   - `content_hash`
   - `embedding_model`
   - `embedding_created_at`
   - `vector_backend`
   - `source_path`
   - `source_line`
   - `schema_version`
6. Define Guardian review expectations for recalled evidence.
7. Define fallback behavior when vector recall fails or returns low confidence.
8. Define stale index detection and rebuild policy.
9. Define encoding-quality screening for embedding candidates.

## Failure Modes To Guard Against

- Vector similarity treated as truth.
- Candidate recall presented as a Guardian decision.
- Candidate recall without source pointer.
- Candidate recall without replay pointer.
- Embedding stale or detached from source content hash.
- Cross-node sync of raw or sensitive data.
- Adapter added to one recall path while other recall paths diverge.
- Historical encoding corruption embedded without quarantine or quality flag.

## Readiness Verdict

Status: Not production ready.

Allowed next step: schema and evidence-contract design.

Blocked next step: TurboVec adapter implementation.

Reason: The architecture has enough structure for a safe design path, but lacks the metadata contract required to make compressed vector recall auditable, replayable, and Guardian-inspectable.

