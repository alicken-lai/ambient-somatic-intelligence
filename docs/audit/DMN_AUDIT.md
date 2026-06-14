# DMN Integration Audit

## Current DMN Role

DMN is the append-only institutional memory surface. It records operator-relevant milestones, tool outcomes, telemetry ticks, and governance events.

## Kernel Write/Consume Map

| Kernel | Writes DMN directly | Consumes DMN directly | Notes |
| --- | --- | --- | --- |
| Deliberation | No | No | Produces traces/reports. |
| Verification | No | No | Produces claim/evidence registries. |
| Acquisition | No | No | Produces evidence and knowledge index reports. |
| Calibration | No | No | Uses reports/registries. |
| Reality Alignment | No | No | Produces belief/reality reports. |
| Identity | No | Yes, summaries only | Timeline reads recent `memory/dmn.jsonl` entries. |
| Operator/Hermes bridge | Yes | Yes | `dmn_append`, `memory_recall`, `dmn_search`. |

## Missing Event Types

- `kernel_report_generated`
- `belief_challenged`
- `identity_continuity_checked`
- `audit_report_generated`

## Redundancy

- Telemetry ticks can dominate recent DMN summaries.
- Commit/milestone records and generated reports sometimes overlap.

## Scalability Risks

- `memory/dmn.jsonl` is append-only and can grow without indexing discipline.
- Identity timeline currently samples recent DMN entries, not semantic milestones.

## Recommendation

Keep DMN append-only, but add a future event taxonomy and milestone index. Do not let kernels write DMN automatically without Guardian-scoped approval.
