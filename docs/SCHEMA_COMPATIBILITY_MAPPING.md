# Schema Compatibility Mapping

Phase: 1C Schema Validation Examples and Compatibility Mapping  
Date: 2026-06-09  
Status: Design mapping only. No existing records are mutated by this document.

## Purpose

This document maps current ASI memory and DMN record fields into the Phase 1B `memory_event` schema. It identifies which fields can be mapped directly, which must be derived, and which are currently missing.

Mapping status values:

- `DIRECT`: field exists in current records with compatible meaning.
- `DERIVED`: field can be computed from current fields, path, line, hash, or surrounding context.
- `MISSING`: field cannot be populated reliably from current records.
- `NOT_APPLICABLE`: field is not meaningful for a record type.
- `UNKNOWN`: field may exist in some sources but is not consistently available.

## DMN And Layered Memory Mapping

| Current Field | New Schema Field | Mapping Status | Transformation Needed | Risk | Notes |
| --- | --- | --- | --- | --- | --- |
| `timestamp` | `timestamp` | DIRECT | Preserve existing ISO timestamp. | Low | Some non-DMN sources use epoch seconds; normalize only in wrappers. |
| `source` | `source_system` | DIRECT | Copy source into source system. | Low | Existing values are free-form. |
| `source` | `created_by` | DERIVED | Use source when creator is unknown. | Medium | Source may be a subsystem, not a human or agent. |
| `tags` | `tags` | DIRECT | Copy array. | Low | Existing tags are useful but not governed vocabulary. |
| `content` | `summary` | DERIVED | Use concise safe summary or truncated content. | Medium | Raw content may be too long or sensitive. |
| `content` | `content_hash` | DERIVED | Hash canonical content string. | Low | Must use stable canonicalization. |
| `content` | `content_ref` | DERIVED | Use source file path and line, or `inline` wrapper reference. | Medium | Current DMN record does not contain a content pointer. |
| `_classified_layer` | `governance_state` | DERIVED | Set `classified` when layer classification exists. | Low | Layer is not the same as governance state. |
| `_source_line` | `replay_pointer.source_line` | DIRECT | Copy line number when available. | Low | Present in classified layer files, not raw DMN. |
| `_layer` | `governance_state` | DERIVED | Use as evidence that record was classified/stored. | Medium | `_layer` is storage layer, not review state. |
| `_content_hash` | `content_hash` | DIRECT | Copy if present. | Low | Kernel/store paths may include it. |
| Path to record file | `replay_pointer.source_path` | DERIVED | Use wrapper source path. | Low | Requires wrapper creation context. |
| Line number in JSONL | `replay_pointer.source_line` | DERIVED | Compute during wrapper generation. | Medium | Line numbers can change if files are rewritten; store once in wrapper. |
| `memory/dmn.jsonl` source path | `replay_pointer.manifest_ref` | DERIVED | Link to replay manifest when source is included. | Low | Current replay manifest includes DMN and layer files. |
| Existing checksum chain | `replay_pointer.checksum` | UNKNOWN | Link checksum when available. | Medium | Not every record has direct checksum pointer. |
| Existing schema version | `schema_version` | MISSING | Set wrapper schema version to `1.0.0`. | Low | Historical records do not carry this. |
| None | `record_id` | DERIVED | Generate stable wrapper id from path, line, timestamp, source, and content hash. | Medium | Must persist generated id to avoid drift. |
| None | `source_node` | MISSING | Use local node if known, otherwise `unknown-node`. | Medium | Historical records often omit node identity. |
| None | `source_agent` | UNKNOWN | Infer from source or tags when safe. | Medium | Avoid overclaiming agent identity. |
| None | `sensor_type` | DERIVED | Infer from tags/source/content for sensor records. | Medium | May be wrong for mixed content. |
| None | `modality` | DERIVED | Infer from source/tags/content. | Medium | Needs conservative defaults. |
| None | `confidence` | MISSING | Assign wrapper confidence based on source quality and parse status. | Medium | Must distinguish record confidence from interpretation confidence. |
| None | `privacy_class` | MISSING | Default to `internal` unless policy says stricter. | High | Privacy misclassification is a key risk. |
| None | `retention_policy` | DERIVED | Use layer TTL/policy or governance docs. | Medium | Existing records do not consistently store retention. |
| None | `embedding_ref` | NOT_APPLICABLE | Set null until sidecar exists. | Low | Existing records are not embedded by this phase. |
| None | `lineage` | DERIVED | Use wrapper source and known parent ids if available. | Medium | Historical causal lineage is incomplete. |
| None | `created_at` | DERIVED | Use wrapper creation time, not original event time. | Low | Preserve original event time in `timestamp`. |

