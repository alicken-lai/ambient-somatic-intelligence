# DMN Cross-Node Sync Policy

Phase: 1G.5 DMN Memory Governance Review  
Date: 2026-06-09  
Status: Policy only. No sync behavior is changed by this document.

## Purpose

This policy defines how DMN memory may eventually synchronize between Home Hermes and Office Hermes.

There is no approved implementation in this phase. Synchronization is not authorized by this document.

## Current State

Repository evidence shows sync doctrine but not a reviewed DMN sync implementation:

- `docs/ASI_GOVERNANCE_CONSTITUTION.md` requires cross-node synchronization to be local first, minimum disclosure, interruptible, and replayable.
- Phase 1B and Phase 1E contracts include `source_node`, provenance, privacy class, replay pointers, and recall evidence.
- Prior review documents note that historical DMN records often lack `source_node`.
- Governance modules reject forced continuity, objective, value, purpose, meaning, agency, or symbolic synchronization.

## Sync Principles

1. Local memory sovereignty is preserved.
2. Sync is minimum disclosure by default.
3. Raw sensitive records do not sync unless explicitly reviewed.
4. Sync never rewrites source node identity.
5. Sync must preserve replay pointers or explain why replay is unavailable.
6. Conflicting memories are surfaced, not forcibly merged.
7. Guardian and human review are required for high-risk categories.
8. Sync can be interrupted and rolled back by tombstone or correction manifest.

## Allowed Categories

Allowed only after policy review and metadata validation:

| Category | Allowed Form |
| --- | --- |
| Public governance docs | Document reference, hash, decision log pointer. |
| Internal governance decisions | Summary plus decision log and replay pointer. |
| Non-sensitive operational lessons | Summary with source node and confidence. |
| Anomaly patterns | Aggregated pattern, source count, no raw sensitive payload. |
| Replay references | Manifest pointers, checksums, source refs. |
| Embedding references | Sidecar references only after privacy review. |

## Disallowed Categories

Do not sync by default:

- raw personal data;
- restricted records;
- raw audio, image, video, or sensor streams;
- credentials, secrets, tokens, private keys;
- full unreviewed DMN dumps;
- unresolved high-risk conflicts;
- records without source node identity;
- records without privacy class;
- records without replay pointer or replay-unavailable reason.

## Trust Model

Each node should have:

- node ID;
- operator scope;
- trust tier;
- allowed sync categories;
- blocked sync categories;
- last reviewed timestamp;
- public key or future identity mechanism when implemented;
- incident history;
- replay manifest compatibility.

No node should become centralized historical authority.

## Privacy Model

Sync must evaluate:

- privacy class;
- raw vs summary status;
- sensitivity of tags and source paths;
- whether embedding exposes private content;
- whether the receiving node has a valid purpose;
- whether a tombstone or redacted summary is safer than transfer.

## Conflict Handling

Cross-node conflicts must:

1. preserve both node records;
2. create or update a conflict record;
3. avoid overwriting local memory;
4. expose conflict state during recall;
5. require review before promotion or governance use.

## Replay Preservation

Every synced record should include:

- source node;
- sync manifest ID;
- source record ID;
- content hash;
- replay pointer;
- sync timestamp;
- receiving node;
- transformation type;
- privacy class;
- governance state.

## Rollback

Rollback should be manifest-based:

1. Identify synced record IDs.
2. Create tombstone or correction records on receiving node.
3. Preserve original sync manifest.
4. Mark recall status as blocked, stale, or superseded.
5. Record rollback in decision log for governance-impacting sync.

## Implementation Gate

Before implementation, the repository must have:

- validated sync manifest schema;
- dry-run examples;
- privacy review checklist;
- conflict register format;
- replay preservation tests;
- explicit Home Hermes / Office Hermes node identity policy.

Until those exist, cross-node DMN sync remains design-only.
