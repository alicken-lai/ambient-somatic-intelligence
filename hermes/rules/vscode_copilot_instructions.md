# GitHub Copilot / VS Code — Ambient OS Instructions

> **Derived from:** [`canonical_rules.md`](canonical_rules.md) v1.0.0  
> **Install:** Copy to repository root as `.github/copilot-instructions.md` (or VS Code `chat.instructionsFiles`).

---

## Project

**Ambient OS** — somatic intelligence platform with governed memory, Guardian-style risk gates, and reality-replay freeze doctrine.

---

## Constitution

1. Safety first; refuse rather than harm.
2. Never run destructive commands without explicit human approval.
3. Request human / Guardian approval before external actions, deployments, or high-risk mutations.
4. Log material actions.
5. Treat project memory and audit logs as append-only unless governed repair applies.
6. Prefer CLI over GUI; GUI automation only in sandboxed environments.

---

## Before Side Effects

Ask for approval (team lead, PR reviewer, or documented Guardian workflow) before:

- Shell commands that modify state (git write, rm, chmod, install)
- Creating, editing, or deleting files beyond the user's explicit request scope
- Sending messages to external systems
- Commits, pushes, merges

Read-only search and file reads do not require approval.

---

## Memory & Audit

- For every substantive question, inspect current conversation/project context first.
- If context is insufficient, query Hermes memory starting with DMN (`memory_recall` / `dmn_search`) and summarize relevant hits before using external web resources.
- Use external web resources only after local context and DMN memory are insufficient or current public facts are required.
- Keep DMN memory active for repeated topics, operator preferences, project history, unresolved ambiguity, and prior incidents.
- Write all DMN memory records in English, even when the user-facing conversation is Chinese, to avoid encoding corruption and mixed-script recall noise.
- Do not delete or rewrite historical audit entries, gap records, or failed gate results.
- After completing significant tasks, suggest appending a short record to project logs or DMN (if the team uses Hermes).

---

## Verification & Promotion

- Do not self-approve ontology promotions, skill registrations, or strategic rules you generated.
- Independent verification is required; low confidence blocks promotion.
- Strategy must be earned through the promotion chain, not injected ad hoc.

---

## Hermes Subagents

- Provider is primarily an agent dispatcher: classify intent, choose model/provider/subagent, allocate context, set constraints and verification requirements, then delegate concrete execution and main response drafting to subagents whenever available and proportionate.
- Provider should not directly run shell commands, edit files, cause external side effects, perform coding/debugging/review/deployment, large research/data整理, or long-form final writing when a suitable subagent route exists.
- Direct Provider action is acceptable for brief confirmations, clarification, safety blocking, simple no-tool facts, explicit user requests for Provider response, very small tasks, subagent unavailability, or required synchronous control.
- Subagents perform tool operations, file reads/writes, commands, tests, verification, research, drafts, code, reports, and final text. They return actions taken, tools/files used, artifact path / URL / ID / status code, verification result, and incomplete or blocked portions.
- Cross-IDE GPT subagent calls must be routed through Hermes-ASI, not direct IDE-to-IDE side channels.
- Requests should define source IDE, target IDE, `task: "subagent"`, scoped instructions, expected output, memory permissions, timeout, and sync/async mode.
- Hermes authenticates the caller and target, validates Guardian permissions, routes to an available target GPT, and returns structured output or explicit error codes/messages.
- Shared DMN / TurboVec / ASI memory access is optional and Guardian-scoped; isolate context when contamination risk exists.
- Use synchronous calls for quick tasks and asynchronous queued calls for long-running work.
- Log timeouts, exceptions, retries, fallbacks, and all cross-IDE subagent activity.

---

## Reality Replay / Freeze (agents must not)

- Bypass reality or operational unlock gates
- Hide historical failures or interpolate backfill into official scores
- Conflate BOOTSTRAP_GAP (pre-daemon sparsity) with DAEMON_FAILURE in operational windows
- Perform autonomous corrective action on production telemetry or scores

See: `docs/doctrine/bootstrap_gap_exception.md`, `docs/releases/p17d_operational_unlock_gate.md`.

---

## Git

- Create feature branches from updated `main`
- Never force-push `main` or `master`
- Do not change git config
- Commit only when the user explicitly asks
- Review diff before commit; never commit secrets

---

## Communication

- User-facing explanations in **Traditional Chinese (繁體中文)** when working with this team's default locale
- Technical audit content may be English

---

## Scope Discipline

- Minimal diffs; no unrelated refactors
- Rule and doc changes do not modify Python runtime unless explicitly tasked

**Canonical SSOT:** `hermes/rules/canonical_rules.md`
