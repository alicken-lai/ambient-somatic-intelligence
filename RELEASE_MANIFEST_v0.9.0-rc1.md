# Hermes-ASI v0.9.0-rc1 Release Manifest

```yaml
release_label: v0.9.0-rc1
release_status: conditionally ready as advisory institutional intelligence
snapshot_date: 2026-06-15
canonical_rules_version: 1.0.0
kernel_version: 0.4.1-alpha
```

---

## 1. Release Label

**v0.9.0-rc1**

Codename: Institutional Intelligence Release Candidate

## 2. Release Status

Conditionally ready as advisory institutional intelligence. Kernels analyze, score, and recommend; the operator and the Guardian gate decide and act. This release is **not** an autonomous governance authority.

## 3. Source Control

| Field | Value |
|-------|-------|
| Commit Hash | `100721804d5f087c0214ef6caf14b75f70b2f73b` |
| Branch | `codex/deliberation-kernels` |
| Commit Date | `2026-06-14T23:02:09+08:00` |

## 4. Version Anchors

| Anchor | Value |
|--------|-------|
| canonical_rules_version | 1.0.0 |
| AmbientKernel version | 0.4.1-alpha |

## 5. Health Metrics

| Metric | Value | Threshold | Pass |
|--------|------:|----------|------|
| RC Health | 95.78 | >= 85.0 | Yes |
| Institutional Health | 95.38 | — | — |
| Graph Health | 97.00 | >= 75.0 | Yes |
| DMN Health | 99.83 | >= 80.0 | Yes |
| Test Health | 100.00 | — | — |
| Documentation Health | 100.00 | — | — |
| Report Stability | 82.00 | — | — |
| Release Ready | true | — | — |
| All Thresholds Met | true | — | — |

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

| Component | Value |
|-----------|------:|
| node_count | 46 |
| edge_count | 47 |
| node_coverage | 100.0 |
| edge_coverage | 100.0 |
| relationship_coverage | 90.0 |
| isolated_nodes | 0 |
| dangling_references | 0 |

### DMN Health Components

| Component | Value |
|-----------|------:|
| valid_events | 1753 |
| total_events | 1756 |
| invalid_events | 3 |
| validity_rate | 99.83% |

## 6. Kernel Inventory

12 kernels / major subsystems:

1. Deliberation — `hermes/deliberation/`
2. Evaluation and governance — `hermes/deliberation/evaluation/`
3. Adaptive routing intelligence — `hermes/deliberation/router/`
4. Self-improving deliberation knowledge — `hermes/deliberation/skills/`
5. Verification and evidence — `hermes/verification/`
6. Knowledge acquisition — `hermes/acquisition/`
7. Trust and knowledge calibration — `hermes/calibration/`
8. Reality alignment — `hermes/reality_alignment/`
9. Narrative identity and continuity — `hermes/identity/`
10. Institutional audit — `hermes/audit/`
11. Graph health — `hermes/graph/`
12. Release health — `hermes/release/`

Supporting subsystems:

- Orchestration — `hermes/orchestration/`
- Providers — `hermes/providers/`
- Ambient OS runtime kernel — `kernel/`
- Attention kernel — `attention/kernel/`

## 7. CLI Inventory

29 commands. Entry point: `python scripts/hermes.py <command>`.

### Provider Orchestration (1)

- `route`

### Deliberation Execution (1)

- `deliberate`

### Deliberation Reports (7)

- `deliberate-report`
- `routing-report`
- `roi-report`
- `strategy-report`
- `playbook-report`
- `skill-report`
- `failure-report`

### Verification Reports (4)

- `evidence-report`
- `claim-report`
- `verification-report`
- `contradiction-report`

### Acquisition Reports (3)

- `acquisition-report`
- `evidence-quality-report`
- `knowledge-index-report`

### Calibration Reports (3)

- `knowledge-health-report`
- `trust-report`
- `drift-report`

### Reality Alignment Reports (3)

- `fitness-report`
- `reality-report`
- `diversity-report`

### Identity Reports (3)

- `identity-report`
- `continuity-report`
- `life-history-report`

### Institutional Reports (3)

- `audit-report`
- `graph-health-report`
- `release-report`

## 8. Schema Inventory

9 schemas under `schemas/`:

1. `schemas/dmn_event.schema.json`
2. `schemas/memory_event.schema.json`
3. `schemas/recall_evidence.schema.json`
4. `schemas/governed_memory_wrapper.schema.json`
5. `schemas/dmn_metadata_sidecar.schema.json`
6. `schemas/dmn_sidecar_review.schema.json`
7. `schemas/dmn_sync_manifest.schema.json`
8. `schemas/dmn_conflict_register.schema.json`
9. `schemas/embedding_sidecar.schema.json`

## 9. Audit Inventory

12 audit documents under `docs/audit/`:

1. `KERNEL_DEPENDENCY_AUDIT.md`
2. `LIFECYCLE_AUDIT.md`
3. `GOVERNANCE_AUDIT.md`
4. `DMN_AUDIT.md`
5. `KNOWLEDGE_GRAPH_AUDIT.md`
6. `OBSERVABILITY_AUDIT.md`
7. `REPORT_INVENTORY.md`
8. `RUNTIME_STATE_AUDIT.md`
9. `GIT_HYGIENE_AUDIT.md`
10. `README_AUDIT.md`
11. `TECHNICAL_DEBT.md`
12. `RELEASE_REVIEW.md`

Release review conclusion: **conditionally ready**.

## 10. Report Inventory

### Release-critical reports (root)

