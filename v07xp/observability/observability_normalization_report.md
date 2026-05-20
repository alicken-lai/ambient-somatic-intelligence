# Observability Normalization Report

## v070 fix

`CIVILIZATION_PARENT_RETENTION = 0.88` documents horizon alignment with v065c.

## Cross-layer checks

- All v070–v077 collectors use `clamp01`
- Gate threshold remains **0.90** per layer
- Production classification remains **≥ 0.95**
- Default evaluate path: no wall-clock, no filesystem

**Normalization:** PASS
