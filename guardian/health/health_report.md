# Temporal Health Score Report

- generated_at: 2026-11-20T06:55:01.160910+00:00
- telemetry_count: 88420
- current_timestamp: 2026-11-20T06:44:05.104497+00:00
- overall_health_score: 65.93
- trend: degrading
- corrective_actions: none
- response_mode: recommendations only

## Subsystems

| Subsystem | Score | Raw Score | Incident Penalty | Incident Links |
| --- | ---: | ---: | ---: | ---: |
| cpu_health | 63.98 | 63.98 | 0.0 | 0 |
| memory_health | 74.63 | 80.63 | 6.0 | 2 |
| disk_health | 61.45 | 61.45 | 0.0 | 0 |
| load_health | 51.51 | 51.51 | 0.0 | 0 |
| process_health | 78.08 | 78.08 | 0.0 | 0 |

## Recent History

| Timestamp | Health Score |
| --- | ---: |
| 2026-11-20T06:19:07.223871+00:00 | 81.12 |
| 2026-11-20T06:24:04.635490+00:00 | 80.76 |
| 2026-11-20T06:24:04.693045+00:00 | 81.29 |
| 2026-11-20T06:29:04.162881+00:00 | 78.63 |
| 2026-11-20T06:29:04.219308+00:00 | 77.52 |
| 2026-11-20T06:34:04.141554+00:00 | 80.06 |
| 2026-11-20T06:34:04.835163+00:00 | 79.73 |
| 2026-11-20T06:39:06.781661+00:00 | 70.39 |
| 2026-11-20T06:39:06.915757+00:00 | 68.75 |
| 2026-11-20T06:44:05.104497+00:00 | 65.93 |

## Recommendations

- Keep memory_health linked to incident memory during future reflex checks.
- Observe cpu_health; score is below 70.
- Observe disk_health; score is below 70.
- Observe load_health; score is below 70.
- Review recent local workload before expanding CUA activity.
