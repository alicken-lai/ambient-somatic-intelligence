# Hermes-ASI v0.9.0-rc1 Release Notes

- **Codename:** Institutional Intelligence Release Candidate
- **Release Date:** 2026-06-15
- **Release Status:** Conditionally ready as advisory institutional intelligence (release-candidate)
- **SSOT:** [`VERSION_MANIFEST.md`](VERSION_MANIFEST.md) · [`docs/architecture/HERMES_ASI_V09.md`](docs/architecture/HERMES_ASI_V09.md)

---

## 0. Executive Foreword

> **From the super manager (2026-06-15):**
>
> Hermes-ASI v0.9.0-rc1 marks the transition from an experimental multi-agent architecture into an Institutional Intelligence platform.
>
> The system now includes governed deliberation, evidence-based verification, trust calibration, reality alignment, narrative identity, continuity tracking, and institutional auditability.
>
> Rather than optimizing for raw model capability, Hermes-ASI focuses on long-term knowledge governance, evidence stewardship, and continuity across time.
>
> This release establishes the first stable baseline for future evolution toward Ambient Somatic Intelligence.

This foreword captures the strategic intent of the v0.9.0-rc1 cut. The technical evidence supporting each claim above is traceable through the architecture snapshot, capability matrix, and audit documents referenced in this file.

---

## 1. Project Overview

Hermes-ASI (Ambient Somatic Intelligence) is an **advisory institutional intelligence architecture** that provides deliberation, verification, trust calibration, reality alignment, identity continuity, and audit memory for operator-mediated workflows. It is not an autonomous governance authority; all side-effecting actions route through the operator and the Hermes / Guardian gate.

Current phase posture:

- Phase 1 through Phase 9: complete
- Integration Audit: complete
- RC Stabilization: complete

The codename "Institutional Intelligence Release Candidate" reflects that this release stabilizes the institutional audit surfaces (auditability, identity continuity, knowledge coverage, graph health, DMN validation) into a frozen baseline suitable for release-candidate promotion.

Naming:

- **Hermes-ASI** — the ambient (always-on, sidecar-style) somatic (body-of-evidence-driven) intelligence subsystem.
- **v0.9.0-rc1** — first release-candidate cut of the institutional intelligence baseline.

---

## 2. Phase Summary

| Phase | Theme | Outcome |
|-------|-------|---------|
| v0.4 stabilization | Truth / Entropy / Isolation | Foundational kernel isolation and entropy discipline established. |
| v0.5 attention kernel | Attention Kernel | Attention-driven routing primitives introduced. |
| v0.6 cognitive governance | Cognitive Governance | Guardian policy + canonical rules v1.0.0 established; advisory posture formalized. |
| v0.7 cognitive continuity | Cognitive Continuity Series (→ v0.7.7) | Identity continuity, life-history, and cognitive agency boundary (v0.7.7) landed. |
| v0.8 integration | Integration | Cross-kernel wiring, registry hydration, and end-to-end lifecycle exercised. |
| v0.9 release candidate | Institutional Intelligence RC | Frozen architecture baseline, capability matrix, release-audit surface, and candidate release notes. |

Earlier release notes: v0.1.0-alpha, v0.3.0-alpha, v0.3.1-alpha (Somatic Metacognition Update, 2026-05-14).

---

## 3. Major Capabilities

The v0.9.0-rc1 baseline ships 12 production-ready (advisory) kernels:

