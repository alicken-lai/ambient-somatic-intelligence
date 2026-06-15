# Hermes-ASI v0.9.0-rc1 Test Coverage Summary

> Scope: summary of the test surface validated for the v0.9.0-rc1 release.
> Source of truth for release readiness: `V09_RELEASE_CHECKLIST.md`.
> Release documentation only. This file does not modify kernel code, governance rules, Guardian settings, or permissions.

## 1. Overview

The test suite lives under `tests/` and contains roughly 396 test files at the time of the v0.9.0-rc1 cut. The directory is organized into three tiers:

1. **Top-level integration tests** — `tests/test_*.py` files that exercise end-to-end kernel behavior and CLI-level flows.
2. **Sub-directory tests** — `tests/test_*/` packages that group focused suites per kernel or per cross-cutting concern.
3. **Phase version suites** — `tests/v0xx/` directories preserving regression suites tied to historical phase releases (v04 through v077).

There is no `pyproject.toml` or `requirements.txt` and no formal CI workflow file in the repository. Tests are executed manually via `pytest` from the project root. The `V09_RELEASE_CHECKLIST.md` confirms that all test categories pass for the rc1 cut.

## 2. Focused Test Suites (tests/test_*.py)

Each top-level test file maps to a kernel or cross-kernel concern. The table records the primary coverage target for each suite.

| Test file | Kernel / target | Coverage scope |
|---|---|---|
| `tests/test_institutional_audit.py` | `hermes/audit` | Institutional audit pipeline, registry aggregation, audit report determinism |
| `tests/test_graph_health.py` | `hermes/graph` | Knowledge graph integrity, connectivity, health scoring |
| `tests/test_release_health.py` | `hermes/release` | Release artifact inventory, release report stability |
| `tests/test_report_determinism.py` | Report stability | Deterministic report generation across runs |
| `tests/test_dmn_taxonomy.py` | DMN governance | DMN taxonomy contracts |
| `tests/test_dmn_governance_contract_schemas.py` | DMN governance | DMN contract schema validation |
| `tests/test_dmn_metadata_sidecar_proposals.py` | DMN governance | DMN metadata sidecar proposal flow |
| `tests/test_dmn_sidecar_review_workflow.py` | DMN governance | DMN sidecar review workflow |
| `tests/test_historical_dmn_governance_audit.py` | DMN governance | Historical DMN governance audit |
| `tests/test_historical_dmn_wrappers.py` | DMN governance | Historical DMN wrapper compatibility |
| `tests/test_asi_deliberation_layer.py` | `hermes/deliberation` | ASI deliberation layer end-to-end |
| `tests/test_deliberation_regression.py` | `hermes/deliberation` | Deliberation regression safeguards |
| `tests/test_deliberation_evaluation.py` | `hermes/deliberation` | Deliberation evaluation metrics |
| `tests/test_deliberation_knowledge_kernel.py` | `hermes/deliberation` | Deliberation knowledge kernel integration |
| `tests/test_verification_evidence_kernel.py` | `hermes/verification` | Verification evidence kernel |
| `tests/test_acquisition_evidence_kernel.py` | `hermes/acquisition` | Acquisition evidence kernel |
| `tests/test_calibration_trust_kernel.py` | `hermes/calibration` | Calibration trust kernel |
| `tests/test_reality_alignment_kernel.py` | `hermes/reality_alignment` | Reality alignment kernel |
| `tests/test_identity_continuity_kernel.py` | `hermes/identity` | Identity continuity kernel |
| `tests/test_routing_intelligence.py` | `hermes/orchestration` | Provider routing intelligence |
| `tests/test_hermes_provider_orchestration.py` | `hermes/providers` | Provider orchestration adapters |
| `tests/test_hermes_rules.py` | `hermes/rules` | Canonical rules export and consistency |
| `tests/test_guardian_gate.py` | Guardian | Guardian gate policy enforcement |
| `tests/test_provider_safety_hardening.py` | Provider safety | Provider capability and safety hardening |
| `tests/test_trace_integrity.py` | Observability / tracing | Trace integrity and observability |
| `tests/test_in_memory_recall_backend.py` | Recall backend | In-memory recall backend behavior |
| `tests/test_recall_backend_contract.py` | Recall backend | Recall backend contract conformance |

## 3. Sub-directory Tests (tests/test_*/)

The following sub-packages hold focused suites that group tests by kernel or cross-cutting concern. Each directory is a discrete pytest package.

