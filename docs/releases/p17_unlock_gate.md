# P1.7 Reality Repair Sprint — V0.4 Unlock Gate

**Program**: P1.7 Reality Repair Sprint — Phase 9
**Generated**: 2026-05-14T14:16:00+08:00
**Data Policy**: REAL DATA ONLY — no interpolation, no synthetic augmentation

---

## Sprint Overview

P1.7 is the **operational maturity assessment** of Ambient OS, analyzing the system's ~2.7 days of real historical data (2026-05-11T12:54 → 2026-05-14T06:16 UTC) using ONLY real data — no interpolation, no synthetic augmentation.

This sprint re-evaluates all metrics from P1.6 with a stricter data policy, revealing that P1.6's gains from interpolated data were partially inflated. P1.7 provides the **honest baseline** from which to measure future progress.

---

## Data Maturity Status

| Metric | Value | Requirement | Status |
|--------|-------|-------------|--------|
| Total observation window | 65.4 hours (~2.7 days) | 168 hours (7 days) | **38.9% of target** |
| Days remaining | 4.3 days | — | Need continuous daemon operation |
| Daemon-stable coverage | 15.3 hours | 168 hours continuous | **9.1% of target** |
| Effective coverage (excl. gaps) | 33.2 hours | 168 hours | **19.8% of target** |
| DMN records | 1,448 | — | Growing at 60/hour |
| Action records | 4,362 | — | Growing at ~180/hour |
| Real incidents | 2 (1 true + 1 artifact) | 5+ for statistical validity | Insufficient |

### Timeline Composition

```
May 11 (Sun)  ████░░░░░░░░░░░░░░░░░░░░  Bootstrap + Incidents + Dark periods
May 12 (Mon)  ░░░░░░░░░░░░░░░░░░░░░░░░  OFFLINE (38h gap)
May 13 (Tue)  ░░░░░░░░░░░░████████████  Recovery + Daemon activation
May 14 (Wed)  ████████████░░░░░░░░░░░░  Daemon steady-state (ongoing)
              └── 00:00 UTC              └── 12:00 UTC            └── 24:00 UTC

█ = Real data available    ░ = No data (gap or offline)
```

---

## Analysis Results

### Phase 4 — Operational Drift Detection

**Primary finding**: The system underwent a fundamental operational transformation from sparse ad-hoc telemetry (0 events/hour during gaps) to continuous daemon-driven sampling (360 events/hour steady-state).

**Key inflection point**: 2026-05-13T15:00 UTC — daemon activation. This single event is the most significant operational improvement in the entire observation window.

| Operational Phase | Duration | Events/hr | Assessment |
|-------------------|----------|-----------|------------|
| Bootstrap burst | 43 min | 66.0 | Initialization — not representative |
| Dark period | 8.2 hr | 0.0 | Critical gap (GAP-001) |
| Incident response | 25.6 min | 790.2 | Reactive burst — dense but localized |
| Long silence | 38.2 hr | 0.0 | System offline (GAP-002) |
| Recovery | 2.6 hr | 85.0 | Agent-driven restart |
| **Daemon steady-state** | **15.3 hr** | **360.0** | **Target operational mode** |

**Circadian observation**: In daemon-stable mode, signal density is constant across all time periods. Day/night and weekday/weekend comparisons are confounded by system evolution.

### Phase 5 — Precursor Maturation (Real Data Only)

| Window | INC-1 Real Records | INC-2 Real Records |
|--------|--------------------|--------------------|
| T-60m | 0 (was 115 in P1.6) | 286 (was 377 in P1.6) |
| T-30m | 0 | 286 |
| T-10m | 0 | 11 |
| T-5m | 22 (at incident, not before) | 10 |

**Score**: 0.48 (down from P1.6's 0.58, up from P1's 0.35)

**Why the drop**: P1.6 used 121 interpolated records to fill the INC-1 T-60m gap. With real data only, INC-1 has ZERO pre-incident records. The improvement over P1 comes from: (1) 286 real records in INC-2 window, (2) daemon baseline establishment (+0.065 bonus).

### Phase 6 — Circadian Maturation (Real Data Only)

| Factor | P1 | P1.6 | P1.7 | Change |
|--------|-----|------|------|--------|
| Data sufficiency | 0.30 | 0.35 | 0.38 | +0.03 from daemon hour coverage |
| Incident coverage | 0.70 | 0.82 | 0.78 | -0.04 from excluding interpolated records |
| FP management | 0.45 | 0.58 | 0.55 | -0.03 minor reduction |
| Period differentiation | 0.65 | 0.72 | 0.60 | -0.12 daemon era shows uniform behavior |
| Recommendation actionability | 0.50 | 0.62 | 0.58 | -0.04 daemon evidence weakens urgency |

**Score**: 0.58 (down from P1.6's 0.62, up from P1's 0.52)

**Paradox**: Better coverage (18/24 hour-buckets vs 4/24) but lower differentiation because the daemon makes all periods look identical. Circadian patterns will only emerge with 7+ days of data where genuine anomalies occur at different times.

### Phase 7 — Replay Continuity

