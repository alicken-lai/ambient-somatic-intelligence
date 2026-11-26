# Hermes-ASI v0.9.0-rc1 Release Decision

```yaml
decision_date: 2026-06-15
decision_kind: release_tag
release_label: v0.9.0-rc1
decision: APPROVED_FOR_TAGGING
```

---

## 1. Decision Question

Should Hermes-ASI be tagged **v0.9.0-rc1**?

## 2. Decision

**YES — Approve tagging as v0.9.0-rc1.**

This is a release decision record, not the tag itself. Tagging is a separate operator action and requires explicit operator consent per canonical_rules v1.0.0 section 8 (Git Safety: commit only when asked).

---

## 3. Decision Rationale

The release is approved for tagging because **all** of the following are true:

1. **All health thresholds pass.**
   - RC Health 95.78 >= 85.0 (PASS)
   - DMN Health 99.83 >= 80.0 (PASS)
   - Graph Health 97.00 >= 75.0 (PASS)
2. **Release Ready flag is true** (`reports/v09_release_report.json`).
3. **All 13 release artifacts are generated** (verified by `tools/check_rc1_readiness.py`).
4. **All 12 audit documents are present** under `docs/audit/`.
5. **No critical tech debt blocks rc1** (`docs/release/TECH_DEBT_PRIORITY.md`).
6. **All 12 kernels present and connected** through reports and registries.
7. **Guardian and advisory-only boundaries are consistently documented.**
8. **Reality alignment and identity continuity are first-class audit surfaces.**
9. **Readiness checker returns READY = true** with zero missing artifacts.
10. **Governance / Guardian / credentials / provider permissions / approval requirements are unchanged** from the v0.9 architecture baseline.

---

## 4. Evidence

| Evidence | Source | Value |
|----------|--------|-------|
| RC Health | `reports/v09_release_report.json` | 95.78 |
| Release Ready | `reports/v09_release_report.json` | true |
| Recommendation | `reports/v09_release_report.json` | "ready for v0.9.0-rc1" |
| Institutional Health | `reports/institutional_audit_report.json` | 95.38 |
| Graph Health | `reports/graph_health_report.json` | 97.00 |
| DMN Valid Events | `reports/dmn_event_validation_report.json` | 1753 / 1756 (99.83%) |
| Test Health | `reports/v09_release_report.json` | 100.00 |
| Documentation Health | `reports/v09_release_report.json` | 100.00 |
| Report Stability | `reports/v09_release_report.json` | 82.00 |
| Checklist Status | `docs/release/V09_RELEASE_CHECKLIST.md` | All critical items checked |
| Tech Debt | `docs/release/TECH_DEBT_PRIORITY.md` | No critical blockers |
| Architecture | `docs/architecture/HERMES_ASI_V09.md` | Release-candidate ready |
| Release Review | `docs/audit/RELEASE_REVIEW.md` | Conditionally ready |
| Readiness Checker | `tools/check_rc1_readiness.py` | READY = true |
| Manifest | `RELEASE_MANIFEST_v0.9.0-rc1.md` | All artifacts listed |

---

## 5. Health Metrics

### Composite Scores

| Metric | Score | Threshold | Status |
|--------|------:|----------|--------|
| RC Health | 95.78 | >= 85.0 | PASS |
| DMN Health | 99.83 | >= 80.0 | PASS |
| Graph Health | 97.00 | >= 75.0 | PASS |
| Release Ready | true | — | PASS |

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

---

## 6. Audit Results

