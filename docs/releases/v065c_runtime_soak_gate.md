# v0.6.5C External Skill Runtime Soak Gate

**Version:** `0.6.5c`  
**Date:** 2026-05-19  
**Base:** v0.6.5B-alpha GOVERNED EXTERNAL COGNITION MOUNTING (ExternalSkillGovernanceScore ~0.905)

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Runtime soak audit | Present | `v065c/audit/` |
| 1 | Runtime sandbox + scope | Bounded | `governance/external/runtime/` |
| 2 | Precedence + sovereignty | Validated | `governance/external/runtime/` |
| 3 | IDE runtime boundary | Contained | `governance/external/runtime/` |
| 4 | Provenance runtime | Validated | `governance/external/runtime/` |
| 5 | Contamination + drift decay | Bounded | `governance/external/runtime/` |
| 6 | Explainability | 3 explainers | `attention/explainability/` |
| 7 | Observability v065c | 6 metrics + score | `observability/v065c/` |
| 8 | Validation + timeseries | 5 horizons + 7 stress | `v065c/reports/` |
| 9 | Tests | 10 areas | `tests/v065c/` |
| 10 | ExternalRuntimeGovernanceScore | ≥ 0.90 | `external_runtime_governance_score.py` |
| 11 | Release doc | This file | `docs/releases/v065c_runtime_soak_gate.md` |

## Runtime dimensions (Phase 10)

| Dimension | Weight |
|-----------|--------|
| runtime_sandbox_containment | 0.025 |
| precedence_guard_rate | 0.025 |
| sovereignty_containment | 0.023 |
| ide_runtime_boundary | 0.023 |
| provenance_runtime_integrity | 0.023 |
| drift_decay_containment | 0.021 |

**Gate threshold:** 0.90

## Governor wiring

`CognitiveGovernor._attach_runtime_observability()` adds `runtime_external_observability` after `external_advisory`. **Observational only** — does not change `accepted` or salience.

## Execution

```bash
python3 -m pytest tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
python3 -c "from v065c_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v065c/reports/external_runtime_timeseries.json'))"
python3 -c "from observability.v065c.external_runtime_governance_score import evaluate_external_runtime_governance as e; r=e(); print(r.external_runtime_score, r.gate_pass)"
```

## Constraints honored

- No new external skill imports or autonomous doctrine evolution
- Hermes rules and Guardian supremacy preserved
- No permanent IDE takeover; runtime guards are observational

## Overall Gate Verdict

Run `evaluate_external_runtime_governance()` and pytest to confirm **PASS**.
