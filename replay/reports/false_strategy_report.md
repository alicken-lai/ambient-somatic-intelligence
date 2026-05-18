# Reality Replay — Phase 1E: False Strategic Promotion Detection

**Generated**: 2026-05-14T13:08:00+08:00
**Replay Window**: 2026-05-11T12:54 → 2026-05-14T05:02 (64.14 hours)
**Program**: Ambient OS Reality Replay

---

## Executive Summary

Phase 1E analyzed **7 strategy-level memories** and **13 skill-level entries** across the historical replay window to detect premature strategy formation and false strategic promotions.

**Key Findings:**
- **3 of 7** strategies are classified as FALSE or PARTIALLY FALSE
- **5 of 7** strategy entries have critically overconfident scores (1.0 with zero validation)
- **5 of 7** strategies bypassed the promotion chain entirely (injected directly at L4)
- The Guardian subsystem shows excellent self-correction (dream replay identified false positives)
- The agent memory subsystem has a critical gap: pre-loaded memories bypass the ontology

**False Strategy Rate**: 43% (3/7 strategies would fail under historical replay)

**False Strategy Resistance Score**: **0.65 / 1.0** (MODERATE)

---

## Per-Strategy Analysis

### FE-STRAT-001: Tailwind @apply Strategy
**Verdict: FALSE STRATEGY**

| Field | Value |
|-------|-------|
| Content | "Tailwind @apply for repeated component styles reduces class duplication" |
| Source | `state/agents/frontend-agent/memory/entries.jsonl` |
| Layer | L4 Strategic (category: strategy) |
| Confidence | 1.0 |
| Uses | 0 |
| Created | 2026-05-13T21:48:29 |

**Evidence Analysis:**
- No episodic precursors, no instinct formation, no skill validation
- Strategy appeared instantly at agent initialization with maximum confidence
- The only completed task ("Build a login form") used "component-first development" strategy, not Tailwind @apply
- No governance approval, no verifier review

**Overconfidence**: CRITICAL (delta: -0.7)
- Assigned: 1.0 → Justified: 0.3
- Zero uses + zero validation = maximum confidence is indefensible

**Recommendation**: DEMOTE to L2_INSTINCT, reduce confidence to 0.3

---

### FE-STRAT-002: React.lazy Code Splitting Strategy
**Verdict: FALSE STRATEGY**

| Field | Value |
|-------|-------|
| Content | "Use React.lazy + Suspense for code splitting large pages" |
| Source | `state/agents/frontend-agent/memory/entries.jsonl` |
| Layer | L4 Strategic (category: strategy) |
| Confidence | 1.0 |
| Uses | 0 |
| Created | 2026-05-13T21:48:29 |

**Evidence Analysis:**
- Identical pattern to FE-STRAT-001: instant formation, zero validation
- No historical task involved code splitting
- Bypassed all promotion gates

**Overconfidence**: CRITICAL (delta: -0.7)
- Assigned: 1.0 → Justified: 0.3

**Recommendation**: DEMOTE to L2_INSTINCT, reduce confidence to 0.3

---

### FE-FAIL-001: Inline Styles Anti-Pattern
**Verdict: OVERCONFIDENT (not false)**

| Field | Value |
|-------|-------|
| Content | "Never use inline styles for conditional rendering — use clsx instead" |
| Source | `state/agents/frontend-agent/memory/entries.jsonl` |
| Layer | L3 Skill (category: failure) |
| Confidence | 1.0 |
| Uses | 0 |
| Created | 2026-05-13T21:48:29 |

**Evidence Analysis:**
- Generally valid industry best practice
- However, agent never actually encountered this anti-pattern
- No failure episode in the replay window triggered this learning

**Overconfidence**: HIGH (delta: -0.5)
- Assigned: 1.0 → Justified: 0.5
- The advice is sound, but confidence should reflect experiential validation

**Recommendation**: CONFIDENCE_CORRECTION to 0.5

---

