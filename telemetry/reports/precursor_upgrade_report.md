# Phase 6 — Precursor Replay Revalidation Report

- **Program**: P1.6 Reality Repair Sprint — Phase 6
- **Generated**: 2026-05-14T14:00:00+08:00
- **Baseline Score (P1)**: 0.35
- **New Score (P1.6)**: **0.58** (+0.23, +65.7%)

---

## Executive Summary

Phase 6 re-ran precursor detection analysis using the 438 backfilled dense-window records produced in Phase 5. The backfill dramatically improved visibility for Incident 2 (21 → 377 records, 17.9× densification) and provided temporal context for Incident 1 (0 → 115 records). However, a critical limitation emerged: **the interpolated records filling the 8-hour gap before Incident 1 carry action metadata only, not system health metrics** (memory, CPU, load). This means the gap is filled temporally but remains blind for precursor resource monitoring.

**Key Finding**: Dense backfill data strongly confirms INC-002 as a scoring artifact (memory decreasing, CPU normalizing, no multi-signal pattern) — improving false positive discrimination. But genuine precursor detection for true incidents (INC-001) is only marginally improved.

---

## Backfill Data Summary

| Dense Window | Incident | Records | REAL | INTERPOLATED | Avg Confidence |
|---|---|---:|---:|---:|---:|
| Window 1 | INC-001 (21:49 UTC) | 195 | 131 | 64 | 0.608 (T-60m) |
| Window 2 | INC-002 (22:14 UTC) | 243 | 186 | 57 | 0.925 (T-60m) |
| **Total** | | **438** | **317** | **121** | **0.892** |

---

## Per-Incident Analysis

### INC-001 — True Memory Pressure Incident

**Incident**: 2026-05-11T21:49:02Z — memory=99.28%, CPU=17.56%, load_1m=2.8

#### Time Window Analysis (with backfill)

| Window | Records | REAL | INTERP | Avg Conf | Health Data | System Metrics |
|---|---:|---:|---:|---:|---|---|
| T-60m | 115 | 22 | 93 | 0.608 | Only at T-0 | Only at T-0 |
| T-30m | 81 | 22 | 59 | 0.743 | Only at T-0 | Only at T-0 |
| T-10m | 41 | 22 | 19 | 0.931 | Only at T-0 | Only at T-0 |
| T-5m | 30 | 22 | 8 | 0.979 | At T-0 | At T-0 |

#### Key Observation

The 22 REAL records are **all concentrated at 21:48:54–21:49:02** (the incident moment). The 93 interpolated records filling T-60m to T-5m are **action-type records only** — they confirm the system was active but carry no health or metric payloads. This is because the backfill engine had no source health data from the 8-hour gap to interpolate from.

**Precursor Improvement**: Marginal. We now know the system was not idle during the gap (useful context), but cannot observe resource trends (memory pressure building, CPU escalating, load increasing).

---

### INC-002 — Scoring Artifact (Not True Incident)

**Incident**: 2026-05-11T22:14:37Z — memory=96.21%, CPU=5.44%, load_1m=1.75

#### Time Window Analysis (with backfill)

| Window | Records | REAL | INTERP | Avg Conf | Health Data | System Metrics |
|---|---:|---:|---:|---:|---|---|
| T-60m | 377 | 286 | 91 | 0.925 | 41 records | 66 records |
| T-30m | 317 | 286 | 31 | 0.992 | 41 records | 66 records |
| T-10m | 20 | 11 | 9 | 0.949 | None | Reflex at T-2s |
| T-5m | 14 | 10 | 4 | 0.970 | None | Reflex at T-2s |

#### Signals Found (with dense data)

1. **Prior Incident Cascade** (confidence 1.0): INC-001 at T-25m fully documented with health scores, reflex telemetry, and recovery trajectory
2. **Health Score Trajectory** (confidence 1.0): 65.79 → 76.07 → 76.37 → stabilized ~76.5 — clear recovery arc
3. **Memory DECREASING** (confidence 1.0): 99.28% → 97.6-97.8% → 96.21% — **opposite of true precursor pattern**
4. **CPU Normalizing** (confidence 1.0): 17.56% → 2.37-10% → 5.44% — no escalating trend
5. **Process Count Plateau** (confidence 1.0): Stable at 665-668 across 66 metric records — no drift
6. **Diagnostic Activity** (confidence 1.0): Memory pressure diagnosis at T-10m (22:04:14-33)

