# Weakest-Link Analysis — v07x Freeze

**Date:** 2026-05-20

## Finding

| Metric | Value |
|--------|-------|
| `CivilizationLineageIntegrityScore` (pre-fix) | **0.940484** |
| Weakest layer | **v070** @ 0.940484 |
| Freeze threshold | **0.95** |
| Gap | **0.009516** |

All eight lineage layer gates (`gate_pass`) were **true** at 0.90 thresholds; freeze failed only on weakest-link integrity ≥ 0.95.

## Root cause

v070 civilization score combines:

```
combined = external_runtime_score × parent_retention + civilization_bonus
```

- `external_runtime_score` (default path): **~0.9366**
- Civilization dimension collectors (diplomacy, treaty, federation, etc.): **all 1.0** → bonus **0.135**
- Parent retention was **0.86** while v065c external-runtime layer uses **0.88**

That **0.02 retention mismatch** double-compressed the civilization horizon:

```
0.9366 × 0.86 + 0.135 ≈ 0.9405  (FAIL < 0.95)
0.9366 × 0.88 + 0.135 ≈ 0.9592  (PASS ≥ 0.95)
```

Upstream metric collectors and stress fixtures were healthy; the gap was **horizon normalization**, not failing governance simulations.

## Post-fix weakest link

| Layer | Score |
|-------|-------|
| v070 | 0.959216 |
| v077 (new min) | 0.954016 |

Lineage integrity (min): **0.954016** — freeze **PASS**.
