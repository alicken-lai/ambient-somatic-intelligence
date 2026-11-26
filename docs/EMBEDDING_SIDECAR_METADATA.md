# Embedding Sidecar Metadata

Phase: 1B Memory Event Schema and Recall Evidence Contract  
Date: 2026-06-09  
Status: Contract only. No embedding generation or vector index is implemented by this document.

## Purpose

Embeddings must never be anonymous vectors. Every embedding must be traceable to a stable memory record, source hash, model, backend, privacy class, retention policy, and schema version.

The JSON Schema lives at `schemas/embedding_sidecar.schema.json`.

## Sidecar Principle

Embedding metadata should live beside or above vector indexes as a sidecar. The sidecar maps vector entries back to governed memory records.

The sidecar must not replace source memory. The source memory remains the durable record.

## Required Fields

| Field | Meaning |
| --- | --- |
| `embedding_id` | Stable id for the embedding sidecar record. |
| `schema_version` | Sidecar schema version. |
| `source_record_id` | Stable memory event id. |
| `source_content_hash` | Hash of canonical source content. |
| `embedding_model` | Model used to create the embedding. |
| `embedding_dimension` | Vector dimension. |
| `embedding_created_at` | Timestamp of embedding creation. |
| `vector_backend` | Backend label, such as `none`, `inverted_index`, or `turbovec`. |
| `vector_index_ref` | Reference to vector index, shard, namespace, or null. |
| `privacy_class` | Privacy class copied from or stricter than the source memory event. |
| `retention_policy` | Retention policy copied from or stricter than the source memory event. |
| `source_schema_version` | Schema version of source memory event. |
| `created_by` | Actor that created the embedding. |
| `replay_pointer` | Replay pointer for embedding creation or source event. |
| `metadata` | Backend-neutral extra metadata. |

## Privacy Rule

Embedding privacy class must be at least as restrictive as the source memory event. Restricted source records must not be embedded without explicit governance review.

## Retention Rule

Embedding retention must not outlive the governed retention policy of the source record unless an explicit governance decision permits an exception.

## Hash Rule

The sidecar is stale when `source_content_hash` no longer matches the canonical source content hash. Stale sidecars must be excluded from candidate recall or clearly marked as stale.

## Backend Neutrality

The sidecar does not require TurboVec. Any future vector backend must use the same identity, privacy, retention, and replay metadata.

