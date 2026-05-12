# Circadian Baseline Report

- generated_at: 2026-05-12T00:29:38.738351+00:00
- telemetry_count: 21
- current_timestamp: 2026-05-11T22:14:35.452488+00:00
- time_context.hour_of_day: 22
- time_context.weekday: monday
- time_context.day_type: weekday
- overall_deviation_severity: warning
- time_adjusted_reflex_confidence: 0.05
- corrective_actions: none
- response_mode: recommendations only

## Current Time-Aware Comparison

Comparison basis: `weekday`

| Metric | Current | Baseline Mean | Count | Stddev | Severity | Z Score |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| cpu_usage_percent | 5.44 | 6.4262 | 21 | 3.248 | normal | -0.3036 |
| memory_used_percent | 96.21 | 97.9329 | 21 | 0.8068 | warning | -2.1355 |
| disk_used_percent | 54.86 | 54.4305 | 21 | 0.2752 | elevated | 1.5607 |
| load_average_1m | 1.75 | 1.481 | 21 | 0.3069 | normal | 0.8765 |
| load_average_5m | 1.43 | 1.5495 | 21 | 0.0987 | elevated | -1.2107 |
| load_average_15m | 1.4 | 1.5481 | 21 | 0.1049 | elevated | -1.4118 |
| process_count | 667.0 | 659.4286 | 21 | 16.0047 | normal | 0.4731 |

## Group Counts

- matching_hour: 1
- matching_weekday: 21
- matching_day_type: 21

## Recommendations

- Continue observing current telemetry against the selected time-aware baseline.
