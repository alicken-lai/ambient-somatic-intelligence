# Stable Record ID Policy

Phase: 1B Memory Event Schema and Recall Evidence Contract  
Date: 2026-06-09  
Status: Policy only. No existing memory records are migrated by this document.

## Purpose

Memory records need stable identifiers independent of storage backend. A record id must remain meaningful if a record is recalled through DMN, layered memory, a replay catalog, an embedding sidecar, or a future vector index.

## Policy

Every memory event must have a `record_id`.

The id must:

- Be stable across indexes and vector backends.
- Be independent of file line number as the sole identity.
- Be deterministic or persistently stored.
- Be safe to expose in recall evidence.
- Be usable by Guardian and replay tooling.
- Not encode sensitive raw content.

## Recommended Format

Use a namespaced id:

```text
mem_<schema_version>_<source_node>_<event_type>_<content_hash_prefix>
```

Example:

```text
mem_v1_localhost_governance_decision_a1b2c3d4e5f6
```

This is a recommended policy, not a migration. Existing records may receive sidecar ids without rewriting historical files.

## Existing Record Compatibility

For existing records without `record_id`, a compatibility wrapper may derive an id from:

- Source path.
- Source line when available.
- Timestamp.
- Source field.
- Content hash.

The derived id must be stored in a sidecar or wrapper so future recalls do not depend on re-deriving it differently.

## Prohibited ID Practices

Do not use:

- Anonymous vector offsets as record identity.
- Backend-specific ids as the only id.
- Raw content as id.
- Mutable line number as the only id.
- Agent-local temporary ids as global ids without namespace.

## Guardian and Replay Requirements

Guardian must be able to use `record_id` to inspect recall source and governance state.

Replay must be able to use `record_id` to find the source record, replay pointer, candidate score, and recall packet.

