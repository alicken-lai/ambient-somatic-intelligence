# Memory Pressure Diagnosis

- generated_at: 2026-05-11T22:04:33.278382+00:00
- latest_snapshot: observability/snapshots/telemetry-2026-05-11T215712.348987Z0000.json
- corrective_actions: none
- response_mode: recommendations only

## Finding

memory_health reached 0.0 because the prior formula used absolute z-score deviation against a very narrow memory baseline.
The latest memory_used_percent is 97.69%, which is -1.7725 points from the baseline mean of 99.4625%.
Because that delta is below the mean, the zero score was a scoring artifact, not evidence of worsening memory pressure.

## Current Memory

| Field | Value |
| --- | ---: |
| total_bytes | 16528687104 |
| used_bytes | 16147693568 |
| free_bytes | 380993536 |
| used_percent | 97.69 |

## Baseline Comparison

| Metric | Value |
| --- | ---: |
| baseline_mean | 99.4625 |
| baseline_min | 99.28 |
| baseline_max | 99.61 |
| baseline_stddev | 0.1413 |
| delta_from_mean | -1.7725 |

## Scoring

| Score | Value |
| --- | ---: |
| legacy_memory_score | 0.0 |
| adjusted_memory_health | 43.93 |
| adjusted_raw_score | 46.93 |
| incident_penalty | 3.0 |
| deviation_score | 100.0 |
| absolute_pressure_score | 46.93 |

## Docker Desktop

- vm_reservation_detected: True
- vm_memory_mib: 8192
- vm_memory_gib: 8.0

| Container | Memory | Memory % | CPU % |
| --- | ---: | ---: | ---: |
| ambient-grafana | 76.89MiB / 7.75GiB | 0.97% | 0.03% |
| ambient-prometheus | 49.62MiB / 7.75GiB | 0.63% | 0.00% |

## Top Memory Consumers

| PID | RSS MB | Memory % | Command |
| ---: | ---: | ---: | --- |
| 12898 | 3201.6 | 19.5 | `/System/Library/Frameworks/Virtualization.framework/Versions/A/XPCServices/com.apple.Virtualization.VirtualMachine.xpc/Contents/MacOS/com.apple.Virtualization.VirtualMachine` |
| 688 | 326.3 | 2.0 | `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser` |
| 27271 | 243.6 | 1.5 | `/Applications/AnyDesk.app/Contents/MacOS/AnyDesk --backend` |
| 3719 | 223.2 | 1.4 | `/Applications/Brave Browser.app/Contents/Frameworks/Brave Browser Framework.framework/Versions/145.1.87.192/Helpers/Brave Browser Helper (Renderer).app/Contents/MacOS/Brave Browser Helper (Renderer) --type=renderer --met` |
| 630 | 222.1 | 1.4 | `/System/Library/PrivateFrameworks/MediaAnalysis.framework/Versions/A/mediaanalysisd` |
| 12819 | 213.2 | 1.3 | `/Applications/Docker.app/Contents/MacOS/com.docker.backend services` |
| 1217 | 204.6 | 1.2 | `/System/Volumes/Preboot/Cryptexes/App/System/Applications/Safari.app/Contents/MacOS/Safari` |
| 13136 | 204.2 | 1.2 | `codex` |
| 13040 | 186.3 | 1.1 | `/Applications/Docker.app/Contents/MacOS/Docker Desktop.app/Contents/MacOS/Docker Desktop --analytics-enabled=true --name=login` |
| 19872 | 174.1 | 1.1 | `/Applications/Brave Browser.app/Contents/Frameworks/Brave Browser Framework.framework/Versions/145.1.87.192/Helpers/Brave Browser Helper (Renderer).app/Contents/MacOS/Brave Browser Helper (Renderer) --type=renderer --met` |

## Risk Assessment

- true_risk: watch
- scoring_artifact: True
- swap: vm.swapusage: total = 0.00M  used = 0.00M  free = 0.00M  (encrypted)
- summary: memory_health was zero from formula shape, while host memory still deserves watch-level pressure monitoring

## Recommendations

- Continue observation; do not restart Docker or kill processes automatically.
- Treat Docker Desktop's VM reservation as a major host-memory context factor.
- Avoid adding heavier local workloads while host memory remains above 95%.
- Manually review Docker Desktop memory allocation later if sustained pressure continues.
- Manually close unused browser or remote desktop sessions only if interactive performance degrades.
