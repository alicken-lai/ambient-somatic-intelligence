# Recalibration Queue

- generated_at: 2026-05-12T08:50:15.012036+00:00
- queue_count: 2
- corrective_actions: none
- response_mode: recommendations only

## Queue Items

### high_memory_usage

- incident: guardian/incidents/incident-2026-05-11T214902.702883Z0000.md
- recommended_confidence: 0.15
- candidate_suggestion: Keep reflex confidence conservative, but escalate repeated memory warnings to review.
- expected_benefit: Keeps repeated high-memory warnings visible in review while reducing the chance that low-confidence artifacts remain underweighted.
- risk_of_overfitting: medium
- required_approval_level: PREPARE_FOR_APPROVAL
- rollback_note: Discard the queue item and preserve the current calibration if review rejects the candidate.
- source_evidence:
  - dream_candidate=guardian/dreams/latest_dream.json
  - incident=guardian/incidents/incident-2026-05-11T214902.702883Z0000.md
  - rule=high_memory_usage
  - incident_count=2
  - repeated_anomaly_types={"high_memory_usage":2}
  - confidence_classes={"low_confidence_watch":1}
  - latest_reflex_confidence=0.05
  - calibration_latest_rule=high_memory_usage

### high_memory_usage

- incident: guardian/incidents/incident-2026-05-11T221437.780998Z0000.md
- recommended_confidence: 0.2
- candidate_suggestion: Lower confidence for this rule family and treat the warning as artifact-prone.
- expected_benefit: Keeps repeated high-memory warnings visible in review while reducing the chance that low-confidence artifacts remain underweighted.
- risk_of_overfitting: medium
- required_approval_level: PREPARE_FOR_APPROVAL
- rollback_note: Discard the queue item and preserve the current calibration if review rejects the candidate.
- source_evidence:
  - dream_candidate=guardian/dreams/latest_dream.json
  - incident=guardian/incidents/incident-2026-05-11T221437.780998Z0000.md
  - rule=high_memory_usage
  - incident_count=2
  - repeated_anomaly_types={"high_memory_usage":2}
  - confidence_classes={"low_confidence_watch":1}
  - latest_reflex_confidence=0.05
  - calibration_latest_rule=high_memory_usage

## Incident Patterns

- {"confidence_classes":{"low_confidence_watch":1},"incident_count":2,"latest_severity":"warning","repeated_anomaly_types":{"high_memory_usage":2},"severity_by_rule":{"high_memory_usage":["warning","warning"]}}

## Calibration Context

- {"anomaly_count":1,"latest_confidence":0.1,"latest_confidence_class":"low_confidence_watch","latest_recommendation":"Review memory pressure and avoid launching additional heavy local tasks.","latest_rule":"high_memory_usage","latest_true_anomaly":false}

## Sources

- dream: guardian/dreams/latest_dream.json
- system_state: state/system_state.json
- incident_patterns: guardian/incidents/index.json
- reflex_confidence_calibration: guardian/incidents/reflex_confidence_calibration.json
