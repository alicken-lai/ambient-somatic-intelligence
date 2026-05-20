# Persistence Boundary Report

**Audit date:** 2026-05-20

## Append-only boundaries

| Store | Role | Required in freeze? |
|-------|------|---------------------|
| `memory/dmn.jsonl` | DMN append-only memory | No |
| `governance/audit/decisions.jsonl` | Guardian decisions | No |
| `governance/audit/incidents.jsonl` | Incident audit | No |
| `logs/*.jsonl` | Action telemetry | No |

## Score / simulation persistence

| Path | Written by | Freeze impact |
|------|------------|---------------|
| `v070/reports/inter_sovereign_timeseries.json` | Optional CLI simulation | Pre-existing validation artifact |
| `v071`–`v077/reports/*_timeseries.json` | Optional CLI | Pre-existing |
| `v07x_freeze/freeze_snapshot/civilization_freeze_snapshot.json` | Freeze evaluator | **Freeze output** (scores only) |

Civilization scores are computable entirely in-memory; persistence is optional for human review.

**Persistence boundary: PASS**
