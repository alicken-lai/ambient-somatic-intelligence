# Phase 1H — Cross-Domain Attention Competition Report

- **Generated**: 2026-05-14T13:08:00+08:00
- **Program**: Reality Replay — Phase 1H
- **Data Window**: 2026-05-11T12:54 → 2026-05-14T05:09 UTC (~64.25 hours)
- **Domain Events Analyzed**: 555 (across 5 domains)
- **Competition Windows**: 11 (1-hour windows with ≥2 domains active)
- **Salience Competition Fairness Score**: **0.72 / 1.0**

---

## Executive Summary

Cross-domain attention competition analysis reveals that **priority ordering is correct** (100% correctness) — the highest-severity signal always received attention. However, the system has a significant **somatic domain starvation problem**: only 31.7% of somatic signals receive attention, while the memory domain consumes 72.5% of the attention budget despite having the lowest average severity (0.2). The primary recommendation is to rebalance the attention budget by increasing somatic allocation and applying habituation dampening to routine memory retrievals.

---

## Domain Signal Inventory

| Domain | Events | Avg Severity | Attention Rate | Starved? |
|---|---:|---:|---:|---|
| **Somatic** | 41 | 0.442 | 31.7% | **YES** |
| **Governance** | 136 | 0.464 | 73.5% | No |
| **Memory** | 356 | 0.200 | 100.0% | No (over-attended) |
| **Skill** | 12 | 0.300 | 100.0% | No |
| **Task** | 10 | 0.600 | 100.0% | No |

---

## Priority Correctness: 100% (11/11)

In all 11 competition windows where multiple domains had simultaneous signals, the highest-severity signal was correctly identified and attended. Key examples:

### Window: 2026-05-11T21:00–22:00 UTC (Critical Incident)

- **Competing**: Somatic (guardian_reflex at 0.9) vs Memory (episodic captures at 0.2) vs Governance (approvals at 0.4)
- **Winner**: Somatic — guardian reflex trigger for memory pressure
- **Correct?** YES — real incident required immediate attention
- **Outcome**: Incident #1 detected, telemetry captured, anomaly explained

### Window: 2026-05-13T22:00–23:00 UTC (Governance Testing)

- **Competing**: Governance (BLOCK at 0.9) vs Memory (agent entries at 0.2) vs Task (blocked actions at 0.6)
- **Winner**: Governance — destructive command block (`rm -rf /`)
- **Correct?** YES — dangerous action correctly prevented

### Caveat

100% priority correctness is partly structural — `PriorityAllocator` hard-codes "must-attend" for BLOCK-level governance signals (salience ≥ 0.85) and `EscalationRouter` always escalates BLOCK-risk events. True close-competition scenarios (signals within 0.1 severity) were rare in this dataset.

---

## Starvation Analysis

### Somatic Domain — STARVED (31.7% attention)

This is the most critical finding. The somatic domain has the second-highest average severity (0.442) but the **lowest attention rate** (31.7%). Breakdown:

| Somatic Signal Type | Count | Attended | Rate | Severity |
|---|---:|---:|---:|---:|
| guardian_reflex / trigger | 4 | 4 | 100% | 0.8–0.9 |
| incident_recall | 1 | 1 | 100% | 0.7 |
| anomaly_explanation | 1 | 1 | 100% | 0.6 |
| health_score | 2 | 2 | 100% | 0.4 |
| sense_local (telemetry) | 19 | 0 | 0% | 0.3 |
| baseline_learn / circadian | 14 | 5 | 36% | 0.3 |

**Root cause**: Background telemetry snapshots (`sense_local` at severity 0.3) are never actively attended. They are captured and stored but do not compete for attention resources. High-severity somatic signals (reflex, incidents) are always attended, but the low-grade continuous monitoring is invisible to the attention system.

**Risk**: Slow-developing anomalies that manifest as gradual telemetry drift could be missed if individual snapshots don't trigger the reflex threshold.

### Memory Domain — OVER-ATTENDED (100% attention, 72.5% share)

