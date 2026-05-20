# Doctrine Conflict Report — v0.6.5B External Skill Mount

**Audit date:** 2026-05-19  
**Source:** [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)

## Summary

External Karpathy guidelines are **compatible as advisory coding heuristics** when mounted through Hermes filter + provenance pipeline. Upstream Cursor packaging (`alwaysApply: true` project rule) is **not mirrored** — IDE precedence conflict avoided.

## Conflicts identified

| ID | External pattern | Hermes conflict | Resolution |
|----|------------------|-----------------|------------|
| C1 | `.cursor/rules/karpathy-guidelines.mdc` alwaysApply | Could supersede Guardian flow | Export advisory-only; no auto IDE write |
| C2 | Personal skill under `~/.cursor/skills` | Unbounded injection surface | Registry states + mount dir only |
| C3 | "Behavioral guidelines" without epistemic bounds | Risk of sovereign coding doctrine | Constitutional adapter + filter |
| C4 | Speed/caution tradeoff stated | None — aligns with minimize-scope | Pass through filtered |
| C5 | CLAUDE.md / plugin marketplace paths | Wrong tool chain for Cursor Hermes | Document in IDE exports; not imported |

## Non-conflicts (aligned)

- Simplicity / surgical edits ↔ canonical minimize-scope
- Verifiable success criteria ↔ gate pytest culture
- Ask when unclear ↔ Guardian REVIEW_REQUIRED culture

## Verdict

**Mount approved as RESTRICTED→COMPATIBLE** after filter, provenance, and contamination scan. Not sovereign truth.
