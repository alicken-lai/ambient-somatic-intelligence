# Memory Architecture Review

Phase: 1A Memory Architecture Design Review  
Date: 2026-06-09  
Scope: Design review only. No TurboVec implementation, adapters, production code, runtime behavior, Guardian logic, governance code, replay code, kernel code, or DMN behavior were changed.

## Executive Finding

ASI has a real layered memory architecture, but it is not yet ready for a compressed vector backend as a governed production path.

TurboVec should sit as a candidate recall backend behind the recall interface, fed by existing durable memory records and returning candidate record references plus similarity evidence. It must not sit inside DMN append, memory promotion, Guardian decision logic, or replay gates.

The current architecture can support a proof of concept, but production adoption is blocked by missing unified memory event metadata, incomplete recall provenance, no standard embedding reference field, no per-recall replay pointer, and split recall paths.

## Repository Evidence Reviewed

- `memory/dmn.jsonl`
- `memory/schema.json`
- `memory/recall_schema.json`
- `memory/index.json`
- `memory/episodic/records.jsonl`
- `memory/semantic/records.jsonl`
- `memory/procedural/records.jsonl`
- `memory/governance/records.jsonl`
- `memory/scratchpad/records.jsonl`
- `memory/memory_kernel.py`
- `memory/ontology/*.py`
- `memory/somatic/*.py`
- `agents/memory.py`
- `scripts/memory_classify.py`
- `scripts/memory_store.py`
- `scripts/memory_recall.py`
- `scripts/memory_index.py`
- `scripts/memory_integrity_audit.py`
- `replay/data_catalog/source_inventory.md`
- `replay/data_catalog/replay_manifest.json`
- `guardian/policy.yaml`
- `guardian/decision_boundary.yaml`
- `scripts/guardian_check.py`
- `architecture/bus_decomposition/event_schema.py`
- `telemetry/core/telemetry_schema.py`
- `observability/trace_schema.py`
- `observability/cognitive_trace_v2/causal_trace_schema.py`
- `docs/ASI_GOVERNANCE_CONSTITUTION.md`
- `docs/MEMORY_LAYER_POLICY.md`
- `docs/TURBOVEC_INTEGRATION_PLAN.md`

## Current Memory Storage Locations

| Location | Current Role | Notes |
| --- | --- | --- |
| `memory/dmn.jsonl` | Append-only durable DMN memory | Minimal schema: `timestamp`, `source`, `tags`, `content`. Current count observed: 1,498 non-empty records. |
| `memory/episodic/records.jsonl` | Layered episodic memory | Classified records with `_classified_layer` and `_source_line`. Current count observed: 328. |
| `memory/semantic/records.jsonl` | Layered semantic memory | Stable concepts, identity, architecture, summaries. Current count observed: 28. |
| `memory/procedural/records.jsonl` | Layered procedural memory | Operational know-how. Current count observed: 1; one record showed encoding/parse fragility during review. |
| `memory/governance/records.jsonl` | Layered governance memory | Incidents, Guardian-related records, policy decisions. Current count observed: 30. |
| `memory/scratchpad/records.jsonl` | Transient memory | Empty in current checkout. |
| `memory/archive/*.jsonl` | Cold or archived memory | `scratchpad_archived.jsonl` contains archived telemetry-derived records. |
| `memory/index.json` | Inverted index summary | Built from layered memory, current build timestamp 2026-05-13. It is stale relative to the current DMN count. |
| `state/agents/*/memory/entries.jsonl` | Per-agent local memory | Agent-local entries with category, confidence, uses, layer, entry_id, outcome counters, and contexts. |
| `logs/actions.jsonl` and `logs/checksums.jsonl` | Action and integrity memory for replay | Used by replay manifest and memory integrity audit. |
| `guardian/*.jsonl` and `guardian/**/*.json` | Guardian memory and safety evidence | Approvals, reflexes, incidents, audits, health, baseline, simulation, dream, approval packet. |
| `replay/data_catalog/*` | Replay catalog and manifest | Defines source inventory, phases, schema mappings, and integrity coverage. |

## Current Memory Layers

### Short-Term Memory

Current actor: conversational context, active tool outputs, and local working context in the current Codex session.

Repository evidence: this is not persisted as a dedicated repository memory layer. It exists outside repo storage until something is intentionally written to DMN or docs.

### Working Memory

Current actor: files inspected during a task, temporary assumptions, active plans, and possibly `memory/scratchpad/records.jsonl` when populated.

Repository evidence: `memory/scratchpad/records.jsonl` exists but is currently empty; `memory/memory_kernel.py` defines scratchpad TTL as 24 hours and low recall weight.

### Long-Term Memory

Current actors:

