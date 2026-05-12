# Latest Anomaly Explanation

- generated_at: 2026-05-12T00:34:10.366432+00:00
- active_warning_count: 5
- latest_telemetry: observability/snapshots/telemetry-2026-05-11T221435.452488Z0000.json
- time_context: {"day_type":"weekday","hour_of_day":22,"timestamp":"2026-05-11T22:14:35.452488+00:00","weekday":"monday"}
- overall_flat_deviation: elevated
- overall_circadian_deviation: warning
- corrective_actions: none
- response_mode: recommendations only

## Metric Warnings

### disk_used_percent

- observed_value: 54.86
- flat_baseline: mean=53.965, severity=warning, z=2.7934, delta=0.895
- circadian_baseline: basis=weekday, mean=54.4305, severity=elevated, z=1.5607, delta=0.4295
- confidence: base=0.1, time_adjusted=0.05, class=low_confidence_watch
- confidence_reason: time-aware severity=warning; comparison bucket count=21
- likely_cause: disk usage is slightly above both broad and time-aware local baselines
- resembles_prior_incidents: False
- health_history: 76.55 -> 76.53

### load_average_15m

- observed_value: 1.4
- flat_baseline: mean=1.745, severity=critical, z=-4.1169, delta=-0.345
- circadian_baseline: basis=weekday, mean=1.5481, severity=elevated, z=-1.4118, delta=-0.1481
- confidence: base=0.1, time_adjusted=0.05, class=low_confidence_watch
- confidence_reason: time-aware severity=warning; comparison bucket count=21
- likely_cause: load is lower than the broad learned baseline; circadian context reduces but does not erase the deviation
- resembles_prior_incidents: False
- health_history: 76.55 -> 76.53

### load_average_5m

- observed_value: 1.43
- flat_baseline: mean=1.745, severity=critical, z=-6.338, delta=-0.315
- circadian_baseline: basis=weekday, mean=1.5495, severity=elevated, z=-1.2107, delta=-0.1195
- confidence: base=0.1, time_adjusted=0.05, class=low_confidence_watch
- confidence_reason: time-aware severity=warning; comparison bucket count=21
- likely_cause: load is lower than the broad learned baseline; circadian context reduces but does not erase the deviation
- resembles_prior_incidents: False
- health_history: 76.55 -> 76.53

### memory_used_percent

- observed_value: 96.21
- flat_baseline: mean=99.4625, severity=critical, z=-23.0184, delta=-3.2525
- circadian_baseline: basis=weekday, mean=97.9329, severity=warning, z=-2.1355, delta=-1.7229
- confidence: base=0.1, time_adjusted=0.05, class=low_confidence_watch
- confidence_reason: time-aware severity=warning; comparison bucket count=21
- likely_cause: memory is lower than the learned weekday pattern, while prior memory incidents keep the reflex cautious
- resembles_prior_incidents: True
- health_history: 76.55 -> 76.53

Prior incident memory:
- 2026-05-11T21:49:02.703942+00:00: high_memory_usage warning value=99.61 in guardian/incidents/incident-2026-05-11T214902.702883Z0000.md
- 2026-05-11T22:14:37.782126+00:00: high_memory_usage warning value=97.69 in guardian/incidents/incident-2026-05-11T221437.780998Z0000.md

## Reflex Signal

- observed_value: 0.05
- base_confidence: 0.1
- risk_class: low_confidence_watch
- circadian_adjustment: {"adjusted_confidence":0.05,"adjustment":-0.05,"base_confidence":0.1,"reason":"time-aware severity=warning; comparison bucket count=21"}
- likely_cause: time-aware warning reduced confidence while prior high-memory incident memory remains present
- resembles_prior_incidents: True
- prior_incident_count: 2
- latest_incident: guardian/incidents/incident-2026-05-11T221437.780998Z0000.md

## Sources

- system_state: state/system_state.json
- latest_telemetry: observability/snapshots/telemetry-2026-05-11T221435.452488Z0000.json
- baseline: guardian/baselines/telemetry_baseline.json
- circadian_baseline: guardian/baselines/circadian_baseline.json
- health_history: guardian/health/health_scores.json
- incident_memory: guardian/incidents/index.json
