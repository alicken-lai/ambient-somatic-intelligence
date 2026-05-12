# Pre-Accident Simulation

- generated_at: 2026-05-12T08:41:56.890236+00:00
- simulation_active: true
- predicted_risk: review
- confidence: 0.6
- corrective_actions: none
- response_mode: recommendations only

## Predicted Risk

Overall predicted risk is review with 0.6 confidence.
Primary driver: memory_used_percent.
Incident similarity: memory_used_percent.
False-positive likelihood: low.

## Horizon Summary

- 5m: watch
- 30m: review
- 2h: review

## Active Warnings

### disk_used_percent

- observed_value: 54.86
- flat_baseline: mean=53.965, severity=elevated, z=1.7322, delta=0.555
- circadian_baseline: basis=weekday, mean=54.4305, severity=elevated, z=1.5607, delta=0.4295
- likely_degradation_path: disk headroom likely tightens slowly, but the current drift looks bounded
- subsystem_impact: disk capacity margin; current disk_health score is 68.82
- incident_similarity: {"matches":[],"repeat_count":0,"resembles_prior_incidents":false}
- confidence: 0.25
- false_positive_likelihood: medium

#### 5 Minutes

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

#### 30 Minutes

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

#### 2 Hours

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

### load_average_15m

- observed_value: 1.4
- flat_baseline: mean=1.745, severity=elevated, z=-1.7303, delta=-0.145
- circadian_baseline: basis=weekday, mean=1.5481, severity=elevated, z=-1.4118, delta=-0.1481
- likely_degradation_path: load stays modestly elevated against the learned baseline
- subsystem_impact: load balancing and short-term scheduling; current load_health score is 100.0
- incident_similarity: {"matches":[],"repeat_count":0,"resembles_prior_incidents":false}
- confidence: 0.2
- false_positive_likelihood: medium

#### 5 Minutes

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

#### 30 Minutes

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

#### 2 Hours

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

### load_average_5m

- observed_value: 1.43
- flat_baseline: mean=1.745, severity=elevated, z=1.7103, delta=0.085
- circadian_baseline: basis=weekday, mean=1.5495, severity=elevated, z=-1.2107, delta=-0.1195
- likely_degradation_path: load stays modestly elevated against the learned baseline
- subsystem_impact: load balancing and short-term scheduling; current load_health score is 100.0
- incident_similarity: {"matches":[],"repeat_count":0,"resembles_prior_incidents":false}
- confidence: 0.2
- false_positive_likelihood: medium

#### 5 Minutes

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

#### 30 Minutes

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

#### 2 Hours

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

### memory_used_percent

- observed_value: 96.21
- flat_baseline: mean=99.4625, severity=elevated, z=-1.2916, delta=-0.1825
- circadian_baseline: basis=weekday, mean=97.9329, severity=warning, z=-2.1355, delta=-1.7229
- likely_degradation_path: continued memory pressure could recreate the earlier high-memory pattern and push the host toward a repeat incident
- subsystem_impact: memory subsystem headroom and local task scheduling; current memory_health score is 43.93
- incident_similarity: {"matches":[{"incident":"guardian/incidents/incident-2026-05-11T214902.702883Z0000.md","rule":"high_memory_usage","severity":"warning","value":99.61},{"incident":"guardian/incidents/incident-2026-05-11T221437.780998Z0000.md","rule":"high_memory_usage","severity":"warning","value":97.69}],"repeat_count":2,"resembles_prior_incidents":true}
- confidence: 0.6
- false_positive_likelihood: low

#### 5 Minutes

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

#### 30 Minutes

- projected_risk: review
- expected_behavior: continued drift toward review

#### 2 Hours

- projected_risk: review
- expected_behavior: continued drift toward review

### reflex_confidence

- observed_value: 0.05
- flat_baseline: mean=0.1, severity=watch, z=None, delta=-0.05
- circadian_baseline: basis=weekday, mean=0.05, severity=warning, z=None, delta=-0.05
- likely_degradation_path: reflex confidence stays suppressed while incident memory remains active
- subsystem_impact: decision routing and conservative behavior
- incident_similarity: {"matches":[{"incident":"guardian/incidents/incident-2026-05-11T214902.702883Z0000.md","rule":"high_memory_usage","severity":"warning","value":99.61},{"incident":"guardian/incidents/incident-2026-05-11T221437.780998Z0000.md","rule":"high_memory_usage","severity":"warning","value":97.69}],"repeat_count":2,"resembles_prior_incidents":true}
- confidence: 0.6
- false_positive_likelihood: medium

#### 5 Minutes

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

#### 30 Minutes

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

#### 2 Hours

- projected_risk: watch
- expected_behavior: bounded watch-level persistence

## Sources

- system_state: state/system_state.json
- latest_telemetry: observability/snapshots/telemetry-2026-05-11T221435.452488Z0000.json
- baseline: guardian/baselines/telemetry_baseline.json
- circadian_baseline: guardian/baselines/circadian_baseline.json
- incident_memory: guardian/incidents/index.json
- anomaly_explanations: guardian/explanations/latest_anomaly.md
