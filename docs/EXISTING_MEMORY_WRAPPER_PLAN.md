# Existing Memory Wrapper Plan

Phase: 1C Schema Validation Examples and Compatibility Mapping  
Date: 2026-06-09  
Status: Plan only. No wrapper generator is implemented by this document.

## Purpose

Existing ASI memory records must be made compatible with the Phase 1B memory event schema without rewriting history.

This plan explains how old records can be wrapped into `memory_event` records while preserving append-only memory doctrine.

## Rules

1. Do not mutate old records.
2. Create wrapper records.
3. Preserve original source hash.
4. Preserve original timestamp if available.
5. Assign stable `record_id`.
6. Add `governance_state`.
7. Add `replay_pointer` if available.
8. Mark missing fields explicitly.

## Wrapper Strategy

### Step 1: Read Historical Record

Read one source record from a known source, such as:

- `memory/dmn.jsonl`
- `memory/episodic/records.jsonl`
- `memory/semantic/records.jsonl`
- `memory/procedural/records.jsonl`
- `memory/governance/records.jsonl`
- `state/agents/*/memory/entries.jsonl`
- `guardian/approvals.jsonl`
- `guardian/reflex.jsonl`
- `governance/audit/*.jsonl`

### Step 2: Canonicalize And Hash

Canonicalize the original record content using stable JSON serialization when possible. Compute `content_hash` from the canonical source payload.

Do not hash a reformatted summary as a substitute for the original source hash.

### Step 3: Assign Stable Record ID

Generate a stable id from:

- Wrapper schema version.
- Source path.
- Source line when available.
- Original timestamp.
- Original source.
- Content hash prefix.

Persist the generated id in the wrapper output so future systems do not re-derive a different id.

### Step 4: Preserve Time Semantics

Use the original event timestamp as `timestamp`.

Use wrapper creation time as `created_at`.

If original timestamp is unavailable, set `timestamp` to wrapper creation time and mark the replay pointer reason.

### Step 5: Classify Event Type And Modality

Use conservative mapping:

| Source Pattern | Event Type | Modality |
| --- | --- | --- |
| DMN text or docs summary | `text` | `text` |
| Telemetry JSON | `system` | `timeseries` or `system_log` |
| Sensor observation | `sensor` | sensor-specific modality |
| Somatic attention or anomaly | `somatic` | `timeseries`, `power`, or `agent_trace` |
| Agent task memory | `agent_action` | `agent_trace` |
| Guardian approval/reflex | `guardian_observation` | `agent_trace` |
| Governance audit/decision | `governance_decision` | `text` |
| Replay report or score | `replay_event` | `system_log` |

When uncertain, use `text` event type only if the record is truly text; otherwise mark classification risk in wrapper metadata or wrapper audit notes.

### Step 6: Add Privacy And Retention

Default old records to `internal` until a privacy classifier or review exists.

Escalate to `sensitive` or `restricted` when records contain:

- Personal identifiers.
- Raw private logs.
- Raw audio, image, or video.
- Access control details.
- External credentials or secrets.
- Security-sensitive operational details.

Retention should come from layer policy when available:

| Layer | Suggested Retention |
| --- | --- |
| scratchpad | `scratchpad-24h` |
| episodic | `episodic-30d` |
| semantic | `semantic-365d` |
| procedural | `procedural-180d` |
| governance | `governance-365d` or `governance-unlimited` |
| archive | `archive-10y` |

### Step 7: Add Replay Pointer

Use replay data when available:

- `source_path`
- `source_line`
- `timestamp`
- checksum reference
- `replay/data_catalog/replay_manifest.json`
- replay phase
- causal event ids when available

If replay data is missing:

```json
{
  "available": false,
  "reason": "source record has no replay manifest entry or line-stable checksum pointer"
}
```

### Step 8: Leave Embedding Ref Null

Set `embedding_ref` to `null` until an embedding sidecar exists.

No wrapper should pretend a record is embedded.

## Wrapper Output Location

This phase does not select or create a production wrapper storage location.

Recommended future options:

- `memory/wrappers/records.jsonl`
- `memory/events/records.jsonl`
- `examples/wrappers/` for non-production examples

The production location should be chosen in a later reviewed phase.

## Compatibility Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Privacy class cannot be reliably inferred from old records | High | Default to internal and require review before embedding or sync. |
| Record ids may drift if generated repeatedly | High | Persist wrapper ids once generated. |
| Per-record replay checksum is not always available | Medium | Use source path/line and manifest; mark checksum missing explicitly. |
| JSON-stringified DMN content may need double parsing | Medium | Preserve original string hash; parse only for summaries. |
| Encoding corruption can degrade summaries and embeddings | Medium | Add encoding-quality flag before indexing. |
| Layer names differ from ontology layers | Medium | Keep storage layer and ontology layer separate in future wrapper metadata. |
| Existing recall paths do not emit wrapper ids | Medium | Require recall evidence packet before vector adapter implementation. |

## Readiness Effect

The wrapper plan reduces schema compatibility uncertainty, but does not yet implement wrapper generation or enforcement.

Recommended next phase remains non-production: create wrapper examples or a dry-run wrapper audit before any vector adapter work.

