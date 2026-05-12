# Decision Boundary Audit

- corrective_actions: none
- response_mode: recommendations only
- boundary_protocol: guardian/decision_boundary.yaml
- protocol_status: valid

## Checks

| Check | Result | Detail |
| --- | --- | --- |
| boundary_levels_defined | ok | OBSERVE_ONLY, RECOMMEND_ONLY, PREPARE_FOR_APPROVAL, EXECUTE_ALLOWED |
| route_mapping_complete | ok | all current routes in `scripts/action_router.py` are mapped in `guardian/decision_boundary.yaml` |
| execute_allowed_empty | ok | no current route is assigned to `EXECUTE_ALLOWED` |
| guardian_checks_include_boundary_level | ok | `scripts/guardian_check.py` and `scripts/action_router.py` include boundary-level metadata in route classification output |
| default_actions_non_corrective | ok | current route scripts continue to report `corrective_actions: none` in generated artifacts |

## Route Summary

- OBSERVE_ONLY: `system-info`, `uptime`, `disk-usage`, `memory-usage`, `vision-capture`, `vision-capture-smoke`, `vision-capture-ocr-smoke`, `state-query`
- RECOMMEND_ONLY: `telemetry-local`, `incident-recall-build`, `baseline-learn-build`, `health-score-build`, `memory-pressure-diagnose`, `circadian-baseline-build`, `system-state-build`, `somatic-dashboard-build`, `daily-digest-build`, `anomaly-explain-build`, `memory-integrity-audit`, `self-reflect-build`, `operator-briefing-build`, `approval-packet-build`, `simulation-build`, `dream-build`
- PREPARE_FOR_APPROVAL: `cua-guarded-smoke`, `guardian-reflex-once`
- EXECUTE_ALLOWED: none

## Recommendations

- Keep `EXECUTE_ALLOWED` empty until a formal approval workflow is explicitly defined.
- Preserve `corrective_actions: none` as the default generated-artifact posture.
- Re-run the audit whenever a route is added or reassigned.
