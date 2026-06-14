# Recall Filter Policy

Phase: 1E Backend-Neutral Recall Interface Specification  
Date: 2026-06-09

## Required Filter Types

Backends must understand or explicitly reject:

- `privacy_class`
- `governance_state`
- `source_node`
- `event_type`
- `modality`
- `retention_policy`
- `time_range`
- `tags`

## Safety Filter Behavior

Privacy filters fail closed.

Governance filters fail closed.

If a backend cannot enforce privacy or governance filters, it must return an empty candidate set and failure evidence if possible.

## Non-Safety Filter Behavior

Non-safety metadata filters may fail open only when documented in evidence.

Non-safety filters include:

- `source_node`
- `event_type`
- `modality`
- `retention_policy`
- `time_range`
- `tags`

If a non-safety filter fails open, recall evidence must include:

- The unsupported filter.
- The reason it failed open.
- The backend that failed open.

## Filter Ordering

Recommended order:

1. Tombstone exclusion.
2. Privacy filters.
3. Governance filters.
4. Source and modality filters.
5. Time range filters.
6. Tags.
7. Backend ranking.

## Evidence Requirements

Recall evidence must include:

- `filters_applied`
- `privacy_filters_applied`
- `governance_filters_applied`
- `excluded_records`

