# Agency Boundary Validation — v0.7.7

**Generated:** 2026-05-20  
**Gate:** `CognitiveAgencyBoundaryScore` ≥ 0.90

## Validation checklist

- [x] Phase 0 audit artifacts (`v077/audit/`)
- [x] Governance agency modules (`governance/agency/`)
- [x] Explainability (`attention/explainability/`)
- [x] Observability v077 (6 metrics + composite score)
- [x] Governor `agency_boundary_observability` (advisory only)
- [x] Timeseries 6 horizons + 7 stress scenarios
- [x] Tests `tests/v077/` (10 areas)

## Score dimensions

| Dimension | Weight |
|-----------|--------|
| autonomous_agency_containment | 0.024 |
| agency_boundary | 0.022 |
| agency_lineage_integrity | 0.022 |
| cognition_decay | 0.022 |
| agency_provenance | 0.022 |
| cognition_integrity | 0.021 |

Run `evaluate_cognitive_agency_boundary()` and pytest for PASS confirmation.
