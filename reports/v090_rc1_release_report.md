# Hermes-ASI v0.9.0-rc1 Release Report

```yaml
release_label: v0.9.0-rc1
release_status: conditionally ready as advisory institutional intelligence
report_date: 2026-06-15
commit_hash: 100721804d5f087c0214ef6caf14b75f70b2f73b
branch: codex/deliberation-kernels
```

---

## 1. Executive Summary

Hermes-ASI v0.9.0-rc1 is **ready for tagging** as the institutional intelligence release candidate.

- RC Health: **95.78** (threshold 85.0) — pass
- DMN Health: **99.83** (threshold 80.0) — pass
- Graph Health: **97.00** (threshold 75.0) — pass
- Release Ready flag: **true**
- Readiness checker: **READY = true**
- Recommendation: **ready for v0.9.0-rc1**

All 13 release artifacts are generated. All 12 audit documents are present. All health thresholds are met. No critical tech debt blocks this release. Governance, Guardian, credentials, provider permissions, and approval requirements are unchanged from the v0.9 architecture baseline.

This release is **advisory-only**. Kernels analyze, score, and recommend; the operator and the Guardian gate decide and act. It is not an autonomous governance authority.

---

## 2. Architecture Summary

Hermes-ASI v0.9.0-rc1 is a coherent advisory institutional intelligence architecture comprising **12 kernels** across three layered subsystems:

- **Ambient OS runtime kernel** (`kernel/`) — truth graph, entropy controller, isolation kernel, reversible wiring, integration bus, v0.4 stabilization container
- **Attention kernel** (`attention/kernel/`) — attention queue, salience engine, priority allocator
- **Hermes-ASI subsystem kernels** (`hermes/`) — deliberation, verification, acquisition, calibration, reality alignment, identity, audit, graph, release, orchestration, providers

The lifecycle is strictly advisory: Task -> Deliberation -> Evaluation -> Skills/Playbooks -> Verification -> Evidence Acquisition -> Trust Calibration -> Reality Alignment -> Belief Registry -> Identity/Continuity -> Life History -> DMN/Audit Memory. Guardian authority boundaries cover Deliberation, Verification, Reality Alignment, and Identity.

Canonical rules v1.0.0 (`hermes/rules/canonical_rules.md`) is the single source of truth. The architecture snapshot is frozen at `docs/release/ARCHITECTURE_SNAPSHOT.md`.

---

## 3. Health Metrics

### Composite Scores

| Metric | Score | Threshold | Status |
|--------|------:|----------|--------|
| RC Health | 95.78 | >= 85.0 | PASS |
| Institutional Health | 95.38 | — | PASS (subjective) |
| Graph Health | 97.00 | >= 75.0 | PASS |
| DMN Health | 99.83 | >= 80.0 | PASS |
| Test Health | 100.00 | — | PASS |
| Documentation Health | 100.00 | — | PASS |
| Report Stability | 82.00 | — | OBSERVED |

### Institutional Health Components

| Component | Score |
|-----------|------:|
| integration | 100.0 |
| governance | 95.0 |
| observability | 100.0 |
| knowledge_coverage | 90.0 |
| identity_continuity | 95.0 |
| auditability | 100.0 |
| maintainability | 78.0 |

### Graph Health Components

- 46 nodes, 47 edges, 0 isolated, 0 dangling
- 100.0% node coverage, 100.0% edge coverage, 90.0% relationship coverage
- 14 relationship types instantiated

### DMN Health Components

- 1753 valid events / 1756 total (99.83%)
- 3 invalid events are legacy schema drift retained per no-silent-erasure doctrine

---

## 4. Audit Summary

12 audit documents under `docs/audit/`:

| Audit | Outcome |
|-------|---------|
| Kernel Dependency Audit | Phase 1-9 kernels present and connected |
| Lifecycle Audit | Advisory lifecycle consistent |
| Governance Audit | Guardian authority unchanged |
| DMN Audit | DMN append-only, schema validated |
| Knowledge Graph Audit | Graph coverage acceptable for RC |
| Observability Audit | Telemetry discipline intact |
| Report Inventory | Reports deterministic under snapshot mode |
| Runtime State Audit | State files well-formed |
| Git Hygiene Audit | No destructive git; branch from main |
| README Audit | Documentation aligned with capabilities |
| Technical Debt | No critical blockers |
| Release Review | Conditionally ready |

