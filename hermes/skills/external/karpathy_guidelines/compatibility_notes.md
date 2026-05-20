# Karpathy Guidelines — Hermes Compatibility Notes

**Mount:** v0.6.5B external skill advisory  
**Status target:** COMPATIBLE (when provenance + filter pass)

## Aligned with Ambient OS

| Karpathy principle | Hermes alignment |
|--------------------|------------------|
| Think before coding | Epistemic limits; uncertainty override |
| Simplicity first | Minimize scope agent principle |
| Surgical changes | Git safety; no unrelated refactors |
| Goal-driven execution | Independent verification; pytest gates |

## Conflicts resolved at mount

| External risk | Hermes control |
|---------------|----------------|
| Cursor `alwaysApply: true` in upstream | **Not imported** — advisory export only |
| Skill as personal sovereign rules | `advisory_only: true` in manifest |
| Unbounded injection | `DoctrineFilter` + registry BLOCKED state |
| Guardian bypass language | Constitutional adapter + contamination guard |

## Non-goals

- Does not replace `hermes/rules/canonical_rules.md`
- Does not weaken Guardian or constitutional cognition
- Does not write to `.cursor/rules/` automatically
