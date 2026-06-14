# Decision Log: Larger Historical DMN Governance Audit

Date: 2026-06-10  
Phase: 1G.9 Larger Read-Only Historical DMN Governance Audit  
Status: Accepted as read-only audit artifact. No migration, sync, or implementation authorized.

## Decision

Run a deterministic read-only audit over a larger sample of historical DMN records.

Write redacted audit outputs only to `reports/dmn_audit/`.

TurboVec remains paused.

## Created Files

- `tools/audit_historical_dmn_governance.py`
- `reports/dmn_audit/historical_dmn_governance_audit.json`
- `reports/dmn_audit/historical_dmn_governance_audit_summary.md`
- `reports/dmn_audit/historical_dmn_sync_eligibility_distribution.md`
- `reports/dmn_audit/historical_dmn_privacy_confidence_report.md`
- `reports/dmn_audit/historical_dmn_replay_coverage_report.md`
- `tests/test_historical_dmn_governance_audit.py`

## Sample

Sample size: 50 records from 1506 parsed DMN records.

Sampling method:

- first 5 records;
- last 5 records;
- keyword representatives for governance, telemetry, phase summaries, Guardian, and sync;
- deterministic evenly spaced fill to 50 records.

## Findings

Metadata coverage:

- timestamp: 50 / 50 (100.0%)
- source node: 0 / 50 (0.0%)
- privacy class: 2 / 50 (4.0%)
- retention policy: 1 / 50 (2.0%)
- replay pointer: 0 / 50 (0.0%)
- Guardian review: 4 / 50 (8.0%)
- lineage: 0 / 50 (0.0%)
- governance state: 1 / 50 (2.0%)

Privacy confidence:

- high: 36
- medium: 11
- unknown: 3

Sync eligibility:

- not eligible sensitive: 36
- not eligible missing replay: 5
- eligible governance only: 6
- requires human review: 3

Replay coverage:

- derived: 4
- missing: 14
- unknown: 32
- explicit: 0

## Risk

Historical DMN is audit-readable but not cross-node-sync-ready. Sensitive operational records dominate the sample, and explicit replay pointers, source node identity, lineage, retention policy, privacy class, and governance state are mostly absent.

## Readiness Score

Previous DMN Governance Readiness Score: 25 / 30.

Updated DMN Governance Readiness Score: 26 / 30.

The score increases only slightly because the project now has quantitative evidence, but the audit shows substantial metadata gaps remain.

## Recommended Next Phase

Create non-mutating metadata sidecar proposals for historical DMN records:

1. source node repair sidecar;
2. privacy class sidecar;
3. retention policy sidecar;
4. replay pointer sidecar;
5. governance state sidecar.

Do not modify `memory/dmn.jsonl`.
