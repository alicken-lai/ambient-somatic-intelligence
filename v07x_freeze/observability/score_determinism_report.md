# Score Determinism Report — Observability v070–v077

**Audit date:** 2026-05-20

## Findings

- Default evaluation uses synthetic forecaster evidence paths — no network I/O
- Metric collectors operate on in-memory governance fixtures
- Repeated `evaluate_*()` calls produce identical floats to 6 decimal places (verified for all 8 layers)
- Freeze aggregate `evaluate_civilization_lineage_integrity()` is deterministic

## Non-determinism risks (none observed)

| Risk | Status |
|------|--------|
| Wall-clock timestamps in score | Not used in default path |
| Random sampling | Not present |
| Filesystem reads in default evaluate | Only optional timeseries writers (explicit CLI) |

**Score determinism: PASS**
