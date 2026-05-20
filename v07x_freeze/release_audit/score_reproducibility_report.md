# Score Reproducibility Report — v070–v077

**Audit date:** 2026-05-20

## Determinism checks

| Version | Run 1 | Run 2 | Match |
|---------|-------|-------|-------|
| v070 | 0.940484 | 0.940484 | Yes |
| v071 | 0.943816 | 0.943816 | Yes |
| v072 | 0.944682 | 0.944682 | Yes |
| v073 | 0.945426 | 0.945426 | Yes |
| v074 | 0.946067 | 0.946067 | Yes |
| v075 | 0.946617 | 0.946617 | Yes |
| v076 | 0.947091 | 0.947091 | Yes |
| v077 | 0.947498 | 0.947498 | Yes |

Freeze aggregate (`evaluate_civilization_lineage_integrity`) is deterministic: min score 0.940484 across repeated invocations.

## Method

- Default evidence path (no injected forecaster) — matches gate doc commands
- Scores computed in-process without filesystem side effects
- No random seeds or wall-clock dependencies in score modules

## Reproducibility verdict

**PASS** — all civilization lineage scores are bitwise-stable across consecutive evaluations.
