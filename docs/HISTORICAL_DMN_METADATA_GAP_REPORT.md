# Historical DMN Metadata Gap Report

Phase: 1G.8 Historical DMN Wrapper Validation Dry Run  
Date: 2026-06-10  
Status: Read-only dry run.

## Summary

Three historical DMN records were wrapped without mutating `memory/dmn.jsonl`.

All wrappers validate, but most governance metadata is derived or unavailable rather than native to the historical records.

## Missing Fields

Common missing fields:

- `source_node`
- `guardian_review_status`
- `promotion_reason`
- `promotion_score`
- `decay_reason`
- native `importance_score`
- native `retention_policy`
- per-record `replay_id`
- replay `manifest_ref`
- `causal_event_id`
- `root_event_id`
- conflict group metadata
- sync provenance

## Derived Fields

Fields derived during wrapping:

| Field | Derivation |
| --- | --- |
| `record_id` | Synthetic stable wrapper ID based on schema version, node placeholder, type, and source line. |
| `source_record_hash` | SHA-256 hash of the historical JSONL line. |
| `content_hash` | Same SHA-256 source line hash for dry-run provenance. |
| `privacy_class` | Derived from source type and content category. |
| `retention_policy` | Derived from record type and governance relevance. |
| `importance_score` | Estimated from governance/project relevance. |
| `summary` | Human-safe summary of source content. |

## Unknown Fields

Fields intentionally marked as unknown, unavailable, or empty:

- `source_node = unknown-node`
- `guardian_review_status = not_available`
- `promotion_reason = not_available`
- `promotion_score = null`
- `decay_reason = not_available`
- `replay_pointer.available = false`

These values are explicit rather than silently invented.

## Privacy Classification Gaps

The telemetry record at `memory/dmn.jsonl:3` contains local system state and machine-identifying details. It was marked `sensitive` and represented by summary only.

The governance and phase-summary records were marked `internal`, but still require review before cross-node sharing because source node and replay metadata are incomplete.

## Retention Policy Gaps

Historical DMN records do not carry native retention policy.

The wrappers use derived retention labels:

- `governance-memory-review-required`
- `summary-only-review-before-sync`
- `governance-summary-retain`

These labels are dry-run classifications only.

## Guardian Review Gaps

None of the sampled records had a native Guardian review ID or Guardian status field.

Wrappers use:

`guardian_review_status = not_available`

This prevents the wrappers from claiming Guardian approval.

## Replay Pointer Gaps

All three samples have source file, source line, timestamp, and checksum.

All three are missing:

- replay ID;
- replay manifest reference;
- causal event ID;
- root event ID.

Therefore `replay_pointer.available` is false in all wrappers.

## Conclusion

Historical DMN records can be represented as governed wrappers, but not as fully replayable or sync-ready records without additional sidecar metadata or review.
