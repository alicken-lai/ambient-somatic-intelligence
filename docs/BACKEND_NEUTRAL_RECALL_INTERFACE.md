# Backend-Neutral Recall Interface

Phase: 1E Backend-Neutral Recall Interface Specification  
Date: 2026-06-09  
Status: Non-production interface specification.

## Purpose

ASI needs a governed recall interface that can support future candidate recall backends without binding memory, Guardian, Replay, or runtime behavior to any specific vector engine.

The interface stub lives at `memory/vector/base.py`.

## Design Goals

1. Keep recall candidate-only.
2. Keep backend selection replaceable.
3. Preserve Guardian-visible evidence.
4. Preserve replay reconstruction.
5. Fail closed for privacy and governance filters.
6. Prefer tombstones over physical deletion.
7. Require every backend to export recall evidence compatible with `schemas/recall_evidence.schema.json`.

## Non-Goals

- No production backend selection.
- No vector engine implementation.
- No adapter implementation.
- No dependency installation.
- No changes to DMN append behavior.
- No changes to Guardian, Replay, runtime, governance, or kernel behavior.

## Interface Summary

`RecallBackend` defines:

- `add_record(record, embedding_sidecar)`
- `query(query_embedding, filters, limit)`
- `export_evidence(query_context, results)`
- `tombstone(record_id, reason)`
- `healthcheck()`
- `capabilities()`

`export_evidence` is concrete because evidence shape must remain consistent across backends.

## Safety Defaults

All exported evidence preserves:

- `guardian_visible = true`
- `decision_allowed = false`
- `action_allowed = false`
- `no_decision_made = true`

Any backend attempting to return `RecallResult(decision_allowed=True)` or `RecallResult(action_allowed=True)` is invalid.

## Recall Result Contract

Every recall result must include:

- `record_id`
- `score`
- `rank`
- `backend`
- `embedding_model`
- `provenance`
- `filters_applied`
- `privacy_filters_applied`
- `governance_filters_applied`
- `excluded_reason`
- `replay_pointer`
- `decision_allowed = false`
- `action_allowed = false`

## Evidence Export

`export_evidence` maps backend results into the existing recall evidence schema. It includes candidate ids, scores, ranking method, filters, exclusions, provenance, confidence, replay reference, and safety defaults.

## Placement

The interface sits behind existing governed recall planning. It must not become the production default by being imported into runtime paths without a later reviewed phase.

