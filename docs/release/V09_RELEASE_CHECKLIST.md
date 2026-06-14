# Hermes-ASI v0.9 Release Checklist

## Tests

- [x] Institutional audit tests pass.
- [x] Phase 8/9/audit focused tests pass.
- [x] DMN taxonomy tests pass.
- [x] Graph health tests pass.
- [x] Release health tests pass.
- [x] Report determinism tests pass for new RC reports.

## Audit Status

- [x] Institutional integration audit completed.
- [x] Kernel dependency audit documented.
- [x] Lifecycle audit documented.
- [x] Governance audit documented.
- [x] Release review documented.

## Documentation

- [x] v0.9 architecture document exists.
- [x] DMN event taxonomy exists.
- [x] Artifact inventory exists.
- [x] Version manifest exists.

## Governance

- [x] Guardian authority unchanged.
- [x] Provider permissions unchanged.
- [x] Credential policies unchanged.
- [x] Identity/reality/release reports remain advisory.

## DMN Validation

- [x] `schemas/dmn_event.schema.json` exists.
- [x] `tools/validate_dmn_events.py` exists.
- [x] Validation report generation supported.

## Graph Health

- [x] `hermes/graph/graph_health.py` exists.
- [x] `hermes graph-health-report` exists.

## Report Stability

- [x] Determinism audit documented.
- [x] New RC report generators use stable inventory/order.
- [ ] Legacy report builders still need shared snapshot mode.

## Release Artifacts

- [x] `reports/institutional_audit_report.md/json`
- [x] `reports/graph_health_report.md/json`
- [x] `reports/v09_release_report.md/json`

## Recommendation

Proceed to v0.9.0-rc1 only as an advisory institutional intelligence release candidate.
