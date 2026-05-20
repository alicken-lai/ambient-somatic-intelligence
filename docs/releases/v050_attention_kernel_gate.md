# v0.5.0 Attention Kernel Gate

**Version:** `0.5.0`  
**Date:** 2026-05-19  
**Base:** v0.4.5-alpha OPERATIONALLY STABLE (`ken-dev` @ c098a4f)

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Read-only audit | Present | `v050/audit/` |
| 1 | Core 10 dimensions | 10 dims, weights ≈ 1.0 | `attention/core/` |
| 2 | Attention kernel | Orchestrator + queue + router | `attention/kernel/` |
| 3 | Somatic bridge | Adapter + precursor sim | `attention/somatic/` |
| 4 | Memory activation | Recall + episodic resonance | `attention/memory/` |
| 5 | Competition | Fairness + budget | `attention/competition/` |
| 6 | Dynamics | Decay, fatigue, circadian, recovery | `attention/dynamics/` |
| 7 | Explainability | Breakdown + precursor explain | `attention/explainability/` |
| 8 | Observability v05 | Metrics, pressure, distribution | `observability/v05/` |
| 9 | Tests | 10 areas | `tests/v050/` |
| 10 | AttentionStabilityScore | ≥ 0.90 | `observability/v05/attention_stability_score.py` |
| 11 | Release doc | This file | `docs/releases/v050_attention_kernel_gate.md` |

## Attention Stability (Phase 10)

| Dimension | Weight |
|-----------|--------|
| salience_explainability | 0.18 |
| competition_fairness | 0.16 |
| focus_stability | 0.14 |
| budget_discipline | 0.14 |
| precursor_coverage | 0.10 |
| memory_activation | 0.10 |
| somatic_integration | 0.08 |
| decay_recovery | 0.10 |

**Gate threshold:** 0.90

## Execution

```bash
python3 -m pytest tests/v050/ -q
python3 -m pytest tests/v045_runtime/ tests/v04/ -q
```

## Constraints honored

- No ontology doctrine / replay semantics changes
- No runtime kernel redesign
- TruthGraph, EntropyController, IsolationKernel, PatchRegistry, Reality Replay preserved
- Legacy `attention/salience_engine.py` retained with backward-compat exports

## Integration note

Pre-existing `attention/` modules (`salience_engine`, `priority_allocator`, `escalation_router`) remain at package root. v0.5 adds `attention/core/`, `attention/kernel/`, and subpackages; `attention/__init__.py` re-exports both.

## Overall Gate Verdict

Run `pytest tests/v050/` and `evaluate_attention_stability()` with clean evidence to confirm **PASS**.
