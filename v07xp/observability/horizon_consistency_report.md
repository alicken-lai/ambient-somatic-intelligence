# Horizon Consistency Report

## Issue

v065c external-runtime combination uses **0.88** parent retention. v070 used **0.86** on `external_runtime_score`, creating an extra 2% compression before civilization bonuses.

## Resolution

Explicit `CIVILIZATION_PARENT_RETENTION = 0.88` in v070 score module with inline documentation.

## Validation

- Default civilization score crosses production tier (≥ 0.95)
- Lineage freeze integrity crosses 0.95 weakest-link gate
- No collector or threshold changes

**Horizon consistency:** PASS