- **Deliberation** — operator intent → candidate strategies with strength-of-evidence scoring.
- **Evaluation and Governance** — strategy evaluation, governance classification (ALLOW / REVIEW_REQUIRED / BLOCK).
- **Adaptive Routing Intelligence** — provider/subagent routing, attention-weighted dispatch.
- **Self-improving Deliberation Knowledge** — A/B learning, skill registry, failure learning loop.
- **Verification and Evidence** — claim → evidence → contradiction verification pipeline.
- **Knowledge Acquisition** — evidence-quality scoring, knowledge indexing, acquisition gating.
- **Trust and Knowledge Calibration** — trust registry, drift detection, calibration feedback.
- **Reality Alignment** — reality / fitness / diversity scores, echo-risk challenges to high-trust beliefs.
- **Narrative Identity and Continuity** — identity registry, life history, continuity links.
- **Institutional Audit** — auditability, maintainability, observability, integration health scoring.
- **Graph Health** — node/edge coverage, relationship diversity, isolated-node / dangling-reference detection.
- **Release Health** — RC Health aggregation, release-ready gating, release-report generation.

Guardian authority boundary coverage (advisory only): Deliberation, Verification, Reality Alignment, Identity.

---

## 4. Audit Results

- **Institutional Audit** — 95.38 / 100. Integration, observability, and auditability all at 100; governance at 95; identity continuity at 95; knowledge coverage at 90; maintainability at 78. *Read-out:* institutional surfaces are audit-ready; maintainability is the long-tail follow-up.
- **Graph Health** — 97.0 / 100, with 46 nodes and 47 edges, 100% node/edge coverage, zero isolated nodes, zero dangling references, and 14 distinct relationship types. *Read-out:* the knowledge graph is internally consistent at release time.
- **DMN Validation** — 99.83 / 100 (1753 / 1756 events valid). *Read-out:* DMN memory is append-only and validator-normalized; three legacy records remain non-conforming but are contained.

---

## 5. Health Scores

Aggregated release posture: **RC Health 95.78**, **Release Ready: true**, recommendation: *"ready for v0.9.0-rc1"*.

### RC Health weighted formula

```
score = test_health*0.18
      + documentation*0.16
      + institutional*0.18
      + graph*0.16
      + dmn*0.16
      + report_stability*0.16

release_ready = (score >= 85) AND (dmn >= 80) AND (graph >= 75)
```

### Score table

| Dimension | Weight | Score | Notes |
|-----------|-------:|------:|-------|
| Test Health | 0.18 | 100.0 | Full test pass. |
| Documentation Health | 0.16 | 100.0 | Docs coverage complete for this baseline. |
| Institutional Audit Health | 0.18 | 95.38 | See institutional sub-scores below. |
| Graph Health | 0.16 | 97.0 | 46 nodes / 47 edges / 14 relationship types. |
| DMN Health | 0.16 | 99.83 | 1753 / 1756 events valid. |
| Report Stability | 0.16 | 82.0 | Shared snapshot mode is the main follow-up. |
| **RC Health (weighted)** | — | **95.78** | release_ready = true |

### Institutional sub-scores

| Sub-score | Value |
|-----------|------:|
| Integration | 100.0 |
| Governance | 95.0 |
| Observability | 100.0 |
| Knowledge Coverage | 90.0 |
| Identity Continuity | 95.0 |
| Auditability | 100.0 |
| Maintainability | 78.0 |

### Graph relationship diversity

`contains` (29), `stored_in` (4), `feeds` (2), `has_report` (2), `continuity_link` (1), `has_challenge_event` (1), `has_core_value` (1), `has_diversity_metric` (1), `has_fitness_score` (1), `has_objective` (1), `has_principle` (1), `has_reality_score` (1), `has_trust` (1), `uses_skill` (1).

---

## 6. Known Limitations

- **Advisory-only posture.** Hermes-ASI v0.9.0-rc1 is an advisory institutional intelligence layer; it does not exercise autonomous governance authority. All side-effecting actions pass through the operator and the Hermes / Guardian gate.
- **Flat-layout project.** The repository is a flat-layout Python project with no `pyproject.toml` or `requirements.txt` at this baseline. Execution is via the CLI entry point `python scripts/hermes.py <command>`; there is no `pip install` distribution path.
- **Runtime snapshot hygiene.** Three release-known risks (see Section 7) remain, all related to runtime report-snapshot generation and persistence rather than to kernel correctness.