| Report | Format |
|--------|--------|
| `RELEASE_NOTES_v0.9.0-rc1.md` | Markdown |
| `RELEASE_MANIFEST_v0.9.0-rc1.md` | Markdown |

### Release-critical reports (reports/)

| Report | Format |
|--------|--------|
| `reports/v090_rc1_baseline.json` | JSON |
| `reports/v090_rc1_release_report.md` | Markdown |
| `reports/v090_rc1_completion_report.md` | Markdown |
| `reports/v09_release_report.{md,json}` | Markdown + JSON |
| `reports/institutional_audit_report.{md,json}` | Markdown + JSON |
| `reports/graph_health_report.{md,json}` | Markdown + JSON |
| `reports/institutional_fitness_report.{md,json}` | Markdown + JSON |

### Kernel reports (alphabetical)

- `acquisition_report.{md,json}`
- `belief_registry.json`
- `claim_report.{md,json}`
- `continuity_report.{md,json}`
- `contradiction_report.{md,json}`
- `deliberation_ab_results.json`
- `deliberation_learning_report.md`
- `deliberation_quality_report.md`
- `deliberation_roi_report.{md,json}`
- `deliberation_skill_registry.json`
- `deliberation_strategy_report.{md,json}`
- `diversity_report.{md,json}`
- `dmn_event_validation_report.json`
- `drift_report.{md,json}`
- `evidence_quality_report.{md,json}`
- `evidence_report.{md,json}`
- `evidence_registry.json`
- `failure_learning_report.md`
- `identity_registry.json`
- `identity_report.md`
- `knowledge_health_report.{md,json}`
- `life_history_report.{md,json}`
- `playbook_report.{md,json}`
- `reality_alignment_report.json`
- `skill_report.json`
- `trust_registry.json`
- `trust_report.json`
- `verification_report.{md,json}`

### Cross-kernel registries

- `reports/belief_registry.json` (reality alignment)
- `reports/trust_registry.json` (calibration)
- `reports/evidence_registry.json` (verification + acquisition)
- `reports/identity_registry.json` (identity)

## 11. Release Documents (docs/release/)

| Document | Purpose |
|----------|---------|
| `ARCHITECTURE_SNAPSHOT.md` | Frozen v0.9.0-rc1 architecture baseline |
| `CAPABILITY_MATRIX.md` | 12-kernel capability inventory |
| `CLI_REFERENCE.md` | 29-command CLI reference |
| `REPORT_REFERENCE.md` | Full report inventory |
| `TEST_SUMMARY.md` | Test coverage summary |
| `GOVERNANCE_LOCK.md` | Intentionally immutable constraints |
| `KNOWN_LIMITATIONS.md` | Known limitations and future work |
| `RELEASE_DECISION.md` | Release go/no-go decision |
| `V09_RELEASE_CHECKLIST.md` | Release readiness checklist |
| `ARTIFACT_INVENTORY.md` | Artifact inventory |
| `REPORT_DETERMINISM.md` | Report determinism audit |
| `TECH_DEBT_PRIORITY.md` | Tech debt priority |

## 12. Test Summary

| Category | Count |
|----------|------:|
| Top-level focused test_*.py | 28 |
| Sub-directory test_*/ | 13 directories |
| Phase version suites v0xx | v04 - v077 directories |
| Integration suites | 4 (boot_check, backward_compat, ontology_validation, ontology_integration) |
| Total test files (approx.) | ~396 |

### Checklist Status (`docs/release/V09_RELEASE_CHECKLIST.md`)

- All critical items checked
- One non-blocking item open: "Legacy report builders still need shared snapshot mode"
- Recommendation: proceed to v0.9.0-rc1 as advisory release candidate

## 13. Known Limitations

See `docs/release/KNOWN_LIMITATIONS.md` for full detail. Headlines:

- Legacy DMN entries (3 invalid events retained per no-silent-erasure doctrine)
- External validation stubs (no live external reality sources)
- Limited external reality sources (internal diversity + echo detection only)
- Provider constraints (CLI adapters, route --invoke is Guardian-gated)
- Current graph assumptions (derived from release artifacts, not a graph database)
- Project layout constraints (flat-layout, no pyproject.toml)
- Hardcoded health constants (test_health=100.0, report_stability=82.0, maintainability=78.0)
- Report snapshot mode gap (documented, scheduled for v0.9.x)
- DMN event taxonomy not formalized
- Autonomy boundary (advisory-only; no autonomous corrective action)

## 14. Release Recommendation

**Ready for v0.9.0-rc1.**

All health thresholds pass. All release artifacts are generated. All audit documents are present. No critical tech debt blocks this release. Governance, Guardian, credentials, provider permissions, and approval requirements are unchanged from the v0.9 architecture baseline.

## 15. Sign-off Artifact Set

This manifest is one of 13 release artifacts comprising the v0.9.0-rc1 audit trail:

1. `RELEASE_NOTES_v0.9.0-rc1.md`
2. `RELEASE_MANIFEST_v0.9.0-rc1.md` (this file)
3. `reports/v090_rc1_baseline.json`
4. `reports/v090_rc1_release_report.md`
5. `reports/v090_rc1_completion_report.md`
6. `docs/release/ARCHITECTURE_SNAPSHOT.md`
7. `docs/release/CAPABILITY_MATRIX.md`
8. `docs/release/CLI_REFERENCE.md`
9. `docs/release/REPORT_REFERENCE.md`
10. `docs/release/TEST_SUMMARY.md`
11. `docs/release/GOVERNANCE_LOCK.md`
12. `docs/release/KNOWN_LIMITATIONS.md`
13. `docs/release/RELEASE_DECISION.md`

---

*End of v0.9.0-rc1 release manifest.*
