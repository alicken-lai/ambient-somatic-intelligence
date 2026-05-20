# Observability Consistency Report — v070–v077

**Audit date:** 2026-05-20

## Package structure

Each `observability/v0xx/` contains:

- 6 dimension metric collectors (`*_metrics.py`)
- 1 composite score module (`cognitive_*_score.py`)
- `__init__.py` export surface

**8/8 packages conform.**

## Cross-layer consistency

| Property | v070–v077 |
|----------|-----------|
| Gate threshold constant | 0.90 |
| Parent score weight in combined formula | 0.86 |
| Layer bonus weight sum | ~0.135 per layer |
| `clamp01` normalization | Yes (`observability/v04/metric_normalizer`) |
| `hard_failures` list on score dataclass | Yes |
| `guardian_supremacy_preserved` evidence field | Yes (inherited chain) |
| Classification tiers | production ≥0.95, stable ≥0.90, restricted <0.90 |

## Metric naming

Lineage-related metrics appear in each layer (`*_lineage_integrity_metrics.py` or equivalent). Agency layer (v077) includes `agency_lineage_integrity_metrics`.

**Observability consistency: PASS**
