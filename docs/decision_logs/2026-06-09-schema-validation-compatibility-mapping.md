# 2026-06-09 Schema Validation Compatibility Mapping

## Decision

Create Phase 1C schema examples and compatibility mapping artifacts.

This phase proves that Phase 1B schemas can represent synthetic ASI-relevant memory events, recall evidence packets, and embedding sidecars without implementing TurboVec or changing production behavior.

## Findings

- Memory event examples can represent text, sensor, somatic, agent action, Guardian observation, and governance decision records.
- Sensor examples can represent WiFi CSI, power anomaly, temperature, and humidity through `sensor_type`, `modality`, tags, and summary.
- Recall evidence examples can represent candidate recall with Guardian-visible evidence and no decision/action authorization.
- Embedding sidecar examples can bind synthetic embeddings to stable source record ids without storing vector payloads.
- Existing DMN and layered memory can be mapped into the new schema through wrappers, but not every field is directly available.

## Risks

- Existing historical records do not contain stable `record_id` values.
- Existing records do not consistently contain privacy class, retention policy, source node, replay checksum, causal event id, or embedding reference.
- Wrapper generation must persist derived ids to avoid drift.
- Privacy class defaults are risky; old records should not be embedded or synchronized until reviewed.
- JSON Schema validation checks shape, not semantic truth.

## Readiness Score

Phase 1B estimate: 21 / 30.

After Phase 1C examples and mapping, estimated readiness is 24 / 30.

| Category | Estimate |
| --- | ---: |
| Architecture | 4 / 5 |
| Memory Schema | 4 / 5 |
| Replay Compatibility | 4 / 5 |
| Guardian Compatibility | 4 / 5 |
| Governance Compatibility | 4 / 5 |
| Synchronization Compatibility | 4 / 5 |

The score remains below adapter-ready because wrapper generation, enforcement, stale-index checks, privacy review, and recall evidence emission are not implemented.

## Recommended Next Phase

Phase 1D: Non-Production Wrapper Dry Run and Evidence Audit.

Recommended deliverables:

- Dry-run wrapper generator or audit report.
- No mutation of existing memory files.
- Sample wrappers for selected existing DMN/layer records.
- Validation report showing which current records can satisfy Phase 1B schema fields.
- Privacy and encoding-quality audit before embedding.

## Rollback

Rollback is documentation/example-only. Remove or supersede the examples and docs with a new decision log entry. Do not delete this decision from history.

## Approval

User requested Phase 1C on 2026-06-09. Guardian classified the documentation-only/example-only action as `ALLOW` with boundary level `OBSERVE_ONLY`.

