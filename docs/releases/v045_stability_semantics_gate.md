# v0.4.5 Stability Semantics Gate

**Version:** `0.4.5-alpha`  
**Date:** 2026-05-19  
**Base:** v0.4.2-alpha (Entropy SSOT PASS)

## Gate Criteria

| Criterion | Target | Result |
|-----------|--------|--------|
| Clean graph stability | ≥ 0.85 | **PASS** — `tests/v045/test_clean_graph_gate.py` |
| v042 stability regression | `test_stability_gate_on_clean_graph` | **PASS** |
| Semantics alignment | ≥ 0.95 | **PASS** — `tests/v045/test_semantics_alignment.py` |
| Explainability | breakdown + dominant failure | **PASS** — `tests/v045/` |
| Doctrine | `docs/doctrine/clean_graph_definition.md` | **PASS** |
| Audit pack | `v045/audit/*` | **PASS** |

## Root Cause (0.72625 failure)

Stability dimensions used **kind-mean** over all metrics, penalizing clean graphs when:

- `truth_orphan_nodes=1` on edgeless baseline graphs
- Patch churn/age/active > 0 while `patch_leakage=0`
- Mutation denial/hook averages > 0 while `mutation_rate=0`

Evidence showed healthy critical signals; composite score contradicted gate semantics.

## Fix Summary

1. `truth_entropy_adapter` — edgeless graphs exempt from orphan truth penalty
2. `stability_score` — max-of-gate-metrics via `metric_normalizer`
3. `stability_breakdown`, `explainable_stability`, `semantics_alignment` observability modules

## pytest

```bash
python3 -m pytest tests/v045/ tests/v042/test_stability_score.py tests/v04/ tests/v042/ tests/v043/ tests/v044/ tests/v044b/ -q
```

## Overall Gate Verdict

**PASS** — Clean graph passes stability gate; semantics aligned; SemanticsAlignmentScore ≥ 0.95.
