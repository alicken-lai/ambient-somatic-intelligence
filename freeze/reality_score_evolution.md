# Reality Score Evolution — P1 Program

**Frozen:** 2026-05-18  
**Machine-readable timeline:** [`freeze/reality_score_timeline.json`](reality_score_timeline.json)

---

## Summary Chart

```
0.6645  P1      unstable      integrity + telemetry gaps
0.7525  P1.5    experimental  promotion repair (+0.088)
0.7970  P1.6    experimental  telemetry upgrade (+0.045); interpolation-assisted
0.7795  P1.7    experimental  real-only correction (−0.018)
0.7795  P1.7B   experimental  recheck — no score change
0.8015  P1.7C   op-usable     7-day materialization (+0.022)
0.812   P1.7D   op-usable     operational window (+0.011)
```

---

## Why the Score Rose

### P1 → P1.5 (+0.0880): Architectural repair

| Metric | P1 | P1.5 | Driver |
|--------|-----|------|--------|
| False strategy resistance | 0.65 | **1.00** | `PromotionChainValidator`, `StrategicWriteGate`, `PromotionVerificationGate` |
| Verifier consistency | 0.82 | **1.00** | `VerifierEnforcement`; self-certification blocked |

No change to precursor (0.35) or circadian (0.52) — **data maturity**, not code, limited those metrics.

### P1.5 → P1.6 (+0.0445): Data maturity (with interpolation)

| Metric | P1.5 | P1.6 | Driver |
|--------|------|------|--------|
| Precursor | 0.35 | **0.58** | Backfill densified incident windows; 438 records (317 REAL, 121 INTERPOLATED) |
| Circadian | 0.52 | **0.62** | Late-night lifecycle documented; +438 events in late_night bucket |

**Architectural:** New `telemetry/` stack (schema, sampling, runtime, backfill).  
**Data:** Interpolation inflated precursor/circadian vs what P1.7 would later measure.

### P1.7C (+0.0220 vs P1.7B): Materialization on full REAL window

| Metric | P1.7/P1.7B | P1.7C | Driver |
|--------|------------|-------|--------|
| Precursor | 0.48 | **0.56** | 7-day REAL maturation; INC-002 adequate coverage |
| Circadian | 0.58 | **0.68** | More hour-buckets with health data; daemon-era coverage |

Static metrics (instinct 0.88, false strategy 1.00, verifier 1.00) unchanged — replay-phase scores held.

### P1.7C → P1.7D Operational (+0.0105): Window re-baselining

| Metric | Historical | Operational | Driver |
|--------|------------|-------------|--------|
| Precursor | 0.56 | **0.61** | Score only **covered incidents** in daemon window; INC-001 excluded |
| Circadian | 0.68 | **0.71** | Daemon-window-only factors; waiver for INSUFFICIENT_DURATION |

Not a global improvement in sensing quality — a **scope change** with documented doctrine.

---

## Why the Score Dropped

### P1.6 → P1.7 (−0.0175): Real-data-only discipline

| Metric | P1.6 | P1.7 | Why |
|--------|------|------|-----|
| Precursor | 0.58 | **0.48** | INC-1 T−60m: 0 real records (was 115 with interpolation) |
| Circadian | 0.62 | **0.58** | Interpolated incident coverage removed; daemon uniformity lowers differentiation |

**Lesson frozen:** P1.6 gains on precursor/circadian were partially **data fabrication**, not operational sensing. P1.7 corrected the record.

---

## Architectural vs Data Maturity Changes

| Change type | Phases | Examples |
|-------------|--------|----------|
| **Architectural** | P1.5 | Promotion guard, write gate, verifier enforcement |
| **Architectural** | P1.6 | Telemetry schema, 5-min sampling policy, gap detector, launchd runtime |
| **Architectural** | P1.7D | BOOTSTRAP_GAP classification; dual historical/operational scoring |
| **Data maturity** | P1.6 | Backfill, denser incident windows (incl. interpolation) |
| **Data maturity** | P1.7–P1.7C | Daemon capture, 7-day materialization, union continuity 0.28→0.77 |
| **Scope / doctrine** | P1.7D | Operational denominator excludes bootstrap; precursor on covered incidents only |

**Weights and scoring modules were not modified during P1 closeout** — only inputs and evaluation scope changed.

---

## Continuity Parallel Track

| Milestone | Continuity | Notes |
|-----------|------------|-------|
| P1.7 full window | 0.282 | Historical gaps dominate |
| P1.7B live | 0.749 | Extended calendar span |
| P1.7C union | **0.7712** | 1436/1862 five-minute slots |
| P1.7D daemon-stable | **1.0000** | 1260/1260 slots; 0 DAEMON_FAILURE |

Historical union continuity **cannot reach 0.95** without backfilling day_01–day_02 (28k+ second gaps) — see P1.7C recommendation in [`telemetry/maturation/p17c_materialization_report.json`](../telemetry/maturation/p17c_materialization_report.json).

---

## Frozen Interpretation Rules

1. **Do not compare P1.6 precursor/circadian to P1.7+ without noting interpolation.**
2. **Historical score 0.8015 does not imply historical gate pass** — 3/6 criteria still fail.
3. **Operational score 0.812 authorizes v0.4 stabilization**, not production deployment at 0.95+.
4. **Projections in gate docs are not actuals** — only scores in `freeze/reality_score_timeline.json` are frozen facts.
