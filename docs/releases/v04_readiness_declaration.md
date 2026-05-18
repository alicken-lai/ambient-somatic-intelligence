# v0.4 Readiness Declaration

**Declaration date:** 2026-05-18  
**Declaring authority:** P1 Reality Replay Program closeout  
**Master closeout:** [`p1_reality_replay_program_closeout.md`](p1_reality_replay_program_closeout.md)

---

## Declaration

> **The v0.4 STABILIZATION PROGRAM MAY BEGIN.**

This authorization is **operational**, not a declaration of production deployment or historical full-gate passage.

---

## Frozen Entry Metrics

| Metric | Value | Mode | Evidence |
|--------|-------|------|----------|
| **Reality Score** | **0.8015** | Historical (P1.7C) | `telemetry/maturation/matured_reality_score.json` |
| **Reality Score** | **0.812** | Operational (P1.7D) | `telemetry/maturation/p17d_continuity_exception_report.json` |
| **Replay continuity** | **0.7712** | Historical union | `telemetry/maturation/p17c_materialization_report.json` |
| **Replay continuity** | **1.0000** | Operational (daemon-stable) | `freeze/daemon_stable_window.json` |
| **Historical gate** | FAIL **3/6** | LOCKED | `docs/releases/p17c_reality_gate.md` |
| **Operational gate** | **PASS 5/5** | **UNLOCKED** | `docs/releases/p17d_operational_unlock_gate.md` |

Computation (historical):  
`0.15×0.88 + 0.15×0.72 + 0.2×1.0 + 0.15×0.56 + 0.1×0.68 + 0.15×0.73 + 0.1×1.0 = 0.8015`

Computation (operational):  
`0.15×0.88 + 0.15×0.72 + 0.2×1.0 + 0.15×0.61 + 0.1×0.71 + 0.15×0.73 + 0.1×1.0 = 0.812`

---

## Gate Status at Entry

### Historical (P1.7C) — LOCKED

| # | Criterion | Result |
|---|-----------|--------|
| 1 | 7 full days REAL telemetry | **PASS** |
| 2 | No interpolation in scoring | **PASS** |
| 3 | Reality Score ≥ 0.80 | **PASS** (0.8015) |
| 4 | Precursor ≥ 0.60 | **FAIL** (0.56) |
| 5 | Circadian ≥ 0.70 | **FAIL** (0.68) |
| 6 | Continuity ≥ 0.95 | **FAIL** (0.7712) |

### Operational (P1.7D) — UNLOCKED

| Criterion | Result |
|-----------|--------|
| No DAEMON_FAILURE >10 min in stable window | **PASS** (0 gaps) |
| Operational continuity ≥ 0.95 | **PASS** (1.0) |
| Precursor ≥ 0.60 (covered incidents) | **PASS** (0.61) |
| Circadian ≥ 0.70 or waiver | **PASS** (0.71, INSUFFICIENT_DURATION) |
| Operational Reality Score ≥ 0.80 | **PASS** (0.812) |

---

## Mandatory Caveats

The stabilization program **must** carry these caveats in all v0.4 planning and external communication:

1. **Circadian INSUFFICIENT_DURATION** — Only **4.37** complete cycles in ~105h daemon window; long-term circadian adaptation **unproven** ([`freeze/unproven_claims.md`](../../freeze/unproven_claims.md)).

2. **Bootstrap debt** — **64** BOOTSTRAP_GAP intervals permanently documented; historical union continuity **0.7712**; day_01–02 sparse windows not backfilled at closeout ([`docs/doctrine/bootstrap_gap_exception.md`](../doctrine/bootstrap_gap_exception.md)).

3. **Long-term drift unproven** — No 30-day operational drift validation ([`freeze/unproven_claims.md`](../../freeze/unproven_claims.md)).

4. **INC-001** — Precursor window **INSUFFICIENT_COVERAGE** (19 REAL records T−60m); not hidden, not scored as operational failure.

5. **Historical gate LOCKED** — v0.4 does **not** inherit a PASS on the 6-criterion historical gate.

6. **P1 program COMPLETE** — Further work is **v0.4 stabilization**, not extension of P1 scoring without a new program ID.

---

## Synthetic Parallel (Not Reality Score)

| Check | Result |
|-------|--------|
| Unit / integration tests | **382/382** pass |
| Ontology health | **0.9592** (stable) |

Evidence: [`v0.3.1_release_gate.md`](v0.3.1_release_gate.md)

Synthetic health **does not override** historical reality gate failures.

---

## Authorized Next Work

Per [`v04_inheritance_contract.md`](v04_inheritance_contract.md):

- Wire enforcement modules to production paths
- Automate maturation pipeline
- Extend daemon-stable capture (target ≥168h)
- Attempt REAL backfill for bootstrap days (audited)
- Close TD-001–TD-008 from [`freeze/technical_debt_register.md`](../../freeze/technical_debt_register.md)

---

## Explicitly Not Authorized

- Claim production-ready (≥0.95 reality) status
- Delete or redact P1 FAIL reports
- Score interpolated data in official REAL-only metrics
- Lower frozen gate thresholds without governance review

---

## Sign-Off Chain

| Document | Role |
|----------|------|
| [`p1_reality_replay_program_closeout.md`](p1_reality_replay_program_closeout.md) | Program complete |
| [`freeze/audit/p1_program_summary.md`](../../freeze/audit/p1_program_summary.md) | Audit summary |
| [`v04_inheritance_contract.md`](v04_inheritance_contract.md) | Stabilization rules |
| This declaration | **Stabilization MAY BEGIN** |

---

**P1 Reality Replay Program: COMPLETE.**  
**v0.4 Stabilization: AUTHORIZED (operational unlock, historical caveats).**