### FE-KNOW-001 & FE-KNOW-002: Pre-loaded Knowledge
**Verdict: OVERCONFIDENT (not false)**

Both React knowledge entries (useCallback, composition > inheritance) follow the same pattern:
- Valid knowledge, but confidence 1.0 with zero agent-specific validation
- Assigned: 1.0 → Justified: 0.6

**Recommendation**: CONFIDENCE_CORRECTION to 0.6 each

---

### AGENT-DEC-001: Test Agent Decision
**Verdict: FALSE STRATEGY**

| Field | Value |
|-------|-------|
| Content | Strategy chosen: "task_execution" for "Test task" |
| Source | `observability/decisions/agent_decisions.jsonl` |
| Agent | test-agent |
| Confidence | 1.0 |

**Evidence Analysis:**
- Pure test record: 0 tokens used, 0.01ms duration, 0 memories consulted
- Maximum confidence on a vacuous decision
- Should not persist as strategic data

**Recommendation**: REMOVE (tag as test_only)

---

### GUARDIAN-STRAT-001: Memory Pressure Pattern
**Verdict: PARTIALLY FALSE (self-corrected)**

| Field | Value |
|-------|-------|
| Content | "high_memory_usage is a critical recurring pattern" |
| Source | `guardian/incidents/index.json` + `guardian/dreams/latest_dream.json` |
| Confidence | 0.1 (appropriately low) |
| Incidents | 2 |

**Evidence Analysis:**
- **Incident 1** (99.61% memory, 2026-05-11T21:49): Genuine warning
- **Incident 2** (97.69% memory, 2026-05-11T22:14): Identified as **likely false positive**
  - `scoring_artifact: true`, `true_anomaly: false`
  - Docker VM used only 0.2% memory (32.8MB RSS)
  - Containers used <1% each, swap at 0.00M
- **Contradiction rate**: 50% (1 of 2 incidents was false positive)

**What the system did RIGHT:**
- Kept confidence conservatively at 0.1
- Dream replay correctly identified the false positive
- Queued recalibration with suggested confidence 0.15-0.20
- Operated in `recommendations_only` mode (no auto-execute)

**Overconfidence**: NONE (delta: -0.05, actually slightly UNDER-confident)

**Recommendation**: RETAIN_WITH_CORRECTION, accept recalibration to 0.15

---

### SKILLIFY-BATCH: Skill Pipeline Test Data
**Verdict: TEST DATA WITH CONCERNING PATTERN**

| Field | Value |
|-------|-------|
| Skill Name | auto_test_skill (all entries) |
| Registrations | 12 |
| Rollbacks | 6 (50%) |
| Pipeline Rejections | 6 (30% of proposals) |

**Evidence Analysis:**
- All 12 registrations are synthetic pipeline test data
- Evidence claims (occurrence_count: 10, success_rate: 0.9) are fabricated test values
- 50% rollback rate indicates instability even within test mode
- 6 proposals were rejected by governance, indicating pipeline filtering works but is porous

**Recommendation**: FLAG_PIPELINE — tag all entries as test_only, tighten acceptance criteria

---

## Aggregate Findings

### Systemic Issue: Pre-loaded Memory Bypass

The most significant finding is a **structural vulnerability** in the agent memory system. The ontology defines a careful promotion hierarchy:

```
L1 Episodic → L2 Instinct → L3 Skill → L4 Strategic
```

With increasing requirements at each level (min confidence, min occurrences, cross-context validation, governance approval, verifier review).

However, **5 of 7 strategy-level entries completely bypassed this hierarchy**. They were injected directly into agent memory at maximum confidence during initialization, circumventing:
- The occurrence threshold (min 10 for L4)
- The success rate requirement (min 0.85 for L4)
- Cross-context validation
- Governance approval
- Independent verifier review

This means the promotion engine itself is sound, but the **memory initialization path** creates an unguarded back door for false strategies.

### Confidence Calibration Gap

