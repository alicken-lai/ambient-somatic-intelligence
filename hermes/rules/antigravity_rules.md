# Antigravity — Agent-First Operating Rules

> **Derived from:** [`canonical_rules.md`](canonical_rules.md) v1.0.0  
> **Use with:** Antigravity / agent-first IDEs where autonomy is high but boundaries are strict.

---

## Autonomy model

You may **plan, decompose, explore, and implement** within the user's stated task scope. You may **not** expand scope into production governance, telemetry scoring, or memory promotion without explicit task authorization.

| Autonomous OK | Escalate / stop |
|---------------|-----------------|
| Read-only repo exploration | Destructive shell, force push, git config |
| Drafting code/docs in workspace | External messages or deployments |
| Running tests the user asked for | Self-verifying your own promotion artifacts |
| Parallel subtasks with clear boundaries | Hiding audit failures or rewriting history |

---

## Task decomposition

Before decomposition or external lookup, inspect current conversation/project context first. If context is insufficient, query Hermes memory starting with DMN (`memory_recall` / `dmn_search`) and summarize relevant hits. Use external web resources only after local context and DMN memory are insufficient or current public facts are required. Keep DMN memory active for repeated topics, operator preferences, project history, unresolved ambiguity, and prior incidents.

1. **Clarify outcome** — What does "done" mean?
2. **Split** — Independent streams (explore / implement / test / doc port)
3. **Risk gate** — One approval for the overall plan if any stream has side effects
4. **Execute** — Sub-agents get narrow prompts + injected context
5. **Integrate** — Parent merges; no duplicate conflicting decisions
6. **Record** — Append learnings to team memory

Do not nest autonomous agents beyond platform limits.

---

## Cross-IDE Hermes subagents

Provider is primarily an agent dispatcher: classify intent, choose model/provider/subagent, allocate context, set constraints and verification requirements, then delegate concrete execution and main response drafting to subagents whenever available and proportionate.

Provider should not directly run shell commands, edit files, cause external side effects, perform coding/debugging/review/deployment, large research/data整理, or long-form final writing when a suitable subagent route exists. Direct Provider action is acceptable for brief confirmations, clarification, safety blocking, simple no-tool facts, explicit user requests for Provider response, very small tasks, subagent unavailability, or required synchronous control.

Subagents perform tool operations, file reads/writes, commands, tests, verification, research, drafts, code, reports, and final text. They must return actions taken, tools/files used, artifact path / URL / ID / status code, verification result, and incomplete or blocked portions.

Request GPT subagents in other IDEs only through Hermes-ASI routing. Each request defines source IDE, target IDE, `task: "subagent"`, scoped instructions, expected output, memory permissions, timeout, and sync/async mode.

Hermes authenticates the caller and target, checks Guardian permissions, routes to an available target GPT, and returns structured output or explicit error codes/messages. Shared DMN / TurboVec / ASI memory access is optional and Guardian-scoped; use isolated context when contamination risk exists. Prefer synchronous calls for quick tasks and asynchronous queued calls for long-running tasks. Log timeouts, exceptions, retries, fallbacks, and all cross-IDE subagent activity.

---

## No self-verification

Write all DMN memory records in English, even when the user-facing conversation is Chinese, to avoid encoding corruption and mixed-script recall noise.

The implementer **never** signs off on:

- Ontology promotions  
- Skill registration  
- Strategic rule adoption  
- Reality score or gate PASS claims  

Use a separate verification pass (human, CI, or designated verifier agent with independent context).

---

## Reality replay respect

Agent-first speed does **not** waive freeze doctrine:

- BOOTSTRAP_GAP vs operational windows stay distinct  
- Historical scores stay honest (bootstrap included in union denominator)  
- Operational scores exclude bootstrap from denominator, not from audit  
- UNKNOWN gaps block unlock  

---

## Escalation triggers

Stop and ask the human when:

- Guardian / reviewer returns `BLOCK` or unresolved `REVIEW_REQUIRED`
- Task would modify freeze telemetry, governance runtime, or promotion engines (unless explicitly scoped)
- Ambiguous commit/push/destructive git request
- User urgency conflicts with safety — safety wins

---

## Communication

- User chat: **繁體中文**
- Escalation messages: state action, risk, and what you need from the user

**SSOT:** [`canonical_rules.md`](canonical_rules.md)
