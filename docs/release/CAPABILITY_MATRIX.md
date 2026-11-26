# v0.9.0-rc1 Capability Matrix

- **Date:** 2026-06-15
- **Release:** Hermes-ASI v0.9.0-rc1 (Institutional Intelligence Release Candidate)
- **SSOT:** [`VERSION_MANIFEST.md`](../../VERSION_MANIFEST.md)

> All kernels are **Production-ready (advisory)** at this baseline.
> Side-effecting actions are operator-mediated and routed through the Hermes / Guardian gate.

---

## Capability Inventory

| Kernel | Purpose | Status | CLI Commands | Reports | Tests | Dependencies | Coverage Notes |
|--------|---------|--------|--------------|---------|-------|--------------|----------------|
| Deliberation | Operator intent → candidate strategies with strength-of-evidence scoring. | Production-ready (advisory) | `deliberate`, `deliberate-report`, `routing-report`, `roi-report`, `strategy-report`, `playbook-report`, `skill-report`, `failure-report` | `deliberation_quality_report.md`, `deliberation_strategy_report.{md,json}`, `deliberation_roi_report.{md,json}`, `deliberation_learning_report.md`, `playbook_report.{md,json}`, `skill_report.json`, `failure_learning_report.md`, `deliberation_ab_results.json`, `deliberation_skill_registry.json` | `tests/test_asi_deliberation_layer.py`, `tests/test_deliberation_regression.py`, `tests/test_deliberation_evaluation.py`, `tests/test_deliberation_knowledge_kernel.py`, `tests/v050/` | Upstream: Routing, Operator. Downstream: Evaluation, Verification, Knowledge, Identity. | Strengths: kernel present and connected through reports/registries. |
| Evaluation and Governance | Strategy evaluation and governance classification (ALLOW / REVIEW_REQUIRED / BLOCK). | Production-ready (advisory) | (exposed via `deliberate` family and Guardian gate) | `deliberation_strategy_report.{md,json}`, governance classifications surfaced via Guardian | Governance classification covered by deliberation / Guardian tests. | Upstream: Deliberation. Downstream: Knowledge, Guardian gate. | Governance boundary immutable via `canonical_rules.md` v1.0.0 and `policy.yaml`. |
| Adaptive Routing Intelligence | Provider / subagent routing with attention weighting. | Production-ready (advisory) | `route` | Routing decisions surfaced via `routing-report`. | Covered by routing test suite under `tests/`. | Upstream: Operator, Attention Kernel. Downstream: Deliberation. | Strengths: single `route` command provides the dispatch surface. |
| Self-improving Deliberation Knowledge | A/B learning, skill registry, failure learning loop. | Production-ready (advisory) | `skill-report`, `failure-report` (via Deliberation family) | `skill_report.json`, `failure_learning_report.md`, `deliberation_ab_results.json`, `deliberation_skill_registry.json` | `tests/test_deliberation_knowledge_kernel.py` | Upstream: Deliberation (A/B outcomes). Downstream: Deliberation (feedback loop). | Strengths: closed feedback loop between deliberation outcomes and skill registry. |
| Verification and Evidence | Claim → evidence → contradiction verification pipeline. | Production-ready (advisory) | `evidence-report`, `claim-report`, `verification-report`, `contradiction-report` | `evidence_report.{md,json}`, `claim_report.{md,json}`, `verification_report.{md,json}`, `contradiction_report.{md,json}` | `tests/` verification suite. | Upstream: Deliberation (claims). Downstream: Acquisition, Identity. | Strengths: full claim/evidence/contradiction triple reportable. |
| Knowledge Acquisition | Evidence-quality scoring, knowledge indexing, acquisition gating. | Production-ready (advisory) | `acquisition-report`, `evidence-quality-report`, `knowledge-index-report` | `acquisition_report.{md,json}`, `evidence_quality_report.{md,json}`, `knowledge_index_report.md` | `tests/` acquisition suite. | Upstream: Verification. Downstream: Calibration. | Strengths: quality-scored acquisition gating wired to verification outputs. |
| Trust and Knowledge Calibration | Trust registry, drift detection, calibration feedback. | Production-ready (advisory) | `knowledge-health-report`, `trust-report`, `drift-report` | `knowledge_health_report.{md,json}`, `trust_report.json`, `drift_report.{md,json}` | `tests/` calibration suite. | Upstream: Acquisition. Downstream: Reality Alignment. | Strengths: trust and drift reports feed Reality Alignment and Identity. |
| Reality Alignment | Reality / fitness / diversity scores and echo-risk challenges to high-trust beliefs. | Production-ready (advisory) | `fitness-report`, `reality-report`, `diversity-report` | `reality_alignment_report.json`, `diversity_report.{md,json}`, `institutional_fitness_report.{md,json}` | `tests/` reality suite. | Upstream: Calibration, `belief_registry.json`. Downstream: Identity. | Guardian authority boundary covers this kernel (advisory). |
| Narrative Identity and Continuity | Identity registry, life history, continuity links. | Production-ready (advisory) | `identity-report`, `continuity-report`, `life-history-report` | `identity_report.md`, `identity_registry.json`, `continuity_report.{md,json}`, `life_history_report.{md,json}` | `tests/` identity suite. | Upstream: Deliberation, Verification, Reality. Downstream: Audit, DMN. | Guardian authority boundary covers this kernel (advisory). |
| Institutional Audit | Auditability, maintainability, observability, integration health scoring. | Production-ready (advisory) | `audit-report` | `institutional_audit_report.{md,json}`, `institutional_fitness_report.{md,json}` | `tests/` audit suite. | Upstream: Identity (and all kernels, read-only). Downstream: Graph Health, Release Health. | Institutional score 95.38; maintainability 78 is the long-tail follow-up. |
| Graph Health | Node/edge coverage, relationship diversity, isolated-node / dangling-reference detection. | Production-ready (advisory) | `graph-health-report` | `graph_health_report.{md,json}` | `tests/` graph suite. | Upstream: Audit artifacts, registries. Downstream: Release Health. | 46 nodes / 47 edges / 14 relationship types / zero isolated / zero dangling. |
| Release Health | RC Health aggregation, release-ready gating, release-report generation. | Production-ready (advisory) | `release-report` | `v09_release_report.{md,json}` | `tests/` release suite (`hermes/release/rc_health.py`). | Upstream: Audit, Graph, DMN, Tests, Docs. Downstream: Operator (advisory). | RC Health 95.78, release_ready = true. |

---

## Registries (cross-kernel)

| Registry | Path | Consumers |
|----------|------|-----------|
| Belief Registry | `reports/belief_registry.json` | Reality Alignment, Identity |
| Trust Registry | `reports/trust_registry.json` | Calibration, Identity |
| Evidence Registry | `reports/evidence_registry.json` | Verification, Acquisition |

---

## CLI Command Surface (29 commands)

`route`, `deliberate`, `deliberate-report`, `routing-report`, `roi-report`, `strategy-report`, `playbook-report`, `skill-report`, `failure-report`, `evidence-report`, `claim-report`, `verification-report`, `contradiction-report`, `acquisition-report`, `evidence-quality-report`, `knowledge-index-report`, `knowledge-health-report`, `trust-report`, `drift-report`, `fitness-report`, `reality-report`, `diversity-report`, `identity-report`, `continuity-report`, `life-history-report`, `audit-report`, `graph-health-report`, `release-report`.

---

## Notes

- All status entries are **Production-ready (advisory)**; none of the kernels exercise autonomous governance authority at this baseline.
- Test paths follow the `tests/` convention; kernel-specific regression suites live alongside cross-kernel integration tests.
- Report file extensions shown as `.{md,json}` indicate both Markdown and JSON variants are generated.
