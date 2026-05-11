# Temporal Health Score Report

- generated_at: 2026-05-11T21:58:20.070467+00:00
- telemetry_count: 20
- current_timestamp: 2026-05-11T21:57:12.348987+00:00
- overall_health_score: 54.75
- trend: stable
- corrective_actions: none
- response_mode: recommendations only

## Subsystems

| Subsystem | Score | Raw Score | Incident Penalty | Incident Links |
| --- | ---: | ---: | ---: | ---: |
| cpu_health | 84.87 | 84.87 | 0.0 | 0 |
| memory_health | 0.0 | 0.0 | 3.0 | 1 |
| disk_health | 68.82 | 68.82 | 0.0 | 0 |
| load_health | 50.19 | 50.19 | 0.0 | 0 |
| process_health | 69.89 | 69.89 | 0.0 | 0 |

## Recent History

| Timestamp | Health Score |
| --- | ---: |
| 2026-05-11T21:57:09.528139+00:00 | 56.65 |
| 2026-05-11T21:57:09.846297+00:00 | 56.97 |
| 2026-05-11T21:57:10.164053+00:00 | 55.5 |
| 2026-05-11T21:57:10.481193+00:00 | 56.75 |
| 2026-05-11T21:57:10.788755+00:00 | 55.15 |
| 2026-05-11T21:57:11.092288+00:00 | 54.73 |
| 2026-05-11T21:57:11.409874+00:00 | 55.19 |
| 2026-05-11T21:57:11.725760+00:00 | 54.81 |
| 2026-05-11T21:57:12.036208+00:00 | 55.63 |
| 2026-05-11T21:57:12.348987+00:00 | 54.75 |

## Recommendations

- Keep memory_health linked to incident memory during future reflex checks.
- Observe disk_health; score is below 70.
- Observe load_health; score is below 70.
- Observe memory_health; score is below 70.
- Observe process_health; score is below 70.
