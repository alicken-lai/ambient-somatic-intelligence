# Guardian Reflex Confidence Calibration

- generated_at: 2026-05-11T22:14:35.447810+00:00
- anomaly_count: 1
- corrective_actions: none
- response_mode: recommendations only

## Classification

| Class | Count |
| --- | ---: |
| low_confidence_watch | 1 |
| medium_confidence_review | 0 |
| high_confidence_incident | 0 |

## Anomalies

| Rule | Confidence | Class | True Anomaly | Scoring Artifact | Baseline Direction | Swap Used | Max Container Memory |
| --- | ---: | --- | --- | --- | --- | ---: | ---: |
| high_memory_usage | 0.1 | low_confidence_watch | False | True | below_baseline | 0.00M | 0.97 |

## Context

```json
{
  "docker_stats": [
    {
      "cpu_percent": "0.05%",
      "memory_percent": "0.97%",
      "memory_usage": "77.04MiB / 7.75GiB",
      "name": "ambient-grafana"
    },
    {
      "cpu_percent": "0.00%",
      "memory_percent": "0.62%",
      "memory_usage": "48.9MiB / 7.75GiB",
      "name": "ambient-prometheus"
    }
  ],
  "docker_vm": {
    "cpus": 10,
    "detected": true,
    "memory_mib": 8192,
    "memory_percent": 0.2,
    "pid": 12894,
    "rss_mb": 32.8
  },
  "latest_telemetry": "observability/snapshots/telemetry-2026-05-11T215712.348987Z0000.json",
  "swap": {
    "raw": "vm.swapusage: total = 0.00M  used = 0.00M  free = 0.00M  (encrypted)",
    "used": "0.00M",
    "used_mb": 0.0
  }
}
```

## Recommendations

- Review memory pressure and avoid launching additional heavy local tasks.
