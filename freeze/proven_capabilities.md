# Proven Capabilities — P1 Closeout Evidence Register

**Frozen:** 2026-05-18  
Each item ties to a file path or frozen score. Capabilities are **proven in scope stated** — not extrapolated to production scale.

---

## 1. Synthetic Ontology & Promotion Chain

| Capability | Evidence | Scope |
|------------|----------|-------|
| 4-layer memory ontology (L1–L4) | `memory/ontology/layer_definition.py`, `docs/releases/v0.3.1_ontology_snapshot.md` | Schema + rules |
| L1→L2→L3→L4 promotion eligibility | `memory/ontology/promotion_rules.py`, `tests/ontology/test_l1_to_l2_promotion.py` | Synthetic tests |
| Cross-domain promotion guards | `tests/ontology/test_cross_domain_promotion.py` | Synthetic tests |
| Ontology health score **0.9592** | `docs/releases/v0.3.1_release_gate.md` | Stress validation |
| **382/382 tests pass** | `docs/releases/v0.3.1_release_gate.md` (pytest collect: 382) | CI-equivalent local run |

---

## 2. False Strategy Resistance & Verifier

| Capability | Evidence | Scope |
|------------|----------|-------|
| Illegal promotion path audit (7 paths) | `repair/audit/illegal_promotion_paths.md`, `repair/audit/promotion_path_audit.json` | Historical replay |
| Promotion chain validator | `memory/ontology/promotion_chain_validator.py` | Module exists + revalidation |
| Strategic write gate | `memory/ontology/strategic_write_gate.py` | Blocks direct L4 injection |
| Verifier enforcement | `governance/doctrine/verifier_enforcement.py` | Self-cert blocked |
| False strategy resistance **1.00** post-P1.5 | `repair/reports/repaired_reality_score.json` | Replay revalidation |
| Verifier consistency **1.00** post-P1.5 | `repair/reports/repaired_reality_score.json` | Replay revalidation |
| 7/7 problematic entries blocked | `repair/reports/replay_repair_report.json` | Phase 6 revalidation |
| Verifier blocking tests | `tests/ontology/test_verifier_blocking.py` | Synthetic |

---

## 3. Reality Replay Sandbox

| Capability | Evidence | Scope |
|------------|----------|-------|
| Full phase replay (1C–1J) without production mutation | `docs/releases/p1_reality_gate.md` (criteria 1–2 PASS) | Sandbox |
| Instinct emergence analysis | `replay/reports/instinct_emergence_report.json` (8 clusters) | Historical |
| Missed instinct detection | `replay/reports/missed_instinct_report.json` (8 candidates) | Historical |
| False strategy detection | `replay/reports/false_strategy_report.json` | Historical |
| Precursor / circadian / salience reports | `replay/reports/precursor_analysis_report.json`, `circadian_attention_report.json`, `salience_competition_report.json` | Historical |
| Replay runner + verifier | `replay/sandbox/replay_runner.py`, `replay/sandbox/replay_verifier.py` | Infrastructure |

---

## 4. Telemetry Infrastructure

| Capability | Evidence | Scope |
|------------|----------|-------|
| Telemetry schema & normalizer | `telemetry/core/telemetry_schema.py`, `telemetry/core/telemetry_normalizer.py` | Built P1.6 |
| Gap detection | `telemetry/core/gap_detector.py` | Built P1.6 |
| 5-minute sampling policy (300s max cadence) | `telemetry/sampling/sampling_policy.py`, `docs/releases/p16_reality_gate.md` | Configured |
| launchd runtime integration | `telemetry/runtime/launchd_sampling.py` | Ready |
| 7-day REAL maturation (day_01–07) | `telemetry/maturation/p17c_materialization_report.json` (7/7) | May 11–17 |
| Zero INTERPOLATED in day-file scoring | `telemetry/maturation/p17c_materialization_report.json` (121 excluded) | P1.7C+ |

---

## 5. Operational Sensing (Daemon-Stable)

| Capability | Evidence | Scope |
|------------|----------|-------|
| Daemon-stable continuity **1.0000** | `freeze/daemon_stable_window.json`, `telemetry/maturation/p17d_continuity_exception_report.json` | ~105h window |
| **0 DAEMON_FAILURE** gaps >10 min in stable window | `telemetry/maturation/p17d_continuity_exception_report.json` | P1.7D gate |
| Operational Reality Score **0.812** | `docs/releases/p17d_operational_unlock_gate.md` | P1.7D |
| Operational gate **PASS 5/5** | `docs/releases/p17d_operational_unlock_gate.md` | v0.4 UNLOCKED |
| Operational precursor **0.61** (covered incidents) | `telemetry/maturation/p17d_continuity_exception_report.json` | 1 covered incident methodology |
| Operational circadian **0.71** | Same | With INSUFFICIENT_DURATION waiver |

---

## 6. Real-Only Discipline

| Capability | Evidence | Scope |
|------------|----------|-------|
| P1.7+ REAL-only scoring policy | `telemetry/maturation/matured_reality_score.json` (`data_policy`) | Enforced |
| P1.6 interpolation audit (121 excluded) | `telemetry/maturation/p17c_materialization_report.json` | Documented |
| Honest score correction P1.6→P1.7 | `freeze/reality_score_evolution.md` | −0.0175 documented |

---

## 7. Historical Union Accountability

| Capability | Evidence | Scope |
|------------|----------|-------|
| Historical Reality Score **0.8015** (≥0.80) | `telemetry/maturation/matured_reality_score.json` | P1.7C |
| Union continuity **0.7712** | `telemetry/maturation/p17c_materialization_report.json` | Honest FAIL vs 0.95 |
| BOOTSTRAP_GAP classification (64) | `telemetry/maturation/p17d_continuity_exception_report.json` | Doctrine frozen |

---

## 8. Attention & Salience (Partial)

| Capability | Evidence | Scope |
|------------|----------|-------|
| Priority correctness 11/11 | `replay/reports/salience_competition_report.json` | Historical replay |
| Salience score **0.72–0.73** across P1.7+ | `freeze/reality_score_timeline.json` | Stable, not gate-blocking alone |

**Not proven:** Somatic starvation fix (memory 72.5% vs somatic 31.7% in P1) — structural debt remains.

---

## 9. Governance Doctrine (Synthetic + Repair)

| Capability | Evidence | Scope |
|------------|----------|-------|
| Confidence validation / no self-cert | `governance/doctrine/confidence_validation.py`, `tests/test_governance_doctrine/` | Tests |
| Independent verification protocol | `governance/doctrine/verifier_protocol.md`, `independent_verification.md` | Documentation |
| Promotion verification gate | `governance/doctrine/promotion_verification_gate.py` | Module + repair proof |

---

## Explicitly Not in This Register

Items listed in [`freeze/unproven_claims.md`](unproven_claims.md) — long-term drift, production scale, historical continuity ≥0.95, etc.