---

## 7. Known Risks

### 7.1 Report snapshot mode is documented but not fully implemented across all generators

- **Risk:** Report freshness and reproducibility depend on a shared snapshot mode that is documented in the release checklist but not yet wired into every report generator.
- **Impact:** Report stability score (82.0) reflects this gap. Some reports may regenerate without snapshot metadata.
- **Mitigation:** Documented in `docs/release/TECH_DEBT_PRIORITY.md` (High priority). Operators should treat report timestamps as advisory until the shared snapshot writer lands.
- **Follow-up:** v0.9.x stabilization track — shared stable report writer + report freshness metadata.

### 7.2 Legacy DMN records are normalized by the validator but not migrated

- **Risk:** Three legacy DMN records (1753 / 1756 valid) are normalized by the validator on read but are not rewritten in place.
- **Impact:** DMN health is 99.83; the gap is contained and does not block release.
- **Mitigation:** Validator enforces the canonical event taxonomy on every read; no operator action required. Append path remains canonical.
- **Follow-up:** v0.9.x — adopt DMN event taxonomy across legacy writers (no in-place migration of historical records).

### 7.3 Graph health is derived from release artifacts rather than a persisted graph database

- **Risk:** The 97.0 graph-health score is computed from release-time artifacts (registries + reports), not from a persistent graph store.
- **Impact:** Graph health is accurate at the snapshot boundary but cannot be queried live between releases.
- **Mitigation:** Snapshot is captured in `reports/graph_health_report.json` and referenced from `docs/release/ARCHITECTURE_SNAPSHOT.md`.
- **Follow-up:** v0.9.x — graph health export to a queryable representation for cross-release trending.

---

## 8. Future Roadmap

### v0.9.x stabilization

- Shared report snapshot mode across all generators (closes Section 7.1).
- DMN event taxonomy adoption for new writes (contains Section 7.2).
- Graph health export (addresses Section 7.3).
- Shared stable report writer and report freshness metadata.
- README lifecycle diagram pointer (Medium tech debt).

### Forward phases

- Deeper maintainability work to lift the institutional audit sub-score beyond 78.
- Cross-release trending on graph health and report stability once persisted exports exist.
- Continued advisory posture; no move toward autonomous governance authority in the v0.9.x line.

---

## 9. Upgrade / Installation Notes

Hermes-ASI is a flat-layout repository; there is no `pip install` distribution path.

```bash
git clone <repository-url>
cd ambient-somatic-intelligence
python scripts/hermes.py <command>
```

Run the release self-check:

```bash
python scripts/hermes.py release-report
```

Run individual reports, e.g.:

```bash
python scripts/hermes.py audit-report
python scripts/hermes.py graph-health-report
python scripts/hermes.py identity-report
```

---

## 10. Compatibility

- Python 3.x standard library runtime.
- External dependencies used: `pyyaml`, `jsonschema`.
- No native extensions. No network calls required for offline kernel/report execution.

---

## 11. Acknowledgments / References

- [`VERSION_MANIFEST.md`](VERSION_MANIFEST.md) — canonical manifest of 12 kernels and 29 CLI commands.
- [`docs/architecture/HERMES_ASI_V09.md`](docs/architecture/HERMES_ASI_V09.md) — v0.9 architecture and lifecycle reference.
- [`docs/audit/`](docs/audit/) — institutional audit evidence.
- [`docs/release/`](docs/release/) — release baseline documents (this notes file, `ARCHITECTURE_SNAPSHOT.md`, `CAPABILITY_MATRIX.md`, `TECH_DEBT_PRIORITY.md`, `V09_RELEASE_CHECKLIST.md`).
- [`hermes/rules/canonical_rules.md`](hermes/rules/canonical_rules.md) — `canonical_version: 1.0.0`.
- Prior releases: v0.1.0-alpha, v0.3.0-alpha, v0.3.1-alpha (Somatic Metacognition Update, 2026-05-14).
