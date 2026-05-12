# Decision Boundary Protocol

Ambient Somatic Intelligence uses four boundary levels to describe what the system may do.

`corrective_actions` remain `none` by default across the current operating stack.

## Levels

`OBSERVE_ONLY`

- Read-only observation and query actions.
- No corrective changes.
- No execution of derived actions.

`RECOMMEND_ONLY`

- Derived analysis, reports, and append-only summaries.
- May append internal memory summaries.
- No external execution.

`PREPARE_FOR_APPROVAL`

- Guarded readiness checks and safety probes.
- Used to prepare evidence for human review.
- No external execution.

`EXECUTE_ALLOWED`

- Explicitly approved execution only.
- No current routes are assigned to this level.

## Route Map

| Route | Level |
| --- | --- |
| `system-info` | `OBSERVE_ONLY` |
| `uptime` | `OBSERVE_ONLY` |
| `disk-usage` | `OBSERVE_ONLY` |
| `memory-usage` | `OBSERVE_ONLY` |
| `telemetry-local` | `RECOMMEND_ONLY` |
| `vision-capture` | `OBSERVE_ONLY` |
| `vision-capture-smoke` | `OBSERVE_ONLY` |
| `vision-capture-ocr-smoke` | `OBSERVE_ONLY` |
| `cua-guarded-smoke` | `PREPARE_FOR_APPROVAL` |
| `guardian-reflex-once` | `PREPARE_FOR_APPROVAL` |
| `incident-recall-build` | `RECOMMEND_ONLY` |
| `baseline-learn-build` | `RECOMMEND_ONLY` |
| `health-score-build` | `RECOMMEND_ONLY` |
| `memory-pressure-diagnose` | `RECOMMEND_ONLY` |
| `circadian-baseline-build` | `RECOMMEND_ONLY` |
| `system-state-build` | `RECOMMEND_ONLY` |
| `somatic-dashboard-build` | `RECOMMEND_ONLY` |
| `daily-digest-build` | `RECOMMEND_ONLY` |
| `anomaly-explain-build` | `RECOMMEND_ONLY` |
| `memory-integrity-audit` | `RECOMMEND_ONLY` |
| `state-query` | `OBSERVE_ONLY` |
| `self-reflect-build` | `RECOMMEND_ONLY` |
| `operator-briefing-build` | `RECOMMEND_ONLY` |
| `approval-packet-build` | `RECOMMEND_ONLY` |

## Operating Rules

- Default system behavior stays non-corrective.
- Guardian logs now include the boundary level for routed actions.
- Routes may move to a higher boundary only through explicit protocol updates.
- The `EXECUTE_ALLOWED` level stays empty until a formally approved execution path exists.

## Operational Reading

- `OBSERVE_ONLY` covers sensing and inspection.
- `RECOMMEND_ONLY` covers synthesis and append-only memory.
- `PREPARE_FOR_APPROVAL` covers guarded readiness.
- `EXECUTE_ALLOWED` remains reserved.