Memory events (episodic captures, semantic lookups) all receive attention but their average severity is only 0.2. They consume a disproportionate share of the attention budget:

- **Actual share**: 72.5%
- **Ideal share by volume**: 64.1%
- **Ideal share by severity**: 12.8%
- **Fairness delta**: 8.3 percentage points over volume-fair

This over-attention to low-severity memory events crowds out somatic signals. Vision captures and telemetry summaries should habituate faster.

### Governance, Skill, Task — Healthy

These domains show appropriate attention rates. Governance at 73.5% correctly ignores routine ALLOW decisions. Skill and Task at 100% have very small samples (12 and 10 events respectively).

---

## Escalation Fairness

| Domain | Actual Share | Volume-Fair Share | Severity-Fair Share | Delta |
|---|---:|---:|---:|---:|
| Somatic | 2.6% | 7.4% | 3.3% | **-4.7%** |
| Governance | 20.4% | 24.5% | 11.4% | -4.1% |
| Memory | 72.5% | 64.1% | 12.8% | **+8.3%** |
| Skill | 2.4% | 2.2% | 0.7% | +0.3% |
| Task | 2.0% | 1.8% | 1.1% | +0.2% |

The fairness imbalance is clear: **memory receives too much attention, somatic receives too little**.

---

## Response Quality Assessment

### Correct Responses

| Event | Response | Quality |
|---|---|---|
| Memory pressure #1 (21:49 UTC) | Reflex → telemetry → incident → explanation | HIGH |
| Memory pressure #2 (22:14 UTC) | Repeat reflex with confidence calibration | HIGH (adaptive) |
| Destructive command blocks | Immediate BLOCK with policy attribution | HIGH |
| Skillify pipeline rejections | Correct governance gate enforcement | HIGH |

### Gap Identified

**Between incidents #1 and #2** (21:49 → 22:14 UTC, ~25 min gap): intermediate somatic telemetry readings were not actively monitored. The system detected incident #2 only when the reflex threshold was hit again, rather than tracking the developing issue through continuous somatic attention.

---

## Improvement Recommendations

### Priority: HIGH

1. **Fix somatic starvation**: Increase somatic domain budget from 0.30 → 0.35 in `PriorityAllocator._DEFAULT_DOMAIN_BUDGETS`. Background telemetry at severity 0.3 should receive at least passive tracking.

2. **Reduce memory over-attention**: Apply stronger recurrence habituation to memory domain signals. In `SalienceEngine`, increase `recurrence` weight for memory signals. Set memory domain budget from 0.15 → 0.10.

### Priority: MEDIUM

3. **Incident-window somatic boost**: When guardian_reflex triggers, temporarily increase all somatic signal salience by +0.2 for 30 minutes. This creates a heightened-attention window for developing issues.

4. **Enable cross-domain correlation**: The `WeakSignalDetector` already defines `(somatic, governance)` as a correlation pair. Ensure weak signals from these domains during concurrent activity receive the 0.15 correlation boost.

### Priority: LOW

5. **Improve task domain instrumentation**: Only 10 task events were captured — likely missing task queue depth, completion latency, and resource contention signals. Expand task domain signal sources.

---

## Score Breakdown

| Component | Score | Weight | Weighted |
|---|---:|---:|---:|
| Priority Correctness | 1.00 | 30% | 0.300 |
| Starvation Resistance | 0.81 | 25% | 0.203 |
| Escalation Fairness | 0.83 | 25% | 0.208 |
| Response Quality | 0.85 | 10% | 0.085 |
| Data Confidence Penalty | -0.075 | 10% | -0.075 |
| **Total** | | | **0.72** |

---

## Conclusion

The salience competition system correctly handles high-severity events but has a structural imbalance: **memory domain crowds out somatic attention**. The priority ordering is correct (100%), and critical events are never missed, but the 31.7% somatic attention rate represents a real risk for detecting slow-developing anomalies. Rebalancing the attention budget and applying habituation to memory signals are the highest-impact improvements.
