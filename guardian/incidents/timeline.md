# Guardian Incident Timeline

- generated_at: 2026-05-11T22:15:25.672370+00:00
- incident_count: 2
- latest_severity: warning
- severity_comparison: latest incident severity matches previous maximum
- repeated_anomaly_types: {"high_memory_usage":2}
- confidence_classes: {"low_confidence_watch":1}
- corrective_actions: none
- response_mode: recommendations only

## Events

### 2026-05-11T21:49:02.703942+00:00

- incident: guardian/incidents/incident-2026-05-11T214902.702883Z0000.md
- severity: warning
- anomaly_rules: high_memory_usage
- confidence_classes: {}
- telemetry_snapshots: observability/snapshots/telemetry-2026-05-11T133644.338636Z0000.json, observability/snapshots/telemetry-2026-05-11T214900.299316Z0000.json
- screenshot: tools/cua/screenshots/grafana-2026-05-11T214900.334186Z0000.png
- recommendations:
  - Review memory pressure and avoid launching additional heavy local tasks.

### 2026-05-11T22:14:37.782126+00:00

- incident: guardian/incidents/incident-2026-05-11T221437.780998Z0000.md
- severity: warning
- anomaly_rules: high_memory_usage
- confidence_classes: {"low_confidence_watch":1}
- telemetry_snapshots: observability/snapshots/telemetry-2026-05-11T215712.348987Z0000.json, observability/snapshots/telemetry-2026-05-11T221435.452488Z0000.json
- screenshot: tools/cua/screenshots/grafana-2026-05-11T221435.484630Z0000.png
- recommendations:
  - Review memory pressure and avoid launching additional heavy local tasks.