- `memory/dmn.jsonl`
- `memory/episodic/records.jsonl`
- `memory/semantic/records.jsonl`
- `memory/procedural/records.jsonl`
- `memory/governance/records.jsonl`
- `memory/archive/*.jsonl`
- Agent-local `state/agents/*/memory/entries.jsonl`

DMN is the durable append-only project memory. Layered records provide classification and retrieval structure.

### Replay Memory

Current actors:

- `replay/data_catalog/replay_manifest.json`
- `replay/data_catalog/source_inventory.md`
- `replay/reports/*`
- `logs/actions.jsonl`
- `logs/checksums.jsonl`
- `guardian/approvals.jsonl`
- `guardian/reflex.jsonl`
- `governance/audit/*.jsonl`
- `observability/cognitive_trace_v2/lineage_data/lineage.jsonl`

Replay is supported by source catalogs, timeline logs, checksums, and schema mappings. It is not yet uniformly attached to each memory recall result.

### Governance Memory

Current actors:

- `memory/governance/records.jsonl`
- `docs/ASI_GOVERNANCE_CONSTITUTION.md`
- `docs/MEMORY_LAYER_POLICY.md`
- `docs/PR_REVIEW_GATE.md`
- `docs/GUARDIAN_CHANGE_POLICY.md`
- `docs/decision_logs/*.md`
- `guardian/policy.yaml`
- `guardian/decision_boundary.yaml`
- `guardian/approvals.jsonl`
- `governance/audit/*.jsonl`

Governance memory exists as both durable data and repository doctrine.

## Memory Lifecycle

Current lifecycle observed:

1. Event or task occurs.
2. A record is appended to `memory/dmn.jsonl`, logs, Guardian artifacts, or agent-local memory.
3. `scripts/memory_classify.py` can classify DMN records into layer files without modifying the original DMN file.
4. `scripts/memory_store.py` can write directly to a layer, update `memory/index.json`, and optionally append backward-compatible DMN records.
5. `scripts/memory_recall.py` searches layered memory, logs, MemPalace, and system state using lexical/tag/layer weighting.
6. `memory/memory_kernel.py` provides a more comprehensive recall/store/scoring/decay/TTL/dedup system, but it is not the only recall path.
7. Replay artifacts can reconstruct timelines using the replay manifest and source inventory.
8. Guardian and governance logs provide safety evidence for action boundaries.

## Memory Promotion Rules

Two promotion models exist:

1. Layered file classification:
   - `scripts/memory_classify.py` classifies records into `episodic`, `semantic`, `procedural`, `governance`, `scratchpad`, or `archive`.
   - Classification is heuristic and based on source, tags, and content signals.

2. Ontology promotion:
   - `memory/ontology/layer_definition.py` defines L1 episodic, L2 instinct, L3 skill, and L4 strategic.
   - `memory/ontology/promotion_rules.py` defines single-step promotion requirements.
   - L1 to L2 requires confidence >= 0.7 and occurrences >= 3.
   - L2 to L3 requires confidence >= 0.8, occurrences >= 5, success rate >= 0.7, cross-context validation, and governance.
   - L3 to L4 requires confidence >= 0.9, occurrences >= 10, success rate >= 0.85, cross-context validation, governance, and an independent verifier.
   - `agents/memory.py` enforces new agent entries entering at L1 with capped initial confidence by default.

Gap: the file classification layers and ontology layers are related but not identical. A TurboVec backend needs a single mapping contract between durable record layer, ontology layer, and recall eligibility.

## Memory Retrieval Paths

Current retrieval paths:

- `scripts/memory_recall.py`: unified lexical recall over layered memory, night logs, MemPalace, and system state.
- `memory/memory_kernel.py`: scored recall over memory layers with decay, access frequency, dedup, token budget, and layer weights.
- `scripts/memory_index.py`: inverted index over tags and tokens.
- `agents/memory.py`: agent-local recall over per-agent JSONL entries.
- Hermes MCP tools: DMN search and memory recall are available externally to this Codex session, but repository implementation is separate.

Gap: recall has multiple implementations and no single production interface contract for candidate sources, rank features, replay pointers, or vector-backed candidates.

## Replay Integration Points

Replay integration exists through:

- `replay/data_catalog/replay_manifest.json`, which maps DMN, memory layers, action logs, Guardian logs, governance audit logs, cognitive lineage, and agent memory into replay phases.
- `replay/data_catalog/source_inventory.md`, which lists 72 replay data sources, 14,178 JSONL records at generation time, and replay confidence.
- `logs/checksums.jsonl`, which is listed as an integrity chain.
- `observability/cognitive_trace_v2/causal_trace_schema.py`, which defines `MEMORY_RECALL` and `MEMORY_STORE` causal event types.
- `observability/trace_schema.py`, which defines a `memory_recall` trace event.

