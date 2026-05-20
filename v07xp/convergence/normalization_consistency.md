# Normalization Consistency — v070–v077

## Parent retention by layer

| Layer | Parent field | Retention |
|-------|--------------|-----------|
| v065c external_runtime | external_skill_score | **0.88** |
| v070 civilization | external_runtime_score | **0.88** (aligned) |
| v071–v077 | prior layer primary score | 0.86 |

v070 now matches its immediate parent (v065c) retention weight. Higher layers retain 0.86 on the stacked civilization lineage score — consistent with `v07x_freeze/observability/observability_consistency_report.md`.

## Bonus weight sums

Each layer adds ~**0.135** civilization/reality/continuity bonus when collectors pass. `clamp01` applied via `observability/v04/metric_normalizer`.

## Change log

| Item | Action |
|------|--------|
| `CIVILIZATION_PARENT_RETENTION` | Introduced at 0.88 in v070 score module |
| Thresholds | No change |
| Collector logic | No change |
