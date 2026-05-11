# Pattern Threshold Baseline Report

- generated_at: 2026-05-11T21:55:23.009180+00:00
- telemetry_count: 4
- current_timestamp: 2026-05-11T21:49:00.299316+00:00
- overall_deviation_severity: elevated
- corrective_actions: none
- response_mode: recommendations only

## Metrics

| Metric | Current | Mean | Min | Max | Stddev | Rolling Mean | Severity | Incident Links |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| cpu_usage_percent | 17.56 | 9.2 | 2.12 | 17.56 | 5.4963 | 11.56 | elevated | 0 |
| memory_used_percent | 99.28 | 99.4625 | 99.28 | 99.61 | 0.1413 | 99.4933 | elevated | 1 |
| disk_used_percent | 54.52 | 53.965 | 53.78 | 54.52 | 0.3204 | 54.0267 | elevated | 0 |
| load_average_1m | 2.8 | 1.68 | 1.29 | 2.8 | 0.647 | 1.7933 | elevated | 0 |
| load_average_5m | 1.83 | 1.745 | 1.71 | 1.83 | 0.0497 | 1.75 | elevated | 0 |
| load_average_15m | 1.6 | 1.745 | 1.6 | 1.8 | 0.0838 | 1.7267 | elevated | 0 |
| process_count | 667.0 | 632.0 | 617.0 | 667.0 | 20.3224 | 637.0 | elevated | 0 |

## Recommendations

- Continue observing memory_used_percent; it is linked to prior incident memory.

## Incident Links

- memory_used_percent: high_memory_usage in guardian/incidents/incident-2026-05-11T214902.702883Z0000.md (warning)
