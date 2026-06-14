# Deliberation Quality Report

Benchmarks evaluated: 25
Overall quality: 66.52
Average safety score: 70.71
Average verification score: 52.87

## Mode Comparison

| Mode | Wins | Average Overall |
| --- | ---: | ---: |
| single | 11 | 60.26 |
| light | 7 | 69.36 |
| full | 7 | 69.95 |

## Failure Analysis

- Unsupported claims remain the primary hallucination-risk proxy.
- Guardian-required tasks are expected to preserve warnings instead of silently executing.
- Trace completeness is scored independently from answer quality.

## Recommendations

- Increase verifier evidence sources before enabling real provider children.
- Keep disabled CLI providers observable but non-invokable until explicitly configured.
- Track scorecard trends across releases before promoting full deliberation as default.
