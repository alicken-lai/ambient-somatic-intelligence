# Temporal Health Score Report

- generated_at: 2026-05-11T22:02:48.229731+00:00
- telemetry_count: 20
- current_timestamp: 2026-05-11T21:57:12.348987+00:00
- overall_health_score: 76.53
- trend: stable
- corrective_actions: none
- response_mode: recommendations only

## Subsystems

| Subsystem | Score | Raw Score | Incident Penalty | Incident Links |
| --- | ---: | ---: | ---: | ---: |
| cpu_health | 100.0 | 100.0 | 0.0 | 0 |
| memory_health | 43.93 | 46.93 | 3.0 | 1 |
| disk_health | 68.82 | 68.82 | 0.0 | 0 |
| load_health | 100.0 | 100.0 | 0.0 | 0 |
| process_health | 69.89 | 69.89 | 0.0 | 0 |

## Recent History

| Timestamp | Health Score |
| --- | ---: |
| 2026-05-11T21:57:09.528139+00:00 | 76.55 |
| 2026-05-11T21:57:09.846297+00:00 | 76.53 |
| 2026-05-11T21:57:10.164053+00:00 | 76.56 |
| 2026-05-11T21:57:10.481193+00:00 | 76.54 |
| 2026-05-11T21:57:10.788755+00:00 | 76.54 |
| 2026-05-11T21:57:11.092288+00:00 | 76.56 |
| 2026-05-11T21:57:11.409874+00:00 | 76.55 |
| 2026-05-11T21:57:11.725760+00:00 | 76.55 |
| 2026-05-11T21:57:12.036208+00:00 | 76.55 |
| 2026-05-11T21:57:12.348987+00:00 | 76.53 |

## Recommendations

- Keep memory_health linked to incident memory during future reflex checks.
- Observe disk_health; score is below 70.
- Observe memory_health; score is below 70.
- Observe process_health; score is below 70.
