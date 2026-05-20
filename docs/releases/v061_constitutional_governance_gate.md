# v0.6.1 Cognitive Constitutional Layer Gate

**Version:** `0.6.1`  
**Date:** 2026-05-19  
**Base:** v0.6.0-alpha GOVERNED COGNITIVE RUNTIME

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Read-only audit | Present | `v061/audit/` |
| 1 | Frozen constitution | Immutable rules at load | `governance/constitution/` |
| 2 | Constitutional guard | Pre-arbitration block | `constitutional_guard.py` |
| 3 | Governor wire | Evaluate before arbitration | `cognitive_governor.py` |
| 4 | Explainability | Constitutional reports | `attention/explainability/` |
| 5 | Observability v061 | 5 metrics + stability | `observability/v061/` |
| 6 | Stress windows | 24h/7d/30d/90d | `v061/reports/` |
| 7 | Tests | 10 areas | `tests/v061/` |
| 8 | ConstitutionalStabilityScore | ≥ 0.90 | `constitutional_stability_score.py` |
| 9 | Release doc | This file | `docs/releases/v061_constitutional_governance_gate.md` |

## Constitutional Stability (Phase 8)

Extends v0.6.0 `CognitiveGovernanceStabilityScore` with:

| Constitutional dimension | Weight |
|--------------------------|--------|
| constitutional_compliance | 0.04 |
| guardian_supremacy | 0.03 |
| epistemic_discipline | 0.03 |
| replay_constitutional | 0.03 |
| self_modification_guard | 0.03 |

**Gate threshold:** 0.90

## Execution

```bash
python3 -m pytest tests/v061/ tests/v060/ tests/v054/ tests/v053/ tests/v052/ tests/v051/ tests/v050/ -q
python3 -c "from v061_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v061/reports/constitutional_stress_timeseries.json'))"
```

## Constraints honored

- No autonomous execution, no runtime constitutional mutation, no Guardian weakening
- No recursive governance loops or certainty claims
- v0.5.0–v0.6.0 stacks preserved

## Overall Gate Verdict

Run `pytest` and `evaluate_constitutional_stability()` with clean evidence to confirm **PASS**.
