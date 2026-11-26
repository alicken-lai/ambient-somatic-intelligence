# Replay Pointer Policy

Phase: 1B Memory Event Schema and Recall Evidence Contract  
Date: 2026-06-09  
Status: Policy only. No replay behavior is changed by this document.

## Purpose

Every important memory event and recall evidence packet must contain or reference replay information. Replay must be able to reconstruct what happened, why it happened, what evidence existed, what memory was recalled, and which governance rule applied.

## Replay Pointer Shape

A replay pointer should include:

- `replay_id`
- `source_path`
- `source_line`
- `timestamp`
- `checksum`
- `manifest_ref`
- `phase`
- `causal_event_id`
- `root_event_id`

Fields may be empty or null when not available, but important memory events must explain missing replay data.

## Required For Important Events

Replay pointer is required for:

- Governance decisions.
- Guardian observations.
- Memory promotions.
- Recall evidence packets.
- Embedding sidecar creation.
- Sensor events used for later decisions.
- Agent actions used for future strategy or policy.
- Any record eligible for vector indexing.

## Missing Replay Data

When replay data is unavailable, the memory event or evidence packet must include:

- `replay_pointer.available = false`
- A reason in `replay_pointer.reason`
- Source metadata sufficient for future repair if possible

## Replay Reconstruction Requirements

Replay must be able to reconstruct:

- Query or event summary.
- Candidate records.
- Scores or confidence.
- Filters.
- Backend.
- Timestamp.
- Initiating agent.
- Guardian state if reviewed.
- Whether action was allowed.

## Relationship To Existing Replay Catalog

The current replay catalog provides source-level and phase-level replay through `replay/data_catalog/replay_manifest.json` and `replay/data_catalog/source_inventory.md`.

This policy adds per-record and per-recall pointer requirements for future schema work. It does not rewrite existing replay artifacts.

