# Phase 1D — Missed Instinct Detection Report

**Generated:** 2026-05-14T05:10:00+00:00  
**Program:** Reality Replay — Phase 1D  
**Data Window:** 2026-05-11T12:54 → 2026-05-14T05:02 (64.14 hours)

---

## Executive Summary

Analysis of historical operational data reveals **8 missed instinct candidates** — patterns that repeated but were never promoted to permanent instincts. Three are ranked HIGH priority, three MEDIUM, and two LOW.

| Metric | Value |
|--------|-------|
| Missed instincts detected | 8 |
| HIGH priority | 3 |
| MEDIUM priority | 2 |
| LOW priority | 3 |
| Wasted governance decisions | 42 |
| Duplicate outputs | 4 |

### Detection Categories

| Category | Count |
|----------|-------|
| Repeated failures | 3 |
| Recurring recovery actions | 3 |
| Recurring governance escalations | 2 |

---

## HIGH Priority Missed Instincts

### MISSED-0001: Memory Scoring Artifact Detection

| Property | Value |
|----------|-------|
| Category | Repeated failure |
| Occurrences | 2 |
| Impact | **HIGH** — catastrophic misclassification |

**What happened:** The legacy memory health scoring formula produced a **zero score** (appearing catastrophic) when the actual risk was merely "watch" level. The root cause: baseline variance was extremely small (stddev=0.1413), causing a z-score of 12.5 that overwhelmed the scoring formula.

**Why it matters:** Memory health was reported as 0/100 when the real situation was ~44/100. This could trigger unnecessary escalations, false panic, and incorrect remediation.

**Evidence:**
- Two consecutive memory_pressure_diagnosis records detected `scoring_artifact: true`
- `legacy_z_score: 12.5442` vs `adjusted_score: 43.93`

**Recommended Instinct:**
> When baseline variance is extremely small (stddev < 0.5), apply a minimum variance floor of 1.0 before z-score calculation and flag as a scoring artifact.

---

### MISSED-0002: Repeated Reflex Without Escalation

| Property | Value |
|----------|-------|
| Category | Recurring recovery action |
| Occurrences | 2 |
| Time Span | 25 minutes |
| Impact | **HIGH** — missed escalation path |

**What happened:** The `high_memory_usage` reflex rule fired twice within 25 minutes, both times at severity="warning". The incident recall step explicitly noted `repeated_anomaly_types: {high_memory_usage: 2}`, but no automatic escalation or threshold adjustment was triggered.

**Why it matters:** The dream cycle later proposed confidence adjustments (0.15, 0.20) that remain in the recalibration queue, never applied. The system recognized the pattern but didn't act on it.

**Evidence:**
- 2 guardian reflex events with identical rule and severity
- Incident recall noted repetition but took no action
- Recalibration queue has 2 pending items, unapplied

**Recommended Instinct:**
> When the same reflex rule fires ≥2 times within 2 hours, auto-apply recalibration queue entries.

---

### MISSED-0006: Skillify Retry Without Backoff

| Property | Value |
|----------|-------|
| Category | Repeated failure |
| Occurrences | 6 |
| Time Span | 48 minutes |
| Impact | **HIGH** — governance capacity waste |

**What happened:** The Skillify pipeline submitted `auto_test_skill` for approval 6 times, each time getting rejected by governance. No exponential backoff or rejection memory was implemented, consuming **42 REVIEW_REQUIRED governance decisions**.

**Why it matters:** Repeated rejections consumed governance review capacity that could have been used for legitimate actions. The pipeline showed no learning from rejection.

**Evidence:**
- 12 governance incidents (6 rejection + 6 proposal pairs)
- 42 total governance decisions consumed by skillify agent
- Zero successful promotions

**Recommended Instinct:**
> After 2+ consecutive rejections of the same skill, apply exponential backoff: 5min → 30min → 2h → permanent cooldown.

---

## MEDIUM Priority Missed Instincts

### MISSED-0003: Docker Context Missing on First Reflex

| Property | Value |
|----------|-------|
| Category | Repeated failure |
| Occurrences | 2 |
| Impact | **MEDIUM** — incomplete diagnosis |

**What happened:** The first memory pressure diagnosis recorded `docker_vm_memory_mib: null` (missing Docker context). The second diagnosis correctly included `docker_vm_memory_mib: 8192`. The system learned mid-stream but never codified the requirement.

**Recommended Instinct:**
> Mandatory Docker context collection as prerequisite for any memory pressure diagnosis.

---

### MISSED-0007: Destructive Command from Multiple Agents

| Property | Value |
|----------|-------|
| Category | Recurring governance escalation |
| Occurrences | 2 |
| Time Span | 8.2 hours |
| Impact | **MEDIUM** — security boundary test |

**What happened:** Two agents (test, backend-agent) independently attempted `rm -rf /`, both correctly blocked. But the block for agent #1 didn't propagate awareness to agent #2.

**Recommended Instinct:**
> Broadcast block decisions to all agent safety constraints after first occurrence.

---

---

## LOW Priority Missed Instincts

### MISSED-0004: Circadian Baseline Convergence Loop

| Property | Value |
|----------|-------|
| Category | Recurring recovery action |
| Occurrences | 4 |
| Time Span | 2 minutes |
| Impact | **LOW** — wasted computation |

**What happened:** 4 circadian baseline runs within 2 minutes, converging from "normal" to "warning" severity. Last 2 runs produced identical output but still executed.

**Recommended Instinct:**
> Cache circadian baseline results; skip re-evaluation if deviation severity hasn't changed.

---

### MISSED-0008: Agent Capability Boundary Violation

| Property | Value |
|----------|-------|
| Category | Recurring governance escalation |
| Occurrences | 1 |
| Impact | **LOW** — wasted planning step |

**What happened:** frontend-agent attempted shell command execution but was blocked by agent-specific permission override. The agent lacked awareness of its own capability boundaries.

**Recommended Instinct:**
> Inject agent capability manifest into planning context to prevent unauthorized action proposals.

---

### MISSED-0005: Anomaly Explanation Duplication

| Property | Value |
|----------|-------|
| Category | Recurring recovery action |
| Occurrences | 4 |
| Time Span | 1.3 minutes |
| Impact | **LOW** — log pollution |

**What happened:** 4 anomaly explanation runs in ~2 minutes. The last 3 outputs were byte-identical (same warning count, same metrics). No content-hash dedup was applied.

**Recommended Instinct:**
> Apply content-hash deduplication to prevent storing identical anomaly explanations.

---

## Wasted Operations Summary

| Resource | Count | Source |
|----------|-------|--------|
| Governance decisions consumed by retries | 42 | Skillify rejection loop |
| Duplicate anomaly explanations | 2 | Anomaly explanation repetition |
| Duplicate circadian baseline runs | 2 | Circadian convergence loop |
| Redundant skill rejections | 10 | Skillify retry without backoff |
| **Total wasted operations** | **56** | |

---

## Methodology

1. **Repeated Failures:** Scanned all episodic, governance, and incident records for identical error types occurring multiple times.
2. **Recurring Recovery Actions:** Identified governance pipeline steps that produced identical outputs across runs.
3. **Recurring Governance Escalations:** Analyzed `governance/audit/incidents.jsonl` for repeated block events.
4. **Impact Assessment:** Based on frequency × operational cost (governance decisions consumed, false positive risk, compute waste).
5. **Ranking Formula:** HIGH = frequency ≥ 2 AND impact ≥ system-level risk; MEDIUM = frequency ≥ 2 OR impact ≥ subsystem-level; LOW = isolated or compute-only impact.

**Data Integrity:** Zero production files modified. All analysis performed read-only.