Gap: recall outputs do not consistently include `event_id`, `root_event_id`, `replay_pointer`, checksum pointer, or causal chain references.

## Guardian Integration Points

Guardian integration exists through:

- `scripts/guardian_check.py`, which classifies actions by policy keywords and decision boundary route.
- `guardian/policy.yaml`, which defines `ALLOW`, `REVIEW_REQUIRED`, and `BLOCK` classes and keyword lists.
- `guardian/decision_boundary.yaml`, which maps routes to `OBSERVE_ONLY`, `RECOMMEND_ONLY`, `PREPARE_FOR_APPROVAL`, or `EXECUTE_ALLOWED`.
- `guardian/approvals.jsonl`, which records approval events.
- `guardian/reflex.jsonl` and incident/audit artifacts.
- `attention/governance/guardian_attention_bridge.py`, which routes Guardian verdicts into attention as governance targets.

Gap: Guardian can inspect an action and its route, but there is no standard recall evidence packet that lets Guardian inspect vector backend, embedding model, similarity score, source record id, replay pointer, and no-decision assertion.

## Cross-Node Synchronization Assumptions

Current repository evidence shows synchronization policy but not a completed DMN heartbeat implementation.

The accepted governance policy allows synchronization of summaries, embeddings or embedding references, anomaly tags, confidence values, replay references, and governance metadata. It rejects raw audio, personal identifiers, sensitive information, full sensor streams, and unnecessary raw data replication.

Gap: there is no reviewed `dmn_sync/heartbeat.py` implementation or `docs/DMN_HEARTBEAT_SYNC.md` artifact in the current inspected files. TurboVec adoption should not assume cross-node embedding synchronization is implemented.

## Existing Memory Schemas

### DMN Schema

`memory/schema.json` requires only:

- `timestamp`
- `source`
- `tags`
- `content`

It rejects additional properties.

### Recall Result Schema

`memory/recall_schema.json` requires:

- `query`
- `sources`
- `matches`
- `confidence`
- `null_recall`
- `timestamp`

Each match requires:

- `source`
- `source_type`
- `content`
- `tags`
- `timestamp`
- `confidence`

### Agent Memory Schema

`agents/memory.py` entries include:

- `content`
- `category`
- `tags`
- `confidence`
- `uses`
- `last_used`
- `created`
- `metadata`
- `layer`
- `entry_id`
- `success_count`
- `failure_count`
- `contexts_validated`

### Telemetry Schema

`telemetry/core/telemetry_schema.py` defines `TelemetryRecord` with:

- `record_id`
- `source`
- `timestamp`
- `timestamp_unix`
- `category`
- `payload`
- `confidence`
- `origin`
- `metadata`

### Trace and Causal Schemas

`observability/trace_schema.py` defines `memory_recall` trace fields:

- `query`
- `results_count`
- `total_tokens`
- `dedup_removed`

`observability/cognitive_trace_v2/causal_trace_schema.py` defines causal events with:

- `event_id`
- `event_type`
- `timestamp`
- `source_subsystem`
- `source_component`
- `action`
- `parent_event_id`
- `root_event_id`
- `generation`
- `agent_id`
- `task_id`
- `payload`
- `outcome`
- `duration_ms`
- `metadata`

## Existing Event Schemas

`architecture/bus_decomposition/event_schema.py` defines IntegrationBus event contracts. Relevant memory events include:

- `memory_metrics`, sourced from `memory.kernel` to `observability.metrics`.
- `memory_flow`, sourced from `memory.kernel` to `observability.memory_flow_tracer`.
- `injection_to_tracer`, which records memory count, tokens used, layers used, top score, and compression status.

These schemas show that memory recall and store are intended to be observable, but not all recall implementations currently emit the same evidence.

## Answers to Key Questions

### A. What currently acts as memory layers?

Short-term memory is the live Codex/session context. Working memory is active task context plus the empty scratchpad layer when used. Long-term memory is DMN plus layered memory and agent-local memory. Replay memory is the replay catalog, logs, checksums, Guardian records, governance audit records, and cognitive trace lineage. Governance memory is `memory/governance`, Guardian artifacts, governance docs, and decision logs.

### B. How does memory move between layers?

DMN records can be classified into layer files by `scripts/memory_classify.py`. New records can be stored directly into layers by `scripts/memory_store.py`. Agent memory starts at L1 by default and can be promoted using ontology promotion rules in `agents/memory.py`. TTL and archive logic exist in `memory/memory_kernel.py`, but this is not the only active memory path.

### C. What metadata is currently preserved?

