# Technical Debt Register — P1 Closeout

**Frozen:** 2026-05-18  
**Severity:** CRITICAL > HIGH > MEDIUM > LOW

---

## CRITICAL

### TD-001: Historical union replay continuity below gate

| Field | Value |
|-------|-------|
| **Description** | 7-day union continuity **0.7712** vs gate **0.95** |
| **Evidence** | `telemetry/maturation/p17c_materialization_report.json`; `docs/releases/p17c_reality_gate.md` |
| **Impact** | Historical v0.4 gate LOCKED; full accountability narrative incomplete |
| **Remediation** | Backfill day_01–02 sparse windows (28k+ s gaps); re-run `p17c_materialize`; never delete gap audit |

### TD-002: INC-001 precursor insufficient coverage

| Field | Value |
|-------|-------|
| **Description** | Only **19** REAL records in T−60m before INC-001 (need ≥60) |
| **Evidence** | `telemetry/maturation/p17d_continuity_exception_report.json` (`inc_001_t60m`) |
| **Impact** | Historical precursor **0.56**; true-incident precursor model under-trained |
| **Remediation** | Cannot recover pre-incident data; document exception; require future incidents with pre-stable sampling |

### TD-003: Production enforcement wiring uncertain

| Field | Value |
|-------|-------|
| **Description** | Promotion guard / write gate / verifier modules created P1.5 but rollout was phased (audit → soft → full) |
| **Evidence** | `docs/releases/p15_repair_gate.md` § Migration Notes |
| **Impact** | Runtime may not block all paths until fully wired |
| **Remediation** | v0.4 stabilization: verify `PromotionGuard` on all mutation paths; integration tests for bypass attempts |

---

## HIGH

### TD-004: Historical precursor below 0.60

| Field | Value |
|-------|-------|
| **Description** | Union precursor **0.56** (P1.7C) |
| **Evidence** | `telemetry/maturation/matured_reality_score.json` |
| **Remediation** | More incidents + adequate windows; composite precursor scorer; reduce memory-saturation FP |

### TD-005: Historical circadian below 0.70

| Field | Value |
|-------|-------|
| **Description** | Union circadian **0.68** |
| **Evidence** | `docs/releases/p17c_reality_gate.md` |
| **Remediation** | ≥7 daemon-stable days; filter test artifacts; validate sensitivity deltas |

### TD-006: Circadian INSUFFICIENT_DURATION (operational)

| Field | Value |
|-------|-------|
| **Description** | **4.37** cycles in ~105h; waiver used for operational PASS |
| **Evidence** | `telemetry/maturation/p17d_continuity_exception_report.json` (`circadian_detail`) |
| **Remediation** | Continue daemon ≥168h; remove waiver dependency |

### TD-007: Maturation pipeline lag (P1.7B lesson)

| Field | Value |
|-------|-------|
| **Description** | Live telemetry existed while day files stale (4/7) — gate artifacts did not advance |
| **Evidence** | `docs/releases/p17b_reality_gate_recheck.md` |
| **Remediation** | Automate daily materialization; alert on AWAITING_CAPTURE status |

### TD-008: Core governance untested

| Field | Value |
|-------|-------|
| **Description** | `governance/policy_engine.py`, `mandatory_gate.py`, etc. lack test coverage |
| **Evidence** | `docs/releases/v0.3.1_known_limitations.md` §3 |
| **Remediation** | Add `tests/test_governance/` in v0.4 stabilization |

---

## MEDIUM

### TD-009: Salience somatic starvation

| Field | Value |
|-------|-------|
| **Description** | Somatic 31.7% attention vs memory 72.5% (P1) |
| **Evidence** | `replay/reports/salience_competition_report.json` |
| **Remediation** | Attention budget caps; somatic circuit-breaker (P1.7 recommendation) |

### TD-010: Missed instinct recall gap

| Field | Value |
|-------|-------|
| **Description** | Score **0.72**; 3 HIGH missed patterns; 56 wasted ops (P1) |
| **Evidence** | `replay/reports/missed_instinct_report.json` |
| **Remediation** | Promote HIGH patterns; deploy monitors |

### TD-011: P1.6 interpolation debt (audit-only)

| Field | Value |
|-------|-------|
| **Description** | **121** interpolated backfill records must stay excluded from scoring |
| **Evidence** | `telemetry/backfill/backfill_results.json`; P1.7C audit |
| **Remediation** | Permanent exclusion list; tag `INTERPOLATED` in tooling |

### TD-012: Kernel / observability test gaps

| Field | Value |
|-------|-------|
| **Description** | `kernel/`, core `governance/`, observability replay modules thin on tests |
| **Evidence** | `docs/releases/v0.3.1_known_limitations.md` |
| **Remediation** | v0.4 test expansion |

### TD-013: Illegal L4 entries retroactive handling

| Field | Value |
|-------|-------|
| **Description** | Phase 5 audit: demote/quarantine/tag actions not fully applied in production memory |
| **Evidence** | `docs/releases/p15_repair_gate.md` § Data Migration table |
| **Remediation** | Execute DEMOTE/QUARANTINE on FE-STRAT-*, SKILLIFY-BATCH per audit |

---

## LOW

### TD-014: Dual-score reporting complexity

| Field | Value |
|-------|-------|
| **Description** | Consumers must distinguish historical 0.8015 vs operational 0.812 |
| **Evidence** | P1.7D methodology |
| **Remediation** | Dashboard labels; API fields `reality_mode: historical|operational` |

### TD-015: Projection documents in repo

| Field | Value |
|-------|-------|
| **Description** | P1.7/P1.7B contain +7d projections that could be misread as actuals |
| **Evidence** | `docs/releases/p17_unlock_gate.md` |
| **Remediation** | Closeout marks projections; link to `freeze/unproven_claims.md` |

### TD-016: day_01 PARTIAL status

| Field | Value |
|-------|-------|
| **Description** | day_01 remains PARTIAL (664 records, 7.74h max gap) |
| **Evidence** | `telemetry/maturation/p17c_materialization_report.json` |
| **Remediation** | Accept as bootstrap record or attempt archival backfill |

---

## Debt Not Accepted as "Won't Fix"

- Lowering gate thresholds to force PASS
- Hiding bootstrap gaps or FAIL criteria
- Scoring interpolated data in official P1.7+ metrics

See [`docs/doctrine/bootstrap_gap_exception.md`](../docs/doctrine/bootstrap_gap_exception.md).