| Audit Document | Outcome |
|----------------|---------|
| `KERNEL_DEPENDENCY_AUDIT.md` | Phase 1-9 kernels present and connected |
| `LIFECYCLE_AUDIT.md` | Advisory lifecycle consistent |
| `GOVERNANCE_AUDIT.md` | Guardian authority unchanged |
| `DMN_AUDIT.md` | DMN append-only, schema validated |
| `KNOWLEDGE_GRAPH_AUDIT.md` | Graph coverage acceptable for RC |
| `OBSERVABILITY_AUDIT.md` | Telemetry discipline intact |
| `REPORT_INVENTORY.md` | Reports deterministic under snapshot mode |
| `RUNTIME_STATE_AUDIT.md` | State files well-formed |
| `GIT_HYGIENE_AUDIT.md` | No destructive git; branch from main |
| `README_AUDIT.md` | Documentation aligned with capabilities |
| `TECHNICAL_DEBT.md` | No critical blockers |
| `RELEASE_REVIEW.md` | Conditionally ready |

---

## 7. Known Risks

| Risk | Severity | Mitigation | Acceptable for rc1 |
|------|----------|------------|--------------------|
| Report snapshot mode not fully implemented | Medium | Documented; new RC report generators use stable inventory/order | Yes — non-blocking |
| Legacy DMN records normalized but not migrated | Low | Validator normalizes; no audit impact; no silent erasure | Yes — retained per doctrine |
| Graph health derived from release artifacts | Low | Acceptable for RC evidence per graph_health_report recommendation | Yes — scheduled for v0.9.x |
| Advisory-only posture | Not a risk | Intentional design boundary | Yes — design |

---

## 8. Conditions of Release

The v0.9.0-rc1 tag carries these non-negotiable conditions:

1. **Advisory-only**: kernels do not perform autonomous corrective action.
2. **Operator + Guardian**: all external action requires operator consent and Guardian approval.
3. **Memory append-only**: no silent erasure; legacy schema drift retained in audit trail.
4. **Immutable governance**: Guardian, governance rules, credentials, provider permissions, and approval requirements are unchanged from the v0.9 architecture baseline.
5. **Schema-stable**: the 9 schemas under `schemas/` are frozen for rc1.
6. **Formula-stable**: RC Health, Institutional Health, and Graph Health formulas are frozen for rc1.
7. **Branch hygiene**: tag must be applied to commit `100721804d5f087c0214ef6caf14b75f70b2f73b` on branch `codex/deliberation-kernels` (or its merged descendant on main, per operator decision).

---

## 9. Approval Boundary

This decision document is **advisory**. It does not perform the tag. The actual `git tag -a v0.9.0-rc1` command requires explicit operator instruction per canonical_rules v1.0.0 section 8 (Git Safety: commit only when asked).

If the operator approves tagging, the recommended commands are:

```bash
git tag -a v0.9.0-rc1 -m "Hermes-ASI Institutional Intelligence Release Candidate"
git push origin v0.9.0-rc1
```

Per the user_rules Git Safety Guide, the operator should first verify:

1. Current branch (`git branch --show-current`)
2. Branch base (`git merge-base main HEAD`)
3. Untracked files (`git status`)
4. No accidental node_modules / build file inclusion (`git diff --stat`)

---

## 10. Sign-off Artifact Set

This decision is one of 13 release artifacts comprising the v0.9.0-rc1 audit trail:

1. `RELEASE_NOTES_v0.9.0-rc1.md`
2. `RELEASE_MANIFEST_v0.9.0-rc1.md`
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
13. `docs/release/RELEASE_DECISION.md` (this file)

---

## 11. Final Recommendation

**Hermes-ASI is formally ready for v0.9.0-rc1.**

All acceptance criteria are met:

- ARCHITECTURE_SNAPSHOT exists: YES
- RELEASE_MANIFEST exists: YES
- Baseline snapshot exists: YES
- Release report exists: YES
- Release decision exists: YES
- Readiness checker passes: YES (READY = true)
- Completion report exists: YES
- READY = true: YES
- No governance changes: CONFIRMED
- No kernel changes: CONFIRMED
- No new capabilities: CONFIRMED

Proceed to operator-approved tagging.

---

*End of v0.9.0-rc1 release decision.*
