# P1.7B — Real-Only Reality Gate Recheck (RERUN)

**Date:** 2026-05-18T15:45:00+08:00  
**Recheck ID:** P1.7B-rerun  
**Data as of:** 2026-05-18T07:33:52 UTC (latest `actions.jsonl` / `dmn.jsonl`)  
**Classification:** Experimental  
**Gate Verdict:** FAIL (1/6 criteria passed)  
**v0.4 Status:** LOCKED

---

## Executive Summary

This is a **fresh rerun** of P1.7B strict verification. Per-day REAL-only stats were recomputed from `day_01.json`–`day_07.json`. The composite Reality Score was recomputed from `observability/replay/matured_reality_score.py`.

**Result:** Reality Score **0.7795** (unchanged). Gate **FAIL** (1/6). v0.4 **LOCKED**.

**What changed since the prior P1.7B run (2026-05-14):**

| Item | Prior (May 14) | This rerun (May 18) |
|------|----------------|---------------------|
| Live telemetry span | ~65.4 h | **~162.7 h** |
| Calendar days in live logs | 4 effective | **8** (May 11–18) |
| Maturation day files populated | 4/7 | **4/7 (unchanged)** |
| Replay continuity (live) | 0.282 (P1.7 window) | **0.749** (still &lt; 0.95) |
| Daemon-era hours | 15.3 h | **112.6 h** at 1.00 continuity |
| Reality Score | 0.7795 | **0.7795** |
| Gate verdict | FAIL 1/6 | **FAIL 1/6** |

**Critical finding:** Live telemetry has accumulated through **May 18**, but `day_05.json`–`day_07.json` remain `AWAITING_CAPTURE`. Gate criterion 1 is evaluated on official maturation day files and **still fails**. Precursor/circadian scores were **not regenerated** in this rerun (still P1.7 reports on the May 14-truncated window).

---

## Verification Methodology

1. **Per-day recompute:** Parsed all 7 day files; counted REAL vs INTERPOLATED per record.
2. **Interpolation scan:** Zero `INTERPOLATED` tags in any day file record array.
3. **Backfill audit:** 121 interpolated records from P1.6 `backfill_results.json` — excluded from scoring.
4. **Score recompute:** `compute_p17_score()` → 0.7795.
5. **Live cross-check:** `memory/dmn.jsonl`, `logs/actions.jsonl`, `state/daemon/dmn_tick_status.json` (daemon `ok`, last tick 2026-05-18T07:32:52 UTC).
6. **Replay continuity (live):** Recomputed gap analysis on `actions.jsonl` for the full May 11–18 window.

---

## Step 1: Per-Day Real Data (Maturation Files)

| Day | Date | Status | Real Records | Max Gap | Coverage |
|-----|------|--------|-------------|---------|----------|
| 01 | 2026-05-11 | PARTIAL | 664 | 27,857s (7.74h) | 43.6% |
| 02 | 2026-05-12 | PARTIAL | 1,420 | 28,463s (7.91h) | 96.5% |
| 03 | 2026-05-13 | CAPTURED | 8,536 | 2,063s (34.4m) | 99.6% |
| 04 | 2026-05-14 | PARTIAL | 3,912 | 240s (4.0m) | 26.3% |
| 05 | 2026-05-15 | **AWAITING** | 0 | — | 0% |
| 06 | 2026-05-16 | **AWAITING** | 0 | — | 0% |
| 07 | 2026-05-17 | **AWAITING** | 0 | — | 0% |

**Totals (maturation files):**

- Days with data: **4 / 7**
- Total REAL records: **14,532**
- Interpolated in day files: **0**
- Interpolated rejected (P1.6 backfill): **121**
- Capture hours in day files: **63.86 / 168** = **38.0%**

### Maturation pipeline lag

Live `actions.jsonl` shows records on **2026-05-15, 16, 17, and 18**, but maturation day files were **not updated** after the May 14 snapshot. The daemon has been healthy (`status: ok`) through May 18. **Gate criterion 1 uses maturation day files** and therefore still fails, even though raw telemetry exists for additional calendar days.

---

## Step 2: Interpolation Rejection

| Check | Result |
|-------|--------|
| Day file INTERPOLATED tags | **0** |
| P1.6 backfill interpolated | **121 excluded** |
| P1.7 report policies | **REAL DATA ONLY** |

**Verdict: PASS** (criterion 2)

---

## Step 3: Reality Score (Recomputed)