Common preserved metadata includes timestamp, source, tags, content, layer/classification fields, source line, content hash in some paths, access counts in kernel paths, confidence in recall and agent memory, uses, success/failure counters, contexts validated, Guardian risk, approval records, action logs, checksums, and replay source mappings.

### D. What metadata is currently missing?

Missing or inconsistent metadata includes universal `event_id`, universal `record_id`, source node, sensor type, embedding model, embedding reference, vector backend, similarity score, replay pointer, checksum pointer, governance state, privacy classification, retention policy, schema version, raw-vs-summary marker, confidence rationale, and causal parent/root ids on memory records.

### E. Can a memory be replayed?

Partially yes.

Replay can reconstruct many memories through `replay/data_catalog/replay_manifest.json`, source inventory, action logs, checksum chain, Guardian logs, governance audit logs, and causal lineage. However, a recalled memory does not consistently carry its own replay pointer or causal event id. Replay is therefore possible at the repository/source level, but not guaranteed at the individual recall result level.

### F. Can a recalled memory explain itself?

Partially.

A recalled memory can expose source, source type, content, tags, timestamp, confidence, and sometimes layer. It generally cannot explain why it exists, why it was promoted, what event produced it, what checksum validates it, what replay phase contains it, or why a similarity result was returned.

### G. Can Guardian inspect the source of a recall?

Partially.

Guardian can inspect action strings, policy, routes, approvals, and boundary levels. A recall result can expose a source path and line in `scripts/memory_recall.py`. Guardian does not currently receive a standardized recall evidence packet with vector backend, embedding model, source record id, replay pointer, similarity score, and no-decision flag.

### H. Would TurboVec improve retrieval?

Likely yes for semantic candidate recall over large memory corpora, especially where lexical/tag overlap misses related records. It could improve candidate generation for DMN and layered memory if used behind the recall interface and combined with existing governance, ranking, and replay evidence.

### I. Would TurboVec break anything?

It could break governance if treated as truth, used to bypass layer weights, used to trigger Guardian actions, or introduced without replay pointers and source provenance. It could also fragment recall if added to one recall path but not the others. It should not break existing behavior if introduced only as optional candidate recall evidence in experimental zones with the existing lexical recall retained as fallback.

### J. Which assumptions currently prevent TurboVec adoption?

- Memory records lack a universal id and embedding reference.
- Recall outputs lack replay pointers and causal ids.
- DMN schema is too minimal for vector metadata and rejects additional fields.
- Recall has multiple non-SSOT implementations.
- `memory/index.json` is stale relative to current DMN.
- Cross-node synchronization is policy-only, not implemented.
- Guardian does not yet have a recall evidence packet contract.
- Some stored content still contains encoding corruption, which can degrade embedding quality.

## Gap Analysis

### Critical Gaps

| Priority | Gap | Impact | Complexity |
| --- | --- | --- | --- |
| 1 | No unified memory event schema with `event_id`, `replay_pointer`, `embedding_reference`, and `governance_state` | TurboVec cannot safely map embeddings back to auditable records | Medium |
| 2 | Recall outputs lack standardized provenance and replay pointers | Guardian cannot fully inspect recall source; replay cannot guarantee per-result reconstruction | Medium |
| 3 | Multiple recall paths without one candidate recall contract | TurboVec could fragment retrieval behavior | Medium |

### Major Gaps

| Priority | Gap | Impact | Complexity |
| --- | --- | --- | --- |
| 4 | DMN schema is minimal and does not allow metadata | Durable memory cannot directly carry vector metadata without schema revision or sidecar mapping | Medium |
| 5 | Cross-node synchronization implementation is absent | Embedding sync assumptions are unproven | High |
| 6 | Index freshness is not guaranteed | Retrieval evidence may be stale or inconsistent | Low |
| 7 | Encoding corruption exists in some historical records | Embedding quality and recall explainability may degrade | Medium |

### Minor Gaps

| Priority | Gap | Impact | Complexity |
| --- | --- | --- | --- |
| 8 | Replay catalog counts are older than current DMN count | Review evidence is useful but stale | Low |
| 9 | Scratchpad exists but is empty | Working-memory persistence path is underused | Low |
| 10 | Memory layer names differ from ontology layer names | Contributor confusion and adapter ambiguity | Low |

## Recommended Next Phase

Proceed to Phase 1B: Memory Event Schema and Recall Evidence Contract.

Do not implement TurboVec yet. First define:

- `ASI_MEMORY_EVENT` schema.
- Recall evidence packet schema.
- Stable record id and replay pointer strategy.
- Sidecar embedding metadata policy.
- Guardian recall evidence review boundary.
- Migration-free compatibility path for existing DMN records.