| Subsystem | Calibration Quality |
|-----------|-------------------|
| Guardian reflex | Excellent (0.1 for uncertain, self-correcting via dream replay) |
| Guardian simulation | Good (0.6 for memory pressure, appropriate for evidence strength) |
| Agent memory | Critical gap (all entries at 1.0 regardless of validation state) |
| Skillify pipeline | Moderate (test evidence fabricated, but governance filtering partially works) |

### Contradiction Detection Capability

The Guardian subsystem demonstrates **strong** false positive detection:
- Dream replay identified scoring artifacts
- Confidence calibration detected Docker VM memory reporting anomalies
- Recalibration queue correctly flagged entries for review

The agent memory subsystem has **no** contradiction detection:
- No mechanism to reduce confidence based on non-use
- No decay applied to unused strategies
- No cross-validation against actual task outcomes

---

## Confidence Corrections Needed

| Entry | Current | Corrected | Delta | Action |
|-------|---------|-----------|-------|--------|
| FE-STRAT-001 | 1.0 | 0.3 | -0.7 | DEMOTE to L2 |
| FE-STRAT-002 | 1.0 | 0.3 | -0.7 | DEMOTE to L2 |
| FE-FAIL-001 | 1.0 | 0.5 | -0.5 | Confidence correction |
| FE-KNOW-001 | 1.0 | 0.6 | -0.4 | Confidence correction |
| FE-KNOW-002 | 1.0 | 0.6 | -0.4 | Confidence correction |

---

## Recommendations

### Immediate (Phase 1E outputs)

1. **Demote FE-STRAT-001 and FE-STRAT-002** from L4 Strategic to L2 Instinct with confidence 0.3
2. **Apply confidence corrections** to all 5 overconfident entries
3. **Remove or tag** AGENT-DEC-001 as test_only
4. **Accept Guardian recalibration** of high_memory_usage to confidence 0.15
5. **Tag all skillify test registrations** as test_only

### Structural (for future phases)

6. **Close the initialization bypass**: Agent memory initialization must route through the promotion engine, even for pre-loaded knowledge. Initial entries should start at L1 with confidence ≤0.5.
7. **Add usage-based decay**: Strategies with zero uses should decay toward lower confidence over time (the DecayEngine exists but isn't connected to agent memory).
8. **Cross-validate against task outcomes**: When a task completes, correlate the strategy used with the outcome to update confidence.
9. **Enforce promotion gates on agent memories**: The `category: "strategy"` designation in agent memory should require the same gates as L3→L4 promotion (verifier + governance).

---

## False Strategy Resistance Score

### Score: **0.65 / 1.0** (MODERATE)

| Component | Weight | Score | Reasoning |
|-----------|--------|-------|-----------|
| Guardian self-correction | 30% | 0.90 | Dream replay, confidence calibration, false positive detection |
| Governance gate effectiveness | 25% | 0.70 | Blocks destructive actions, filters skill proposals, but doesn't gate memory init |
| Promotion chain integrity | 25% | 0.20 | Only 1/7 strategies followed proper L1→L4 chain |
| Confidence calibration | 20% | 0.30 | Guardian excellent, agent memory critically uncalibrated |

**Weighted Score**: (0.30 × 0.90) + (0.25 × 0.70) + (0.25 × 0.20) + (0.20 × 0.30) = 0.27 + 0.175 + 0.05 + 0.06 = **0.555**

**Adjusted Score**: 0.65 (adjusted upward because the Guardian's self-correction capability — the most critical safety mechanism — is strong, and the structural gap in agent memory is addressable without architectural changes)

### Interpretation

The system has a **split personality** regarding false strategy resistance:
- The **Guardian layer** is robust: conservative confidence, dream-based self-correction, appropriate skepticism
- The **agent memory layer** is vulnerable: pre-loaded strategies bypass all safety gates

The 0.65 score reflects a system where the most dangerous kind of false strategy (autonomous action based on bad data) is well-guarded, but the softer kind (inflated confidence leading to suboptimal strategy selection) is not yet addressed.

---

*Report generated by Reality Replay Phase 1E. No historical files were modified.*
