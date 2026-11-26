# Report Determinism

## Review Scope

Reviewed report generators under `hermes/*/reports.py`, audit/release report generators, registries, and generated report artifacts.

## Findings

| Risk | Status | Stabilization Guidance |
| --- | --- | --- |
| Timestamp churn | Present in registries and generated events | Avoid committing regenerated registry timestamps unless tied to release evidence. |
| Non-deterministic ordering | Partially mitigated | Sort report inventories, relation maps, and coverage outputs consistently. |
| Randomized outputs | Not found | Current report generation does not use random sampling. |
| Unstable metrics | Present where reports rebuild lower layers | Prefer read-only snapshots for release audits. |

## Requirements

- Reports should remain stable when source data is unchanged.
- Output ordering should be deterministic.
- JSON serialization should use indentation and stable key ordering where practical.
- Generated-at metadata should be isolated from canonical content or omitted in release evidence.
- Report commands should avoid unnecessary rewrites when content is unchanged.

## Implemented In This Pass

- New RC reports use deterministic path lists and sorted relationship summaries.
- DMN validator normalizes legacy records without mutating DMN.
- Graph health report sorts relationship diversity and recommendations.
- Release health report uses explicit component scoring.

## Remaining Follow-Up

Introduce a shared stable report writer and read-only snapshot mode for older Phase 5-9 report builders.