| Metric | Weight | Value | Weighted |
|--------|--------|-------|----------|
| Instinct Emergence Precision | 0.15 | 0.88 | 0.1320 |
| Missed Instinct Recall | 0.15 | 0.72 | 0.1080 |
| False Strategy Resistance | 0.20 | 1.00 | 0.2000 |
| Precursor Detection | 0.15 | 0.48 | 0.0720 |
| Circadian Adaptation | 0.10 | 0.58 | 0.0580 |
| Salience Competition | 0.15 | 0.73 | 0.1095 |
| Verifier Consistency | 0.10 | 1.00 | 0.1000 |

```
0.1320 + 0.1080 + 0.2000 + 0.0720 + 0.0580 + 0.1095 + 0.1000 = 0.7795
```

**Verified Reality Score: 0.7795** (Experimental — 0.0205 below 0.80)

Precursor (0.48) and circadian (0.58) are from P1.7 reports ending **2026-05-14T06:16 UTC**. A full-window rerun after day-file materialization may change these.

### Score progression

| Version | Score | Note |
|---------|-------|------|
| P1 | 0.6645 | Initial |
| P1.5 | 0.7525 | Enforcement modules |
| P1.6 | 0.7970 | Includes interpolation |
| P1.7 | 0.7795 | Real-only correction |
| P1.7B (May 14) | 0.7795 | Verified |
| **P1.7B-rerun (May 18)** | **0.7795** | **Confirmed — no change** |

---

## Step 4: V0.4 Unlock Gate (6 Criteria)

| # | Criterion | Threshold | Actual | Verdict | Gap |
|---|-----------|-----------|--------|---------|-----|
| 1 | 7 full days REAL telemetry | 7/7 | **4/7** day files; 3 AWAITING | **FAIL** | Materialize day_05–07 |
| 2 | No interpolated in scoring | 0 used | 0 used (121 rejected) | **PASS** | — |
| 3 | Reality Score ≥ 0.80 | 0.80 | 0.7795 | **FAIL** | −0.0205 |
| 4 | Precursor detection ≥ 0.60 | 0.60 | 0.48 | **FAIL** | −0.12 |
| 5 | Circadian adaptation ≥ 0.70 | 0.70 | 0.58 | **FAIL** | −0.12 |
| 6 | Replay continuity ≥ 0.95 | 0.95 | **0.749** (live) | **FAIL** | −0.201 |

### Replay continuity detail

| Window | Hours | Continuity | Notes |
|--------|-------|------------|-------|
| P1.7 frozen (May 14) | 65.37 | 0.282 | Historical gaps dominate |
| **Live (May 18)** | **162.55** | **0.749** | Improved; still below 0.95 |
| Daemon era only | 112.55 | **1.00** | Max gap 0s in actions log |

Criterion 6 **improved materially** (+0.467) but **still fails** because early May 11–13 gaps remain in the full observation window.

### Gate verdict: **FAIL — 1/6 passed**

### v0.4 status: **LOCKED**

---

## Comparison to Prior P1.7B (2026-05-14)

| Dimension | Changed? |
|-----------|----------|
| Reality Score 0.7795 | No |
| Gate 1/6 FAIL | No |
| v0.4 LOCKED | No |
| Live data span | **Yes** (+97h) |
| Replay continuity (live) | **Yes** (0.282 → 0.749) |
| Day file population | **No** (still 4/7) |
| Daemon-era hours | **Yes** (15.3 → 112.6) |

The system has been **collecting data** but the **gate artifacts** (maturation day files + P1.7 sub-reports) were not refreshed. Unlock remains blocked on pipeline materialization and metric regeneration, not on daemon uptime.

---

## Next Actions

1. **IMMEDIATE:** Run maturation pipeline to populate `day_05.json`–`day_07.json` and extend `day_04.json` through end-of-day May 14+ from live REAL sources.
2. **THEN:** Regenerate `precursor_maturation_report.json`, `circadian_maturation_report.json`, and `replay_revalidation_report.json` on the full 7-day REAL window.
3. **Re-run gate:** Earliest **2026-05-19** after day files and reports are current.

### Projection (labeled PROJECTION — not actual)

If 7 maturation days are populated and daemon stability continues:

| Metric | Current | Projected |
|--------|---------|-----------|
| Precursor | 0.48 | 0.62 |
| Circadian | 0.58 | 0.72 |
| Replay continuity | 0.749 | ~0.95 |
| Composite | 0.7795 | 0.8165 |

**Confidence:** MODERATE — requires maturation rerun, not just waiting.

---

## Honest Assessment

P1.7B-rerun **confirms** the prior conclusion: scoring is clean (zero interpolation), the composite is **0.7795**, and v0.4 stays **LOCKED**. The new information is operational: **~4 extra days of live telemetry exist** but were **not ingested into maturation day files**, so the formal gate did not advance. Replay continuity on the live window rose to **0.749** but remains below **0.95**. Unlock requires **maturation pipeline work**, then a full metric regeneration — not merely calendar time passing.
