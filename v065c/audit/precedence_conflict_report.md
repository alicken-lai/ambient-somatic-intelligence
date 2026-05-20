# Precedence Conflict Report — v0.6.5C Runtime Soak

**Date:** 2026-05-19  
**Base:** v0.6.5B Karpathy mount (advisory-only)

## Authority stack (canonical)

1. Constitution / Guardian supremacy  
2. Hermes `canonical_rules.md`  
3. CognitiveGovernor (arbitration, identity, coherence)  
4. External advisory (Karpathy guidelines)  
5. IDE export previews (`hermes/rules/external/`)

## Detected conflict classes

| Class | Pattern | Guard |
|-------|---------|-------|
| Hermes override | `supersedes all Hermes` | `RuntimePrecedenceGuard` |
| Guardian bypass | `override guardian` | `RuntimePrecedenceGuard` |
| IDE takeover | `alwaysApply: true` | `IdeRuntimeBoundary` |
| Sovereign claim | `sovereign truth` | `SovereigntyDetector` |

## Verdict

Runtime precedence guards block all tested conflict injections. External doctrine remains **subordinate** to Hermes and Guardian.
