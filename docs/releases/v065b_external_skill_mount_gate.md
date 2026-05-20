# v0.6.5B External Skill Mount Gate (Karpathy Guidelines)

**Version:** `0.6.5b`  
**Date:** 2026-05-19  
**Base:** v0.6.5-alpha HOMEOSTATIC COGNITIVE RUNTIME

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | External audit | Present | `v065b/audit/` |
| 1 | Karpathy mount + provenance | Mirrored advisory | `hermes/skills/external/karpathy_guidelines/` |
| 2 | Doctrine governance | Filter + adapter | `governance/external/` |
| 3 | Skill registry | 5 states | `hermes/skills/external/` |
| 4 | IDE exports | Advisory header | `hermes/rules/external/` |
| 5 | Contamination / drift / provenance | Guards | `governance/external/` |
| 6 | Explainability | 3 explainers | `attention/explainability/` |
| 7 | Observability v065b | 5 metrics + score | `observability/v065b/` |
| 8 | Validation + timeseries | Simulations | `v065b/reports/` |
| 9 | Tests | 10 areas | `tests/v065b/` |
| 10 | ExternalSkillGovernanceScore | ≥ 0.90 | `external_skill_governance_score.py` |
| 11 | Release doc | This file | `docs/releases/v065b_external_skill_mount_gate.md` |

## External dimensions (Phase 10)

| Dimension | Weight |
|-----------|--------|
| doctrine_filter_containment | 0.030 |
| provenance_integrity | 0.030 |
| contamination_containment | 0.028 |
| compatibility_advisory | 0.028 |
| ide_export_boundary | 0.024 |

**Gate threshold:** 0.90

## Governor wiring

`CognitiveGovernor._attach_external_advisory()` adds `external_advisory` after homeostasis. **Observational only** — does not change `accepted` or salience.

## Execution

```bash
python3 -m pytest tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
python3 -c "from v065b_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v065b/reports/doctrine_filtering_timeseries.json'))"
```

## Constraints honored

- External doctrine is not sovereign truth
- Guardian and constitutional cognition preserved
- No automatic IDE overwrite from upstream `alwaysApply`

## Overall Gate Verdict

Run `evaluate_external_skill_governance()` and pytest to confirm **PASS**.
