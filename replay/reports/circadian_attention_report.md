# Phase 1G — Circadian Attention Validation Report

- **Generated**: 2026-05-14T13:08:00+08:00
- **Program**: Reality Replay — Phase 1G
- **Data Window**: 2026-05-11T12:54 → 2026-05-14T05:09 UTC (~64.25 hours)
- **Total Events Analyzed**: 5,652
- **Circadian Adaptation Quality Score**: **0.52 / 1.0**

---

## Executive Summary

Analysis of ~64 hours of operational data across 5,652 timestamped events reveals a weak but meaningful circadian pattern in Ambient OS attention behavior. **Both real incidents (memory pressure) clustered in the late-night period (21:00–00:00 UTC)**, while automated test artifacts inflated anomaly counts during quiet hours. Current attention policy is time-agnostic, but the data supports modest circadian adjustments — particularly increased vigilance during late-night autonomous operations.

**Key Recommendation**: Increase salience sensitivity by 25% during late_night (21:00–00:00 UTC), where both real incidents occurred and operator presence is lowest.

---

## Data Limitations

| Limitation | Impact |
|---|---|
| Only ~64 hours of data | Covers ~2.7 circadian cycles — minimum for pattern detection |
| 2 real incidents only | Insufficient for statistical confidence in incident timing |
| No weekend data | All observations are weekdays (Mon–Wed) |
| System started mid-day | Day 1 active hours are under-sampled |
| Test artifacts | Skillify pipeline tests inflate quiet-hours anomaly counts |

---

## Time Period Definitions

| Period | UTC Range | Local (UTC+8) | Hours Covered | Description |
|---|---|---|---|---|
| Quiet Hours | 00:00–06:00 | 08:00–14:00 | 18h | Autonomous operations |
| Transition Morning | 06:00–09:00 | 14:00–17:00 | 6h | System waking up |
| Active Hours | 09:00–18:00 | 17:00–02:00 | 24h | Peak operator activity |
| Transition Evening | 18:00–21:00 | 02:00–05:00 | 9h | Activity winding down |
| Late Night | 21:00–00:00 | 05:00–08:00 | 9h | Autonomous late-night ops |

---

## Per-Period Metrics

| Period | Events/h | Anomaly/h | Escalation/h | FP Rate | Blocks | Reviews |
|---|---:|---:|---:|---:|---:|---:|
| **Quiet Hours** | 82.8 | 3.889 | 1.389 | 60% | 14 | 42 |
| **Transition Morning** | 15.5 | 0.000 | 0.167 | 0% | 0 | 0 |
| **Active Hours** | 89.2 | 0.583 | 0.125 | 71% | 3 | 3 |
| **Transition Evening** | 88.0 | 0.000 | 0.000 | 0% | 0 | 0 |
| **Late Night** | 126.3 | 1.778 | 1.556 | 50% | 2 | 8 |

---

## Key Findings

### 1. Real Incidents Cluster in Late Night

Both guardian reflex triggers occurred between 21:49 and 22:14 UTC:
- **Incident 1** (21:49:02 UTC): Memory pressure — high_memory_usage anomaly. Health score dropped from 86.99 → 65.79.
- **Incident 2** (22:14:37 UTC): Repeat memory pressure, with confidence calibration. Classified as low_confidence_watch.

Both were correctly detected and escalated. No missed escalations.

### 2. Quiet Hours Anomalies Are Test Artifacts

The 3.889 anomaly/h rate during quiet hours (highest of any period) is misleading. It is dominated by:
- Skillify pipeline governance tests generating REVIEW_REQUIRED/BLOCK decisions
- Automated skill proposal/rejection cycles during 03:15–04:03 UTC

These are **not genuine operational anomalies** but test activity. Excluding skillify test events, the quiet-hours anomaly rate drops to approximately the same level as active hours.

### 3. Active Hours Are Well-Supervised

Active hours show the lowest effective anomaly rate (0.583/h), consistent with operator presence providing real-time oversight and reducing the need for automated escalation.

### 4. Transition Periods Are Calm

Both transition periods (morning and evening) show zero or near-zero anomalies — natural candidates for reduced sensitivity, though the morning transition is notably sparse (15.5 events/h vs 88.0/h for evening).

---

## Circadian Salience Adjustment Recommendations

| Period | Sensitivity Multiplier | Rationale |
|---|---|---|
| Quiet Hours | **0.85×** | Dampen skillify test artifacts; maintain somatic baseline |
| Transition Morning | **1.10×** | Low activity = higher novelty; slight increase warranted |
| Active Hours | **1.00×** | Standard — operator present |
| Transition Evening | **1.00×** | No adjustment needed |
| Late Night | **1.25×** | **Both real incidents here**; operator absent; increase vigilance |

### Late Night Specific Adjustments

- **somatic_stress weight**: Increase to 0.18 (from 0.12) — prioritize system health signals
- **escalation_threshold**: Lower to 0.65 (from 0.75) — escalate sooner when unsupervised
- **temporal_decay half-life**: Extend to 120s (from 60s) — avoid losing track of developing issues

### Quiet Hours Specific Adjustments

- **skillify_pipeline signals**: Apply 0.6× salience dampening for routine rejections
- **somatic_anomalies**: Maintain 1.0× — never reduce sensitivity to system health
- **governance BLOCK events**: Maintain 1.0× — always attend

---

## Score Breakdown

| Factor | Score | Notes |
|---|---:|---|
| Data Sufficiency | 0.30 | ~2.7 cycles; minimum viable |
| Incident Coverage | 0.70 | Both incidents detected and escalated |
| False Positive Management | 0.45 | High rates but mostly test artifacts |
| Period Differentiation | 0.65 | Clear differences exist |
| Recommendation Actionability | 0.50 | Directionally correct; needs validation |
| **Overall** | **0.52** | Moderate — more data needed for confidence |

---

## Next Steps

1. **Accumulate 2+ weeks of data** before implementing circadian adjustments with confidence
2. **Tag test vs. production events** to improve false positive analysis
3. **Monitor late-night incident rate** — if pattern persists, elevate implementation priority
4. **Add circadian_period field** to all action log entries for easier future analysis
5. **Re-run this analysis** after Phase 2 operations to validate or revise recommendations
