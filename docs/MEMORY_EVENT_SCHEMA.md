# Memory Event Schema

Phase: 1B Memory Event Schema and Recall Evidence Contract  
Date: 2026-06-09  
Status: Contract only. No runtime behavior is changed by this document.

## Purpose

ASI memory records need stable identity, provenance, replay semantics, privacy classification, and embedding references before any compressed vector backend can be safely introduced.

This document defines the unified memory event contract. The JSON Schema lives at `schemas/memory_event.schema.json`.

## Design Principles

1. Memory identity is independent of storage backend.
2. Vector recall is candidate recall only.
3. Candidate recall does not equal truth.
4. Candidate recall does not authorize action.
5. Every important memory event must be replayable or explicitly mark why replay is unavailable.
6. Embeddings must reference memory records; they must not become anonymous vectors.
7. Guardian must be able to inspect the origin, privacy class, governance state, and replay pointer of recalled records.

## Supported Event Types

| Event Type | Meaning |
| --- | --- |
| `text` | Human-authored, agent-authored, or document-derived text memory. |
| `sensor` | Raw or summarized sensor-derived observation. |
| `somatic` | Somatic attention, pressure, anomaly, or embodied-system signal. |
| `system` | System state, telemetry, daemon, environment, or operational event. |
| `agent_action` | Agent task, tool, decision, or execution record. |
| `guardian_observation` | Guardian classification, approval, block, review, or reflex observation. |
| `governance_decision` | Governance policy, decision log, PR gate, or safety doctrine event. |
| `replay_event` | Replay, validation, audit, or reconstruction event. |

## Supported Modalities

| Modality | Meaning |
| --- | --- |
| `text` | Text content, summaries, docs, logs. |
| `audio` | Audio-derived source. |
| `image` | Image or screenshot-derived source. |
| `video` | Video-derived source. |
| `timeseries` | Numeric time-series data. |
| `wifi_csi` | Wi-Fi CSI signal-derived data. |
| `power` | Power or energy measurement. |
| `temperature` | Temperature measurement. |
| `humidity` | Humidity measurement. |
| `vibration` | Vibration or motion signal. |
| `access_control` | Access, entry, permission, or boundary event. |
| `system_log` | System, daemon, process, or action log event. |
| `agent_trace` | Agent trace, causal trace, or task execution trace. |

## Privacy Classes

| Privacy Class | Use |
| --- | --- |
| `public` | Safe to share publicly. |
| `internal` | Project-internal, not public by default. |
| `sensitive` | Contains sensitive operational, personal, or security-relevant information. |
| `restricted` | Highly restricted; requires explicit review before sync, embedding, or disclosure. |

## Governance States

| State | Meaning |
| --- | --- |
| `raw` | Newly captured or imported; not classified. |
| `classified` | Assigned layer, privacy, or semantic class. |
| `promoted` | Promoted through governed memory criteria. |
| `recalled` | Returned by a recall operation. |
| `reviewed` | Reviewed by Guardian, human, governance gate, or verifier. |
| `archived` | Moved to archive or cold storage. |
| `deleted` | Deleted or tombstoned through a governed process. |

## Required Fields

| Field | Requirement |
| --- | --- |
| `record_id` | Stable id independent of storage backend. |
| `schema_version` | Schema version for compatibility. |
| `event_type` | One of the supported event types. |
| `timestamp` | Event occurrence time. |
| `source_node` | Node, machine, or deployment where the event originated. |
| `source_system` | System or subsystem that produced the event. |
| `source_agent` | Agent id when applicable. Empty string when no agent is involved. |
| `sensor_type` | Sensor type when applicable. Empty string when not sensor-derived. |
| `modality` | One of the supported modalities. |
| `summary` | Human-readable summary safe for recall display. |
| `content_ref` | Path, URI, line pointer, object key, or `inline` reference to source content. |
| `content_hash` | Hash of canonical source content. |
| `confidence` | 0.0 to 1.0 confidence in record quality or interpretation. |
| `privacy_class` | One of the supported privacy classes. |
| `retention_policy` | Retention class or policy label. |
| `governance_state` | One of the supported governance states. |
| `replay_pointer` | Replay pointer object. |
| `embedding_ref` | Embedding reference object or null. |
| `tags` | Search and governance tags. |
| `lineage` | Parent/root/source lineage. |
| `created_by` | Creator identity. |
| `created_at` | Record creation timestamp. |

## Compatibility With Existing Memory

Existing DMN records only require `timestamp`, `source`, `tags`, and `content`. Phase 1B does not change DMN append behavior.

Future adapters should create memory event wrappers or sidecars around existing records rather than rewriting historical DMN records.

## Required Before Vector Recall

A memory event is eligible for vector indexing only when it has:

- Stable `record_id`.
- Non-empty `content_hash`.
- Non-empty `content_ref`.
- Privacy class reviewed for embedding.
- Replay pointer or explicit replay-unavailable reason.
- Embedding sidecar metadata if already embedded.
- Governance state that permits recall.

