# Single Source of Truth Report

- generated_at: 2026-05-12T08:41:56.890716+00:00
- state_file: state/system_state.json
- corrective_actions: none
- response_mode: recommendations only
- stale_state_detection: ok

## Authoritative Sources

| Value | Source | Field / Method |
| --- | --- | --- |
| dmn_append_count | memory/dmn.jsonl | count non-empty JSONL records |
| health_score | guardian/health/health_scores.json | /current/health_score |
| incident_count | guardian/incidents/index.json | /incident_count |
| repeated_anomalies | guardian/incidents/index.json | /patterns/repeated_anomaly_types |
| reflex_confidence | guardian/incidents/reflex_confidence_calibration.json | /anomalies/-1/confidence |
| baseline_deviation | guardian/baselines/telemetry_baseline.json | /overall_deviation_severity and /metrics/*/deviation |
| time_context | guardian/baselines/circadian_baseline.json | /time_context |
| circadian_deviation | guardian/baselines/circadian_baseline.json | /overall_deviation_severity and /metrics/*/deviation |
| simulation_active | guardian/simulations/latest_simulation.json | /simulation_active |
| predicted_risk | guardian/simulations/latest_simulation.json | /predicted_risk |

## Current Values

- dmn_append_count: 77
- health_score: 76.53
- incident_count: 2
- repeated_anomaly_count: 2
- repeated_anomalies: {"high_memory_usage":2}
- reflex_confidence: 0.05
- base_reflex_confidence: 0.1
- risk_class: low_confidence_watch
- baseline_deviation: elevated
- time_context: {"day_type":"weekday","hour_of_day":22,"timestamp":"2026-05-11T22:14:35.452488+00:00","weekday":"monday"}
- circadian_deviation: warning
- simulation_active: True
- predicted_risk: {"confidence":0.6,"false_positive_likelihood":"low","horizon_summary":{"2h":"review","30m":"review","5m":"watch"},"incident_similarity":"memory_used_percent","level":"review","primary_driver":"memory_used_percent"}

## Validation

- stale_state_detection.status: ok
- stale_state_detection.mismatches: none
- stale_state_detection.newer_sources: none

## Recommendations

- Rebuild `state/system_state.json` before regenerating dashboard or daily digest metadata.
- Keep dashboard and digest builders read-only against source artifacts; they should render state, not recompute it.
