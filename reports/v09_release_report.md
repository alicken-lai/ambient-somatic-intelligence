# Hermes-ASI v0.9 Release Report

RC Health: 95.78
Release Ready: True
Recommendation: ready for v0.9.0-rc1

## Component Scores

- test_health: 100.00
- documentation_health: 100.00
- audit_health: 95.38
- graph_health: 97.00
- dmn_health: 99.83
- report_stability: 82.00

## Audit Summary

- Institutional Health: 95.38
- Graph Health: 97.00
- DMN Valid Events: 1753/1756

## Known Risks

- Report snapshot mode is documented but not fully implemented across all generators.
- Legacy DMN records are normalized by validator but not migrated.
- Graph health is derived from release artifacts rather than a persisted graph database.
