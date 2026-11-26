# Recall Failure Policy

Phase: 1E Backend-Neutral Recall Interface Specification  
Date: 2026-06-09

## Required Failure Behavior

On backend failure:

1. No autonomous action.
2. No fallback to unsafe recall.
3. Return an empty candidate set.
4. Produce failure evidence if possible.
5. Log failure as an auditable event in a later governed phase.

## Fail-Closed Conditions

A backend must fail closed when:

- Privacy filters cannot be enforced.
- Governance filters cannot be enforced.
- Tombstone state cannot be checked.
- Source provenance is missing for returned candidates.
- Backend state is corrupt or stale.
- Evidence export cannot satisfy required safety defaults.

## Failure Evidence

Failure evidence must preserve:

- `guardian_visible = true`
- `decision_allowed = false`
- `action_allowed = false`
- `no_decision_made = true`
- Empty candidate ids.
- Empty similarity scores.
- Replay reference with failure reason when available.

## Unsafe Fallbacks

Unsafe fallbacks are prohibited.

A backend failure must not silently switch to broad raw memory dump, ignore filters, bypass tombstones, or authorize action.

