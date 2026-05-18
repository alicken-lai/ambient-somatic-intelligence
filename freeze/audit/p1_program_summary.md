# P1 Reality Replay Program — Executive Summary

**Closeout date:** 2026-05-18  
**Program status:** COMPLETE (documentation freeze)  
**Authoritative inventory:** [`freeze/audit/p1_program_inventory.json`](p1_program_inventory.json)

---

## Verdict

The P1 Reality Replay Program ran from initial historical replay (P1) through operational unlock (P1.7D). **Synthetic cognition is strong** (382/382 tests, ontology health 0.9592). **Historical union reality is operationally usable but gate-locked** (score 0.8015, 3/6). **Daemon-era operational reality is unlocked** (score 0.812, 5/5). v0.4 stabilization may begin under the operational contract with documented caveats.

---

## Score Trajectory

| Phase | Date | Reality Score | Δ vs prior | Gate |
|-------|------|---------------|------------|------|
| P1 | 2026-05-14 | **0.6645** | — | FAIL (2/6) |
| P1.5 | 2026-05-14 | **0.7525** | +0.0880 | PARTIAL (4/5 repair) |
| P1.6 | 2026-05-14 | **0.7970** | +0.0445 | FAIL (2/5) |
| P1.7 | 2026-05-14 | **0.7795** | −0.0175 | FAIL (0/6) |
| P1.7B | 2026-05-18 | **0.7795** | 0 | FAIL (1/6) LOCKED |
| P1.7C | 2026-05-18 | **0.8015** | +0.0220 | FAIL (3/6) LOCKED |
| P1.7D Operational | 2026-05-18 | **0.812** | +0.0105 | **PASS (5/5) UNLOCKED** |

See [`freeze/reality_score_timeline.json`](../reality_score_timeline.json) for metric-level breakdowns.

---

## What Each Phase Proved

### P1 — Replay framework works; cognition immature

- All replay phases (1C–1J) completed in sandbox without production mutation.
- Composite **0.6645 (unstable)** driven by precursor (0.35), false strategy resistance (0.65), verifier gaps.
- Evidence: [`replay/reports/reality_replay_score.json`](../../replay/reports/reality_replay_score.json), [`docs/releases/p1_reality_gate.md`](../../docs/releases/p1_reality_gate.md).

### P1.5 — Promotion integrity repaired

- Illegal promotion paths blocked; false strategy resistance and verifier consistency → **1.00**.
- Composite rose to **0.7525** but still below 0.80 (precursor/circadian unchanged).
- Evidence: [`repair/reports/repaired_reality_score.json`](../../repair/reports/repaired_reality_score.json), [`docs/releases/p15_repair_gate.md`](../../docs/releases/p15_repair_gate.md).

### P1.6 — Telemetry infrastructure built

- Sampling, gap detection, backfill, and runtime modules created.
- Precursor 0.35→0.58, circadian 0.52→0.62 (with interpolation in incident windows).
- Composite **0.7970** — 0.003 below 0.80 threshold.
- **121 interpolated records** later excluded from official scoring.
- Evidence: [`telemetry/reports/telemetry_reality_score.json`](../../telemetry/reports/telemetry_reality_score.json), [`docs/releases/p16_reality_gate.md`](../../docs/releases/p16_reality_gate.md).

### P1.7 — Honest real-data baseline

- Removing interpolation dropped precursor/circadian; composite **0.7795**.
- Daemon steady-state: **100% continuity**, 360 events/hr after 2026-05-13T15:00Z.
- Evidence: [`telemetry/maturation/matured_reality_score.json`](../../telemetry/maturation/matured_reality_score.json), [`docs/releases/p17_unlock_gate.md`](../../docs/releases/p17_unlock_gate.md).

### P1.7B — Recheck confirmed lock

- Score unchanged at **0.7795**; live data grew but maturation artifacts stale (4/7 days).
- Evidence: [`docs/releases/p17b_reality_gate_recheck.md`](../../docs/releases/p17b_reality_gate_recheck.md).

### P1.7C — Historical materialization

- All 7 maturation days populated (REAL only); composite **0.8015** crosses 0.80.
- Union continuity **0.7712**; still fails precursor (0.56), circadian (0.68), continuity (0.95) gates.
- Evidence: [`telemetry/maturation/p17c_materialization_report.json`](../../telemetry/maturation/p17c_materialization_report.json), [`docs/releases/p17c_reality_gate.md`](../../docs/releases/p17c_reality_gate.md).

### P1.7D — Operational unlock

- **64 BOOTSTRAP_GAP** intervals classified; **0 DAEMON_FAILURE** in stable window.
- Operational continuity **1.0000**; operational score **0.812**; gate **PASS 5/5**.
- INC-001 T−60m: **INSUFFICIENT_COVERAGE** (19 REAL records).
- Evidence: [`telemetry/maturation/p17d_continuity_exception_report.json`](../../telemetry/maturation/p17d_continuity_exception_report.json), [`docs/releases/p17d_operational_unlock_gate.md`](../../docs/releases/p17d_operational_unlock_gate.md).

---

## Dual-Score Model (Frozen)

| Mode | Score | Continuity | Gate | Use |
|------|-------|------------|------|-----|
| **Historical (P1.7C)** | 0.8015 | 0.7712 | FAIL 3/6 LOCKED | Full 7-day union accountability |
| **Operational (P1.7D)** | 0.812 | 1.0000 | PASS 5/5 UNLOCKED | Daemon-era sensing contract |

Doctrine: [`docs/doctrine/bootstrap_gap_exception.md`](../../docs/doctrine/bootstrap_gap_exception.md)

---

## Accepted Exceptions

1. **BOOTSTRAP_GAP (64):** Pre-daemon sparse capture; excluded from operational continuity denominator, retained in historical audit.
2. **INC-001 insufficient precursor coverage:** Documented; not hidden; excluded from operational precursor numerator.
3. **Circadian INSUFFICIENT_DURATION:** Operational score 0.71 with waiver path at 4.37 cycles (<7 days).
4. **P1.6 interpolation (121 records):** Audited and excluded from P1.7+ scoring.

---

## P1 Program Outcome

| Dimension | Status |
|-----------|--------|
| Replay sandbox integrity | Proven |
| Promotion / verifier enforcement | Proven (synthetic + repair revalidation) |
| Telemetry daemon steady-state | Proven (~105h window) |
| Historical union gate (6 criteria) | **Not passed** — continuity, precursor, circadian |
| Operational gate (5 criteria) | **Passed** |
| v0.4 stabilization authorization | **Yes, with caveats** — see [`docs/releases/v04_readiness_declaration.md`](../../docs/releases/v04_readiness_declaration.md) |

---

## Related Freeze Artifacts

- [`freeze/reality_score_evolution.md`](../reality_score_evolution.md)
- [`freeze/proven_capabilities.md`](../proven_capabilities.md)
- [`freeze/unproven_claims.md`](../unproven_claims.md)
- [`freeze/technical_debt_register.md`](../technical_debt_register.md)
- [`docs/releases/p1_reality_replay_program_closeout.md`](../../docs/releases/p1_reality_replay_program_closeout.md)