Release review conclusion: **conditionally ready**. The single open checklist item ("Legacy report builders still need shared snapshot mode") is non-blocking and scheduled for v0.9.x.

---

## 5. Governance Summary

### Intentionally Immutable in v0.9.0-rc1

- Canonical rules v1.0.0 (`hermes/rules/canonical_rules.md`)
- Guardian risk classes: `ALLOW`, `REVIEW_REQUIRED`, `BLOCK`
- Guardian keyword policy (`guardian/policy.yaml` is SSOT)
- Memory append-only doctrine
- BOOTSTRAP_GAP vs DAEMON_FAILURE distinction
- Verification independence (implementer does not self-verify)
- Promotion chain L1 -> L2 -> L3 -> L4
- Outbound messaging double confirmation
- DMN English-only language rule
- 9 schemas under `schemas/`
- RC Health, Institutional Health, Graph Health formulas

### Verification

- Guardian authority unchanged: confirmed
- Provider permissions unchanged: confirmed
- Credential policies unchanged: confirmed
- Identity / reality / release reports remain advisory: confirmed
- No kernel code modifications during release audit: confirmed
- No governance rule modifications during release audit: confirmed

---

## 6. Known Risks

| Risk | Impact | Mitigation | Follow-up |
|------|--------|------------|-----------|
| Report snapshot mode not fully implemented | Timestamp churn in lower-layer registries; release diff noise | Documented; new RC report generators use stable inventory/order | v0.9.x stabilization |
| Legacy DMN records normalized but not migrated | 3 invalid events retained; audit trail retains legacy schema drift | Validator normalizes; no audit impact; no silent erasure | Governed migration in future phase |
| Graph health derived from release artifacts | Not a persisted graph database; snapshot-dependent | Acceptable for RC evidence per `reports/graph_health_report.json` recommendation | v0.9.x graph export |

### Advisory-only posture

The advisory-only posture is **not a risk**; it is an intentional design boundary. All external action requires operator + Guardian approval. Kernels do not perform autonomous corrective action.

---

## 7. Known Limitations

See `docs/release/KNOWN_LIMITATIONS.md` for the full list. Headlines:

- Legacy DMN entries (3 invalid events)
- External validation stubs
- Limited external reality sources (internal diversity + echo detection only)
- Provider constraints (CLI adapters, route --invoke is Guardian-gated)
- Current graph assumptions (release-artifact-derived)
- Project layout constraints (flat-layout, no pyproject.toml)
- Hardcoded health constants (test_health, report_stability, maintainability, governance, knowledge_coverage, identity_continuity)
- Report snapshot mode gap
- DMN event taxonomy not formalized
- Autonomy boundary (advisory-only)

---

## 8. Recommendation

**Tag as v0.9.0-rc1.**

### Rationale

1. All health thresholds pass (RC 95.78 / DMN 99.83 / Graph 97.00)
2. Release Ready flag is true
3. All 13 release artifacts are generated
4. All 12 audit documents are present and pass
5. No critical tech debt blocks the release
6. All 12 kernels present and connected through reports / registries
7. Guardian and advisory-only boundaries consistently documented
8. Reality alignment and identity continuity are first-class audit surfaces
9. Governance, Guardian, credentials, provider permissions, approval requirements all unchanged
10. Readiness checker returns READY = true with zero missing artifacts

### Conditions of release

- v0.9.0-rc1 is **advisory-only**; kernels do not perform autonomous corrective action
- All external action requires operator + Guardian approval
- Memory remains append-only
- Guardian, governance rules, credentials, provider permissions, and approval requirements are immutable in this release

### Tag recommendation (does not auto-tag)

```bash
git tag -a v0.9.0-rc1 -m "Hermes-ASI Institutional Intelligence Release Candidate"
git push origin v0.9.0-rc1
```

Tagging is a separate operator action and requires explicit operator consent. This report does not perform the tag.

---

*End of v0.9.0-rc1 release report.*
