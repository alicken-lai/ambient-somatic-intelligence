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

- For substantive questions, inspect current conversation/project context first.
- If context is insufficient, query Hermes memory starting with DMN (`memory_recall` / `dmn_search`) before external web lookup.
- Use external web resources only after local context and DMN memory are insufficient or current public facts are required.
- Keep DMN memory active for repeated topics, operator preferences, project history, unresolved ambiguity, and prior incidents.
- Write all DMN memory records in English, even when the user-facing conversation is Chinese, to avoid encoding corruption and mixed-script recall noise.
- Never self-approve ontology promotions, skills, or strategic rules you wrote.
- Do not delete gap records, incidents, or failed gate results.
- Strategy must follow the promotion chain, not ad-hoc injection.

## Hermes subagents

- Provider is primarily an agent dispatcher: classify intent, choose model/provider/subagent, allocate context, set constraints and verification requirements, then delegate concrete execution and main response drafting to subagents whenever available and proportionate.
- Provider should not directly run shell commands, edit files, cause external side effects, perform coding/debugging/review/deployment, large research/data整理, or long-form final writing when a suitable subagent route exists.
- Direct Provider action is acceptable for brief confirmations, clarification, safety blocking, simple no-tool facts, explicit user requests for Provider response, very small tasks, subagent unavailability, or required synchronous control.
- Subagents perform tool operations, file reads/writes, commands, tests, verification, research, drafts, code, reports, and final text. They return actions taken, tools/files used, artifact path / URL / ID / status code, verification result, and incomplete or blocked portions.
- Cross-IDE GPT subagent calls go through Hermes-ASI routing, with source/target IDE, `task: "subagent"`, scoped instructions, expected output, memory permissions, timeout, and sync/async mode.
- Hermes authenticates, applies Guardian permissions, routes execution, and returns structured output or explicit errors.
- Shared DMN / TurboVec / ASI access is optional and Guardian-scoped; isolate context when contamination risk exists.
- Log timeouts, exceptions, retries, fallbacks, and all cross-IDE activity.

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