| Metric | Full Window | Daemon Era |
|--------|-------------|------------|
| Continuous coverage ratio | 28.2% | 100.0% |
| Max gap | 38.2 hours | 60 seconds |
| Gaps > 10 min | 3 | 0 |

The daemon-era continuity is **perfect** (60s tick cadence). The overall low ratio (28.2%) is entirely from historical gaps that cannot be recovered.

---

## Score Progression

| Version | Score | Classification | Key Change |
|---------|-------|----------------|------------|
| **P1** | **0.6645** | unstable | Initial evaluation — critical gaps identified |
| **P1.5** | **0.7525** | experimental | Repaired false_strategy (0.65→1.00), verifier (0.82→1.00) |
| **P1.6** | **0.7970** | experimental | Upgraded precursor (0.35→0.58), circadian (0.52→0.62) [includes interpolation] |
| **P1.7** | **0.7795** | experimental | Real-data-only correction: precursor (0.58→0.48), circadian (0.62→0.58), salience (0.72→0.73) |

### Metric Breakdown (P1.7)

| Metric | Weight | P1 | P1.5 | P1.6 | P1.7 | Weighted |
|--------|--------|-----|------|------|------|----------|
| Instinct Emergence | 0.15 | 0.88 | 0.88 | 0.88 | 0.88 | 0.1320 |
| Missed Instinct Recall | 0.15 | 0.72 | 0.72 | 0.72 | 0.72 | 0.1080 |
| False Strategy Resistance | 0.20 | 0.65 | 1.00 | 1.00 | 1.00 | 0.2000 |
| Precursor Detection | 0.15 | 0.35 | 0.35 | 0.58 | 0.48 | 0.0720 |
| Circadian Adaptation | 0.10 | 0.52 | 0.52 | 0.62 | 0.58 | 0.0580 |
| Salience Competition | 0.15 | 0.72 | 0.72 | 0.72 | 0.73 | 0.1095 |
| Verifier Consistency | 0.10 | 0.82 | 1.00 | 1.00 | 1.00 | 0.1000 |
| **COMPOSITE** | **1.00** | **0.6645** | **0.7525** | **0.7970** | **0.7795** | |

---

## V0.4 Gate Criteria Evaluation

| # | Criterion | Threshold | Actual | Verdict | Notes |
|---|-----------|-----------|--------|---------|-------|
| 1 | 7-day capture complete | 168 hours | 65.4 hours | **FAIL** | 38.9% of target. 4.3 days still needed. |
| 2 | No gap > 10 min in available data | 0 gaps | 3 gaps | **FAIL** | Max gap: 38.2 hours (GAP-002). Historical, unrecoverable. |
| 3 | Replay continuity ≥ 0.95 | 0.95 | 0.282 | **FAIL** | Daemon-era continuity is 1.00, but historical gaps drag overall to 0.282. |
| 4 | Precursor detection ≥ 0.60 | 0.60 | 0.48 | **FAIL** | Real-data-only assessment. Down from P1.6's 0.58 (interpolation-assisted). |
| 5 | Circadian adaptation ≥ 0.70 | 0.70 | 0.58 | **FAIL** | Real-data-only assessment. Daemon uniformity reduces differentiation. |
| 6 | Reality score ≥ 0.80 | 0.80 | 0.7795 | **FAIL** | 0.0205 below threshold. Classification: experimental. |

### Gate Verdict: **FAIL — 0 of 6 criteria met**

---

## Honest Assessment

### What P1.7 Reveals

1. **P1.6 was optimistic**: Interpolated data inflated precursor detection (0.58 vs real 0.48) and circadian adaptation (0.62 vs real 0.58). P1.7 corrects this.

2. **The daemon works**: Since activation, the daemon delivers perfect 60s cadence with 100% continuity. This is the foundation for all future improvement.

3. **The gap is time, not capability**: The system's current capability (360 events/hr, 60s cadence, enforcement modules active) is solid. The bottleneck is insufficient operational history.

4. **Interpolation was not worthless**: P1.6's interpolation provided useful signals (system activity confirmation, incident cascade documentation). But it should not be counted as equivalent to real precursor detection.

### Why No Criteria Pass

- **Criteria 1-3** (temporal coverage): These are purely time-dependent. The system has been stable for ~15 hours in daemon mode. It needs 168+ hours. This requires waiting, not engineering.

- **Criteria 4-5** (precursor/circadian): These require both more time AND more incidents. With only 1 true incident and 2.7 days of data, statistical validation is impossible.

- **Criterion 6** (composite score): At 0.7795, the score is 0.0205 below the 0.80 threshold. Precursor (0.48) and circadian (0.58) are the primary drag.

---

## 7-Day Projection

If the daemon continues operating at current 60s cadence for 7 more days (through May 21):