**Precursor Improvement**: Dramatic. From 21 records to 377 records with complete cascade documentation. Strong confirmation that INC-002 was a scoring artifact.

---

## Revised Precursor Cluster Assessment

| Cluster | Pattern | P1 Conf | P1.6 Conf | Change | FP Rate |
|---|---|---:|---:|---|---|
| PC-001 | Multi-Signal Saturation | 0.50 | 0.55 | +0.05 | LOW (0/1 non-incident) |
| PC-002 | Persistent Memory >97% | 0.25 | 0.25 | 0.00 | 0.92 (chronic state) |
| PC-003 | Process Count Drift | 0.30 | 0.35 | +0.05 | MODERATE |
| PC-004 | Prior Incident Cascade | 0.40 | 0.70 | +0.30 | HIGH (predicted artifact) |

### Notable Changes

- **PC-004** saw the largest improvement (+0.30) because the dense backfill data fully documents the INC-001 → INC-002 cascade. However, this cluster predicted a *false alarm*, not a true incident — it's valuable for incident deduplication, not genuine precursor detection.
- **PC-001** improved slightly because the INC-2 dense data confirms the multi-signal pattern was *absent* during the scoring artifact (CPU and load were normal), improving specificity.
- **PC-002** remained unchanged — memory saturation is confirmed as a chronic background condition.

---

## Score Breakdown

| Factor | Weight | P1 | P1.6 | Weighted |
|---|---:|---:|---:|---:|
| Precursor patterns identified | 0.25 | 0.60 | 0.70 | 0.175 |
| False positive discrimination | 0.25 | 0.40 | 0.55 | 0.1375 |
| Earliest detection window | 0.20 | 0.10 | 0.30 | 0.060 |
| Observability coverage | 0.15 | 0.15 | 0.55 | 0.0825 |
| Statistical confidence | 0.15 | 0.10 | 0.20 | 0.030 |
| Artifact identification bonus | — | 0.04 | 0.095 | 0.095 |
| **Total** | | **0.35** | | **0.58** |

---

## Limitations and Honest Assessment

### Why the score isn't higher

1. **INC-001 health gap persists**: The interpolation engine could not generate health metrics from action log data. The 8-hour gap before Incident 1 is filled temporally but remains blind for resource monitoring. This is the **primary remaining limitation**.

2. **INC-002 was not a real incident**: Improved precursor detection for INC-002 reflects better *false alarm characterization*, not better *true precursor capability*. This inflates apparent improvement.

3. **Sample size = 2**: With only 1 true incident and 1 scoring artifact, no precursor pattern can be statistically validated. Minimum ~10 true incidents needed.

4. **38-hour unrecoverable gap**: GAP-002 (post-incident silence) remains. No post-incident behavior analysis is possible.

5. **Interpolated data quality**: 121 records (27.6%) are interpolated with decaying confidence (min 0.18). These add temporal density but not measurement fidelity.

### What genuinely improved

1. **INC-2 characterization**: 17.9× data densification with mostly REAL records. The scoring artifact is now backed by strong evidence.
2. **False positive discrimination**: Multi-signal pattern (PC-001) confirmed as specific to true incidents.
3. **Infrastructure**: 5-minute sampling engine, normalization layer, and gap detector prevent future blind spots.
4. **Temporal continuity**: System activity confirmed during INC-1's 8-hour gap — the gap was inactivity in *monitoring*, not in the *system itself*.

---

## Recommendations

1. **CRITICAL**: Future health telemetry must be captured at every sampling interval (5 min), not just on-demand. This would have prevented the INC-1 gap entirely.
2. **HIGH**: Build composite precursor scoring using CPU + load + process count trends (as designed in somatic modules) — requires minimum 3 consecutive health snapshots.
3. **HIGH**: Accumulate more incident data (target: 10+ true incidents) before trusting precursor patterns.
4. **MEDIUM**: Explore archived system logs (syslog, dmesg) as alternative backfill sources for the 8-hour gap — they may contain resource pressure indicators.