| Sub-directory | Scope |
|---|---|
| `tests/test_kernel/` | Core kernel behavior |
| `tests/test_attention/` | Attention mechanism unit tests |
| `tests/test_somatic_memory/` | Somatic memory subsystem |
| `tests/test_ontology/` | Ontology definition and promotion |
| `tests/test_ontology_health/` | Ontology health checks |
| `tests/test_skills/` | Skill registry and dispatch |
| `tests/test_skillify/` | Skillification pipeline |
| `tests/test_governance_doctrine/` | Governance doctrine enforcement |
| `tests/test_integration/` | Cross-kernel integration suites (see section 6) |
| `tests/attention_forecasting/` | Attention forecasting experiments |
| `tests/attention_runtime/` | Attention runtime behavior |
| `tests/attention_consolidation/` | Attention consolidation pipeline |
| `tests/agent_memory/` | Agent memory subsystem |

## 4. Phase Version Suites (tests/v0xx/)

The `tests/v0xx/` directory preserves regression suites tied to historical phase releases. As of v0.9.0-rc1 the following phase directories are present:

```
tests/v04/
tests/v05/
tests/v06/
tests/v07/
tests/v071/
tests/v072/
tests/v073/
tests/v074/
tests/v075/
tests/v076/
tests/v077/
```

These suites are kept to guard against regressions in behavior introduced at each phase. They are run as part of the rc1 validation pass.

## 5. Integration Suites

The `tests/test_integration/` package groups end-to-end integration suites that exercise multiple kernels together:

| Suite | Scope |
|---|---|
| `tests/test_integration/boot_check.py` | Boot-time sanity check across kernels |
| `tests/test_integration/backward_compat.py` | Backward compatibility with prior phase artifacts |
| `tests/test_integration/ontology_validation.py` | Ontology validation pipeline |
| `tests/test_integration/ontology_integration.py` | Ontology integration across kernels |

## 6. Release Validation

`V09_RELEASE_CHECKLIST.md` tracks the rc1 release readiness. The following categories are marked as passing for the rc1 cut:

- Tests (top-level, sub-directory, and phase suites)
- Audit status
- Documentation
- Governance
- DMN validation
- Graph health
- Report stability
- Release artifacts

The single unchecked item on the checklist is the migration of legacy report builders to a shared snapshot mode. This gap is tracked under Known Gaps (section 8) and does not block the rc1 cut.

## 7. Audit Validation

The `docs/audit/` directory holds 12 audit documents that accompany the rc1 release. These audits underpin the release review and are referenced by the institutional audit report.

| Audit document | Scope |
|---|---|
| `KERNEL_DEPENDENCY_AUDIT.md` | Kernel dependency graph and ownership boundaries |
| `LIFECYCLE_AUDIT.md` | Lifecycle state transitions across kernels |
| `GOVERNANCE_AUDIT.md` | Governance doctrine and Guardian policy enforcement |
| `DMN_AUDIT.md` | DMN event schema and sidecar governance |
| `KNOWLEDGE_GRAPH_AUDIT.md` | Knowledge graph integrity and health |
| `OBSERVABILITY_AUDIT.md` | Tracing, telemetry, and observability coverage |
| `REPORT_INVENTORY.md` | Report artifact inventory and ownership |
| `RUNTIME_STATE_AUDIT.md` | Runtime state files and persistence |
| `GIT_HYGIENE_AUDIT.md` | Git workflow and branch hygiene |
| `README_AUDIT.md` | Top-level README and onboarding accuracy |
| `TECHNICAL_DEBT.md` | Known technical debt register |
| `RELEASE_REVIEW.md` | Pre-release review notes |

## 8. Known Gaps

The following gaps are acknowledged for the rc1 cut. They are documented here for transparency and tracked in `KNOWN_LIMITATIONS.md` and `TECHNICAL_DEBT.md`.

- **Legacy report builders still require a shared snapshot mode.** This is the only unchecked item on `V09_RELEASE_CHECKLIST.md` and the primary follow-up for the rc2 cut.
- **`report_stability` is a hardcoded constant (`82.0`)** rather than a dynamically measured value.
- **`test_health` is a hardcoded constant (`100.0`)** rather than an aggregation of live test results.
- **`maintainability` is a hardcoded constant (`78.0`)** rather than a computed metric.
- **No `pyproject.toml` / `requirements.txt`.** Dependencies are implicit and tests must be executed manually via `pytest`.
- **No formal CI workflow file.** There is no checked-in CI pipeline configuration; release validation is operator-driven.
- **`golden_traces/benchmarks.json` is a static fixture**, not a dynamically sampled benchmark set.
