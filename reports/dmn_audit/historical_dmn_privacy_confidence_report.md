# Historical DMN Privacy Confidence Report

Phase: 1G.9
Status: Read-only audit with redacted summaries.

## Privacy Confidence Distribution

| Privacy Confidence | Count | Percentage |
| --- | --- | --- |
| high | 35 | 70.0% |
| low | 1 | 2.0% |
| medium | 10 | 20.0% |
| unknown | 4 | 8.0% |

## High-Risk Categories

- Telemetry and local system observations.
- Hook records containing conversation IDs, generation IDs, workspace roots, or local paths.
- Records with machine names, host fields, or operational metrics.

## Classification Uncertainty

Privacy confidence is derived heuristically because historical DMN records usually lack native `privacy_class` metadata.

## Recommendation

Add non-mutating privacy sidecars or wrappers before any sync, embedding, or broader recall indexing of historical DMN records.