## Agent Memory Mapping

| Current Field | New Schema Field | Mapping Status | Transformation Needed | Risk | Notes |
| --- | --- | --- | --- | --- | --- |
| `entry_id` | `record_id` | DERIVED | Namespace as agent-local memory id. | Medium | Existing ids may not be globally unique. |
| `content` | `summary` / `content_hash` | DERIVED | Summarize and hash content. | Medium | Content may contain task-specific sensitive data. |
| `category` | `event_type` | DERIVED | Map strategy/skill/failure/preference to `agent_action` or `text`. | Medium | Category is not the same as event type. |
| `tags` | `tags` | DIRECT | Copy tags. | Low | Tags may be sparse. |
| `confidence` | `confidence` | DIRECT | Copy confidence. | Low | Semantics are agent-local confidence. |
| `created` | `timestamp` | DERIVED | Convert epoch seconds to ISO timestamp. | Low | Current schema requires date-time string. |
| `metadata.author` | `source_agent` / `created_by` | DIRECT | Copy when present. | Low | Missing for some legacy entries. |
| `layer` | `governance_state` | DERIVED | Map L1 to raw/classified, promoted entries to promoted. | Medium | Ontology layer is not governance state. |
| `uses` | `lineage` or side metadata | DERIVED | Preserve in wrapper metadata if schema is extended later. | Low | Current memory_event schema has no direct use count field. |
| `success_count` / `failure_count` | `lineage` or side metadata | DERIVED | Preserve in wrapper metadata if schema is extended later. | Low | Current schema has no direct outcome counters. |
| `contexts_validated` | `lineage` | DERIVED | Include as derived context references if needed. | Medium | May contain sensitive context labels. |

## Replay And Guardian Mapping

| Current Field | New Schema Field | Mapping Status | Transformation Needed | Risk | Notes |
| --- | --- | --- | --- | --- | --- |
| `guardian/approvals.jsonl.action` | `summary` | DERIVED | Summarize action. | Low | Avoid raw sensitive action details when needed. |
| `guardian/approvals.jsonl.risk` | `governance_state` | DERIVED | Map reviewed approval records to `reviewed`. | Low | Risk class should also appear in tags or future metadata. |
| `guardian/approvals.jsonl.approver` | `created_by` | DIRECT | Copy approver. | Low | Approver can be subsystem. |
| `guardian/decision_boundary.yaml` route | `tags` / `summary` | DERIVED | Include boundary as tag or summary. | Low | Not part of memory_event required fields. |
| `replay_manifest.schema_mapping` | `replay_pointer.manifest_ref` | DIRECT | Link manifest. | Low | Source must be included in manifest. |
| `observability/cognitive_trace_v2.event_id` | `replay_pointer.causal_event_id` | DIRECT | Copy when causal event exists. | Low | Not all memory events have causal trace. |
| `observability/cognitive_trace_v2.root_event_id` | `replay_pointer.root_event_id` | DIRECT | Copy when present. | Low | Not all memory events have root id. |

## Fields That Cannot Yet Be Reliably Populated

- `source_node` for older records.
- `privacy_class` for older records.
- `retention_policy` for records outside known layers.
- `replay_pointer.checksum` at per-record precision.
- `replay_pointer.causal_event_id` for non-traced records.
- `embedding_ref` for all current records until sidecars exist.
- Accurate `sensor_type` for mixed or JSON-stringified content.
- Accurate `modality` for mixed records.

## Compatibility Findings

The Phase 1B schema can represent current ASI memory through wrappers, but not by direct raw-record conversion alone.

The safest path is:

1. Keep historical records append-only.
2. Generate wrapper memory events.
3. Store stable wrapper ids.
4. Preserve original timestamps and hashes.
5. Mark unknown or unavailable fields explicitly.
6. Attach replay pointers where manifest and line data exist.
7. Leave `embedding_ref` null until an embedding sidecar is created.

