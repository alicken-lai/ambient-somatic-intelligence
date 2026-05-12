# Guardian Dream

- generated_at: 2026-05-12T08:47:35.570047+00:00
- incident_window: 5
- replayed_incident_count: 2
- dominant_theme: repeated memory pressure with watch-level reflex suppression
- corrective_actions: none
- response_mode: recommendations only

## Replay Window

### guardian/incidents/incident-2026-05-11T214902.702883Z0000.md

- what_happened: high_memory_usage=99.61 (warning)
- what_was_predicted: Latest anomaly explanation framed this as a watch-level deviation with no corrective action.
- what_actually_happened: Observed high_memory_usage at 99.61 with severity warning.
- alternative_interpretation: The replay does not show a strong alternative beyond the observed deviation.
- possible_false_positive: possible
- possible_missed_warning: The repeated pattern should have raised the next memory warning sooner.
- confidence_recalibration_suggestion: Keep reflex confidence conservative, but escalate repeated memory warnings to review.

### guardian/incidents/incident-2026-05-11T221437.780998Z0000.md

- what_happened: high_memory_usage=97.69 (warning)
- what_was_predicted: Latest anomaly explanation framed this as a watch-level deviation with no corrective action.
- what_actually_happened: Observed high_memory_usage at 97.69 with severity warning.
- alternative_interpretation: This may be a scoring artifact amplified by memory-scoring logic rather than a structural fault.
- possible_false_positive: likely
- possible_missed_warning: The earlier incident established the pattern; repeat escalation remains the key missed warning.
- confidence_recalibration_suggestion: Lower confidence for this rule family and treat the warning as artifact-prone.

## Recalibration Candidates

- {"incident":"guardian/incidents/incident-2026-05-11T214902.702883Z0000.md","recalibration_suggestion":"Keep reflex confidence conservative, but escalate repeated memory warnings to review.","rule":"high_memory_usage","suggested_confidence":0.15}
- {"incident":"guardian/incidents/incident-2026-05-11T221437.780998Z0000.md","recalibration_suggestion":"Lower confidence for this rule family and treat the warning as artifact-prone.","rule":"high_memory_usage","suggested_confidence":0.2}

## Sources

- incident_memory: guardian/incidents/index.json
- anomaly_explanations: guardian/explanations/latest_anomaly.md
- simulations: guardian/simulations/latest_simulation.json
- self_reflections: docs/reflections/latest.md
- operator_briefings: docs/briefings/latest_operator_briefing.md