| Metric | Current (P1.7) | Projected (P1.7 + 7d) | Confidence |
|--------|----------------|------------------------|------------|
| Observation window | 65.4 hr | 233 hr (~9.7 days) | HIGH |
| Daemon-stable coverage | 15.3 hr | 183 hr | HIGH |
| Complete circadian cycles | 0.64 | 7.64 | HIGH |
| Hour-bucket coverage | 18/24 | 24/24 | HIGH |
| Precursor detection | 0.48 | **0.62** | MODERATE |
| Circadian adaptation | 0.58 | **0.72** | MODERATE-HIGH |
| Salience competition | 0.73 | **0.75** | HIGH |
| Replay continuity | 0.282 | **0.79** | HIGH |
| **Composite score** | **0.7795** | **0.8165** | MODERATE |
| **Classification** | experimental | **operationally-usable** | — |

### Projection Methodology

- **Precursor detection (0.48 → 0.62)**: Full normal baseline across all periods + improved observability coverage. Conservative: assumes 0-1 new incidents.
- **Circadian adaptation (0.58 → 0.72)**: 7 complete cycles enable period differentiation. Weekend data adds new dimension.
- **Salience competition (0.73 → 0.75)**: Marginal — structural issue requires code change.
- **Replay continuity (0.282 → 0.79)**: 183h daemon / 233h total ≈ 0.79. Would reach 0.95 only with ~10 more uninterrupted days.

### Gate Criteria at +7 Days

| # | Criterion | Threshold | Projected | Verdict |
|---|-----------|-----------|-----------|---------|
| 1 | 7-day capture | 168 hr | 183 hr | **PASS** |
| 2 | No gap > 10 min | 0 gaps | 3 historical gaps | **FAIL** (historical) |
| 3 | Continuity ≥ 0.95 | 0.95 | 0.79 | **FAIL** |
| 4 | Precursor ≥ 0.60 | 0.60 | 0.62 | **PASS** (projected) |
| 5 | Circadian ≥ 0.70 | 0.70 | 0.72 | **PASS** (projected) |
| 6 | Reality score ≥ 0.80 | 0.80 | 0.8165 | **PASS** (projected) |

**Projected verdict at +7d**: **PARTIAL PASS — 4 of 6 criteria met**

Criteria 2 and 3 will remain failed because of unrecoverable historical gaps. These criteria should be re-baselined to measure **daemon-era continuity** (currently 1.00) rather than entire-history continuity.

---

## Final Verdict

### P1.7 Gate Result: **FAIL — PARTIAL PASS with positive trajectory**

The V0.4 unlock gate does NOT pass at P1.7. However:

1. **The trajectory is positive**: P1→P1.7 shows genuine +0.115 improvement (from 0.6645 to 0.7795)
2. **The daemon infrastructure is solid**: 60s cadence, 100% continuity, enforcement modules active
3. **The bottleneck is time**: 4.3 more days of daemon operation should bring the score above 0.80
4. **The historical gaps are permanent**: Criteria 2 and 3 need re-baselining for practical utility

### Concrete Next Steps

1. **IMMEDIATE**: Ensure the `night35-dmn-tick` daemon continues running uninterrupted
   - Target: 7 days continuous from now (through 2026-05-21)
   - Monitor: daemon health via `state/daemon/dmn_tick_status.json`

2. **AT 7 DAYS (2026-05-21)**: Re-run P1.7 gate evaluation
   - Expected: composite score ≈ 0.82 (operationally-usable)
   - Expected: 4 of 6 gate criteria pass
   - Action: If score ≥ 0.80, propose re-baselined gate criteria for v0.4

3. **GATE RE-BASELINE PROPOSAL**: For v0.4 readiness, modify:
   - Criterion 2: "No gap > 10 min **in daemon era**" (currently PASS at 1.00)
   - Criterion 3: "Replay continuity ≥ 0.95 **in daemon era**" (currently PASS at 1.00)
   - Rationale: Historical gaps predate the current operational mode and are unrecoverable

4. **ARCHITECTURAL**: Address salience competition fairness (0.73)
   - Implement attention budget caps per domain
   - Add somatic domain starvation circuit-breaker
   - This is the one metric that won't improve with more data alone

### v0.4 Readiness Recommendation

**NOT READY** — but on track. Deploy the sampling engine, wait 7 days, re-evaluate. The system is 0.0205 below the operationally-usable threshold with a clear path to crossing it.

Expected v0.4 readiness date: **2026-05-21** (conditional on daemon stability and gate re-baselining).

---

## Appendix: Files Created in P1.7

| File | Purpose |
|------|---------|
| `telemetry/maturation/drift_report.json` | Phase 4: Operational drift analysis |
| `telemetry/maturation/circadian_observation.md` | Phase 4: Human-readable circadian observations |
| `telemetry/maturation/precursor_maturation_report.json` | Phase 5: Precursor analysis (real data only) |
| `telemetry/maturation/circadian_maturation_report.json` | Phase 6: Circadian analysis (real data only) |
| `telemetry/maturation/replay_revalidation_report.json` | Phase 7: Full replay revalidation |
| `telemetry/maturation/matured_reality_score.json` | Phase 8: Reality score recompute |
| `observability/replay/matured_reality_score.py` | Phase 8: Scoring module (P1→P1.5→P1.6→P1.7) |
| `docs/releases/p17_unlock_gate.md` | Phase 9: This gate document |
