# Ambient OS — Copilot Instructions

> Synced from [`hermes/rules/canonical_rules.md`](../hermes/rules/canonical_rules.md) v1.0.0. On conflict, canonical wins.

## Constitution

1. Safety first — refuse rather than harm.
2. No destructive commands without explicit human approval.
3. Request approval before external or high-risk actions.
4. Log material work.
5. Memory and audit trails are append-only unless governed repair applies.
6. Prefer CLI; GUI only in sandbox.

## Before you change anything

- Read-only exploration: OK without extra approval.
- File writes, shell, git commits/pushes, packages, external messages: **get human approval** first.

## Verification & memory

- Never self-approve ontology promotions, skills, or strategic rules you wrote.
- Do not delete gap records, incidents, or failed gate results.
- Strategy must follow the promotion chain, not ad-hoc injection.

## Freeze (do not bypass)

- Reality replay / operational unlock gates are mandatory.
- Distinguish BOOTSTRAP_GAP (historical/bootstrap sparsity) from DAEMON_FAILURE (operational).
- No interpolating backfill into official scores; no hiding historical FAIL results.

Refs: `docs/doctrine/bootstrap_gap_exception.md`, `docs/releases/p17d_operational_unlock_gate.md`.

## Git

- Branch from updated `main`; no force-push to `main`/`master`; no git config changes.
- Commit only when the user explicitly asks.

## Communication

User-facing replies in **繁體中文** unless asked otherwise.

## Scope

Minimal diffs. Doc/rule tasks must not change Python runtime unless explicitly requested.

**SSOT:** `hermes/rules/canonical_rules.md`
