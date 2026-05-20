# v0.6.0 Cognitive Governance Kernel Gate

**Version:** `0.6.0`  
**Date:** 2026-05-19  
**Base:** v0.5.4-alpha CALIBRATED + ANTICIPATORY

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Read-only audit | Present | `v060/audit/` |
| 1 | Cognition core | Governor + arbitration | `governance/cognition/` |
| 2 | Sovereignty limits | Anti-monopolization | `governance/cognition/sovereignty_limits.py` |
| 3 | Runtime wire | Governed activation | `attention/runtime/governed_attention_activation.py` |
| 4 | Explainability | Governance reports | `attention/explainability/` |
| 5 | Observability v060 | 5 metrics + stability | `observability/v060/` |
| 6 | Simulated windows | 24h/7d/30d/90d | `v060/reports/` |
| 7 | Tests | 10 areas | `tests/v060/` |
| 8 | CognitiveGovernanceStabilityScore | ≥ 0.90 | `observability/v060/cognitive_governance_stability_score.py` |
| 9 | Release doc | This file | `docs/releases/v060_cognitive_governance_gate.md` |

## Governance Stability (Phase 8)

Extends v0.5.4 `CalibrationStabilityScore` with:

| Governance dimension | Weight |
|----------------------|--------|
| arbitration_fairness | 0.04 |
| sovereignty_compliance | 0.04 |
| uncertainty_discipline | 0.04 |
| replay_bounded | 0.03 |

**Gate threshold:** 0.90 (combined with calibration + forecast + memory + runtime + base attention)

## Execution

```bash
python3 -m pytest tests/v060/ tests/v054/ tests/v053/ tests/v052/ tests/v051/ tests/v050/ -q
python3 -c "from v060_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v060/reports/arbitration_timeseries.json'))"
```

## Constraints honored

- No autonomous execution, no deterministic authority, no Guardian weakening
- No recursive governance loops or cognition monopolization
- v0.5.0–v0.5.4 attention layers preserved

## Overall Gate Verdict

Run `pytest` and `evaluate_cognitive_governance_stability()` with clean bridge evidence to confirm **PASS**.
