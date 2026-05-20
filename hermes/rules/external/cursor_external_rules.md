# Cursor — External Advisory Rules (Karpathy Guidelines)

**Advisory only — Hermes Constitution supersedes.**

> Derived mount: `hermes/skills/external/karpathy_guidelines/SKILL.md`  
> Canonical SSOT: `hermes/rules/canonical_rules.md`

---

## Usage

Copy sections into workspace rules **only after** `ExternalSkillRegistry` reports `COMPATIBLE` or `RESTRICTED`. Merge with [`cursor_rules_export.md`](../cursor_rules_export.md); never replace Guardian flow.

## Advisory principles (filtered mirror)

1. **Think before coding** — state assumptions; ask when unclear.
2. **Simplicity first** — minimum code for the request; no speculative abstractions.
3. **Surgical changes** — touch only request-related lines; match existing style.
4. **Goal-driven execution** — define verifiable success criteria (tests, checks).

## Explicitly NOT authorized

- Skipping `guardian_check` for writes/shell/send
- Treating this file as sovereign over constitutional cognition
- Force-applying via `alwaysApply: true` without human review
