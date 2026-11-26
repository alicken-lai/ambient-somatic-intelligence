# Historical DMN Governance Audit Summary

Phase: 1G.9 Larger Read-Only Historical DMN Governance Audit
Date: 2026-06-10
Status: Read-only redacted audit. No DMN memory was mutated.

Sample size: 50 of 1745 parsed DMN records.

Sampling method: first 5 records, last 5 records, keyword representatives for governance, telemetry, phase summaries, Guardian, and sync, then deterministic evenly spaced fill to 50.

## Metadata Coverage

| Field | Count | Coverage |
| --- | --- | --- |
| has_timestamp | 50 | 100.0% |
| has_source_node | 0 | 0.0% |
| has_privacy_class | 0 | 0.0% |
| has_retention_policy | 0 | 0.0% |
| has_replay_pointer | 0 | 0.0% |
| has_guardian_review | 1 | 2.0% |
| has_lineage | 0 | 0.0% |
| has_governance_state | 0 | 0.0% |

## Record Type Coverage

| Record Type | Count |
| --- | --- |
| governance | 4 |
| guardian_observation | 35 |
| phase_summary | 1 |
| system_observation | 3 |
| telemetry | 3 |
| unknown | 4 |

## Major Systemic Gaps

- Source node identity is usually absent or only inferable.
- Privacy class is usually absent and must be derived.
- Retention policy is usually absent.
- Per-record replay pointers are usually absent.
- Guardian review status is rarely explicit.
- Lineage and governance state are not native fields on historical DMN records.

## Risk Assessment

Historical DMN records can be summarized and audited, but most are not directly sync-ready. Sensitive operational records require summary-only handling and human review.

## Recommended Next Phase

Create schema-compatible sidecar proposals for source node, privacy class, retention policy, replay pointer, and governance state repair without rewriting `memory/dmn.jsonl`.

Updated DMN Governance Readiness Score: 26 / 30.

TurboVec remains paused.
