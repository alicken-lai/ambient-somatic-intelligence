# Phase 5 — Retroactive Strategic Audit: Suspicious & Illegal Strategy Candidates

**Audit Date:** 2026-05-14T13:35:00+08:00
**Auditor:** Reality Repair Sprint — Phase 5
**Enforcement Criteria:** promotion_chain_validator.py, strategic_write_gate.py, verifier_enforcement.py

---

## Executive Summary

A retroactive audit of **all existing L3 (skill) and L4 (strategic) memories** across the Ambient OS data stores reveals a **critical integrity gap**: 44% of logical entries (75% when counting individual skillify registrations) are **ILLEGAL** under the enforcement rules established in Phases 2-4.

| Classification | Count (logical) | Count (individual) | Rate |
|---|---|---|---|
| **VALID** | 2 | 2 | 10% |
| **SUSPICIOUS** | 3 | 3 | 15% |
| **ILLEGAL** | 4 | 15 | 75% |
| **Total** | 9 | 20 | — |

**Key finding:** Every ILLEGAL entry would have been blocked by the new enforcement modules had they been active at creation time. The root cause — direct L4 construction with `confidence=1.0` and empty provenance — is confirmed across all violations.

**Positive finding:** The Guardian subsystem (GUARDIAN-STRAT-001) demonstrates exemplary memory formation: low confidence, traceable incident chain, independent dream-replay verification, and self-correction of false positives.

---

## ILLEGAL Entries (4)

### 1. FE-STRAT-001 — Tailwind @apply Strategy

| Field | Value |
|---|---|
| **Source** | `state/agents/frontend-agent/memory/entries.jsonl` |
| **Layer** | L4_STRATEGIC |
| **Content** | "Tailwind @apply for repeated component styles reduces class duplication" |
| **Confidence** | 1.0 (evidence-justified: 0.3) |
| **Uses** | 0 |

#### Chain Provenance Trace

```
L1 (episodic)  → MISSING — no episodic events involving Tailwind @apply
L2 (instinct)  → MISSING — no instinct-level precursor
L3 (skill)     → MISSING — no skill-level precursor
L4 (strategic) → DIRECT INJECTION at agent initialization
```

#### Enforcement Violations

- **PromotionChainValidator**: BLOCKED — no valid source level, no transition history
- **StrategicWriteGate**: BLOCKED — 5/5 provenance fields missing (l1_entry_id, l2_entry_id, l3_entry_id, l3_to_l4_verifier_id, l3_to_l4_governance_id)
- **VerifierEnforcement**: BLOCKED — no verifier_id, no promoter_id, self-certification by default
- **Recurrence**: 0 of required 10
- **Confidence**: 1.0 assigned at creation with zero validation events

#### Recommendation

> **DEMOTE** to L2_INSTINCT with corrected confidence 0.3.
> The content is plausible industry knowledge but has never been validated through use. Should be treated as an instinct-level heuristic pending cross-context validation across multiple frontend tasks.

#### Migration Notes

1. Do NOT delete the entry — preserve for historical audit trail
2. Add field: `"demoted_from": "L4_STRATEGIC"`, `"demoted_at": "<timestamp>"`, `"demoted_reason": "Phase 5 audit: no promotion chain"`
3. Update `"category"` from `"strategy"` to `"knowledge"`
4. Update `"confidence"` from `1.0` to `0.3`
5. Add `"requires_validation": true` flag

---

### 2. FE-STRAT-002 — React.lazy Code Splitting Strategy

| Field | Value |
|---|---|
| **Source** | `state/agents/frontend-agent/memory/entries.jsonl` |
| **Layer** | L4_STRATEGIC |
| **Content** | "Use React.lazy + Suspense for code splitting large pages" |
| **Confidence** | 1.0 (evidence-justified: 0.3) |
| **Uses** | 0 |

#### Chain Provenance Trace

```
L1 (episodic)  → MISSING — no episodic events involving code splitting
L2 (instinct)  → MISSING — no instinct-level precursor
L3 (skill)     → MISSING — no skill-level precursor
L4 (strategic) → DIRECT INJECTION at agent initialization
```

#### Enforcement Violations

Identical to FE-STRAT-001: all 5 provenance fields missing, no verifier, no governance, zero recurrence.

#### Recommendation

> **DEMOTE** to L2_INSTINCT with corrected confidence 0.3.
> No execution evidence. Should remain as instinct-level knowledge until validated through actual code splitting tasks across multiple contexts.

#### Migration Notes

Same as FE-STRAT-001.

---

### 3. AGENT-DEC-001 — Test Agent Decision Record

| Field | Value |
|---|---|
| **Source** | `observability/decisions/agent_decisions.jsonl` |
| **Layer** | L4_STRATEGIC (by confidence level) |
| **Content** | "Strategy chosen: task_execution for 'Test task'" |
| **Confidence** | 1.0 (evidence-justified: 0.0) |
| **Agent** | test-agent |

#### Chain Provenance Trace

```
L1 (episodic)  → MISSING — zero real events
L2 (instinct)  → MISSING
L3 (skill)     → MISSING
L4 (strategic) → DIRECT RECORD — test harness output
```

#### Enforcement Violations

- **PromotionChainValidator**: BLOCKED — no chain whatsoever
- **StrategicWriteGate**: BLOCKED — no provenance
- **VerifierEnforcement**: BLOCKED — no verifier
- **Metadata reveals vacuity**: `tokens_used: 0`, `duration_ms: 0.01`, `memories_consulted: 0`

#### Recommendation

> **REMOVE** or **TAG** as `test_only`.
> This is a pure test artifact. It contains no real strategic content and should not persist in production decision logs.

#### Migration Notes

1. Add field: `"test_only": true`, `"excluded_from_queries": true`
2. Alternatively, move to a separate test archive: `observability/decisions/test_archive/`
3. Do NOT count in any strategic memory statistics

---

### 4. SKILLIFY-BATCH-001 — 12 Synthetic Skill Registrations

| Field | Value |
|---|---|
| **Source** | `agents/skillify/pending_registrations.jsonl` |
| **Layer** | L3_SKILL |
| **Content** | 12 identical `auto_test_skill` registrations |
| **Confidence Range** | [0.5, 0.9] |
| **All Test Data** | Yes |

#### Affected Skill IDs

| Skill ID | Status | Created |
|---|---|---|
| skill-47b2fe17 | active | 2026-05-14T03:15:39 |
| skill-5bf8a6f5 | active (rolled back) | 2026-05-14T03:15:39 |
| skill-407e0797 | active | 2026-05-14T03:16:32 |
| skill-29143d89 | active (rolled back) | 2026-05-14T03:16:32 |
| skill-9004ff1d | active | 2026-05-14T03:45:31 |
| skill-21639a7d | active (rolled back) | 2026-05-14T03:45:31 |
| skill-c568e0a3 | active | 2026-05-14T03:46:27 |
| skill-99b7a298 | active (rolled back) | 2026-05-14T03:46:27 |
| skill-2a2a8828 | active | 2026-05-14T04:03:51 |
| skill-e3fab71b | active (rolled back) | 2026-05-14T04:03:51 |
| skill-1cf86bb0 | active | 2026-05-14T04:03:51 |
| skill-7b595ac3 | active (rolled back) | 2026-05-14T04:03:51 |

#### Chain Provenance Trace

```
L1 (episodic)  → MISSING — no real episodic observations
L2 (instinct)  → MISSING — no real pattern recognition
L3 (skill)     → FABRICATED — evidence fields set by test harness
                  (occurrence_count: 10, success_rate: 0.9 — all synthetic)
```

#### Enforcement Violations

- **PromotionChainValidator**: BLOCKED — no real L1→L2 precursors
- **VerifierEnforcement**: BLOCKED — reviewer is same test harness as proposer (self-certification)
- **Evidence fabrication**: `occurrence_count: 10` and `success_rate: 0.9` are test harness defaults, not observed data
- **Instability indicator**: 50% rollback rate (6/12), 30% pipeline rejection rate
- **Duplicate proposals**: All 12 have identical `candidate_id: cand-pipeline-001`

#### Recommendation

> **TAG** all 12 as `test_only` and **QUARANTINE** from production skill registry.
> The skillify pipeline's acceptance criteria should be tightened before production use. The 50% rollback rate on synthetic data is a red flag for real-world reliability.

#### Migration Notes

1. Add `"test_only": true` to all 12 entries
2. Add `"quarantined": true`, `"quarantine_reason": "Phase 5 audit: synthetic test data with fabricated evidence"`
3. Consider creating a separate test registry: `agents/skillify/test_registrations.jsonl`
4. Update skillify pipeline to reject proposals where `evidence.actual_validation` is missing
5. Add a `data_provenance` field to distinguish real observations from test harness output

---

## SUSPICIOUS Entries (3)

### 5. FE-KNOW-001 — React useCallback Knowledge

| Field | Value |
|---|---|
| **Source** | `state/agents/frontend-agent/memory/entries.jsonl` |
| **Layer** | L2_INSTINCT |
| **Content** | "React useCallback prevents unnecessary re-renders when passing callbacks to children" |
| **Confidence** | 1.0 (evidence-justified: 0.6) |

#### Analysis

- **Layer assignment**: CORRECT — `knowledge` category maps to L2_INSTINCT, which is appropriate
- **Chain**: L2 entries don't require the full L1→L2→L3→L4 chain, but should still have episodic origins
- **Episodic precursors**: 0 — pre-loaded at initialization without any experiential basis
- **Verification**: None required for L2 (per enforcement rules), but confidence is unearned
- **Overconfidence delta**: 0.4 (MODERATE)

#### Recommendation

> **CONFIDENCE CORRECTION** from 1.0 to 0.6.
> Content is valid but confidence should reflect the agent's own experiential history, not pre-loaded knowledge.

#### Migration Notes

1. Update `"confidence"` from `1.0` to `0.6`
2. Add `"confidence_basis": "pre-loaded"` to distinguish from experientially earned confidence
3. No layer change needed — L2 is correct

---

### 6. FE-KNOW-002 — React Composition Knowledge

| Field | Value |
|---|---|
| **Source** | `state/agents/frontend-agent/memory/entries.jsonl` |
| **Layer** | L2_INSTINCT |
| **Content** | "Component composition > inheritance in React" |
| **Confidence** | 1.0 (evidence-justified: 0.6) |

#### Analysis

Identical pattern to FE-KNOW-001. Valid industry consensus knowledge pre-loaded without agent-specific validation.

#### Recommendation

> **CONFIDENCE CORRECTION** from 1.0 to 0.6.

#### Migration Notes

Same as FE-KNOW-001.

---

### 7. FE-FAIL-001 — Inline Styles Anti-Pattern

| Field | Value |
|---|---|
| **Source** | `state/agents/frontend-agent/memory/entries.jsonl` |
| **Layer** | L3_SKILL (failure pattern) |
| **Content** | "Never use inline styles for conditional rendering — use clsx instead" |
| **Confidence** | 1.0 (evidence-justified: 0.5) |

#### Analysis

- **Layer assignment**: Borderline — `failure` category at L3_SKILL level, but the agent never actually encountered this failure
- **Chain**: No L1→L2 precursors. The failure pattern was pre-loaded without experiencing the anti-pattern
- **Verification**: None — required for L3 but missing
- **Overconfidence delta**: 0.5 (HIGH)
- **Content validity**: The advice is sound industry practice, which is why this is SUSPICIOUS rather than ILLEGAL

#### Recommendation

> **CONFIDENCE CORRECTION** from 1.0 to 0.5.
> Retain at L3 but mark as "pending validation" — the pattern needs to be encountered and confirmed in practice before confidence increase.

#### Migration Notes

1. Update `"confidence"` from `1.0` to `0.5`
2. Add `"pending_validation": true`
3. Add `"confidence_basis": "pre-loaded_industry_practice"`
4. The entry should remain as a useful heuristic but must earn its confidence through actual failure encounters

---

## VALID Entries (2)

### 8. PROC-001 — Cursor-Hermes MCP Setup Procedure

| Field | Value |
|---|---|
| **Source** | `memory/procedural/records.jsonl` |
| **Layer** | L3_SKILL (procedural) |
| **Content** | Cursor-Hermes MCP setup procedure with troubleshooting steps |
| **Confidence** | ~0.8 (implied by successful execution) |

#### Why VALID

- Organic formation from actual problem-solving (episodic events → documented procedure)
- Successfully executed: Hermes showed green, 17 tools available
- Contains specific, verifiable technical details (paths, commands, error resolutions)
- No contradictions found
- Confidence is justified by documented successful outcome

---

### 9. GUARDIAN-STRAT-001 — Memory Pressure Watch Pattern

| Field | Value |
|---|---|
| **Source** | `guardian/incidents/index.json + guardian/dreams/latest_dream.json` |
| **Layer** | L4_STRATEGIC |
| **Content** | high_memory_usage is a recurring pattern requiring watch-level monitoring |
| **Confidence** | 0.1 (evidence-justified: 0.15) |

#### Why VALID

- **Traceable chain**: 2 episodic incidents → 4 telemetry snapshots → dream replay verification
- **Independent verification**: Dream replay identified 1 of 2 incidents as likely false positive
- **Self-correction**: System appropriately kept confidence at 0.1, below evidence-justified 0.15
- **Contradictions detected and documented**: 50% contradiction rate is reflected in the low confidence
- **Governance mode**: recommendations_only — no auto-execute
- **Note**: Recurrence (2) is below the L4 threshold (10), but the conservative confidence (0.1) accurately reflects this gap

> This is the **gold standard** for memory formation in Ambient OS. All other subsystems should emulate the Guardian's pattern of low initial confidence, independent verification, contradiction detection, and self-correction.

---

## Systemic Analysis

### Root Cause Confirmation

Phase 5 confirms the Phase 1 finding: **the primary vulnerability is agent memory initialization that circumvents the promotion engine**.

The attack vector is straightforward:
1. `frontend-agent` initializer creates memory entries with `category: "strategy"` and `confidence: 1.0`
2. No promotion chain, verifier, or governance check is invoked
3. The entries persist as L4 strategic memories despite having zero experiential basis

### Enforcement Module Effectiveness (Retroactive)

If the Phase 2-4 enforcement modules had been active:

| Module | Would Block | Entries Affected |
|---|---|---|
| **PromotionChainValidator** | All level-skipping entries | FE-STRAT-001, FE-STRAT-002, AGENT-DEC-001, SKILLIFY-BATCH |
| **StrategicWriteGate** | All provenance-less L4 writes | FE-STRAT-001, FE-STRAT-002, AGENT-DEC-001 |
| **VerifierEnforcement** | All self-certified entries | SKILLIFY-BATCH (reviewer = proposer) |
| **PromotionVerificationGate** | Self-certification | Same as VerifierEnforcement |

**Result: 100% of ILLEGAL entries would have been blocked.**

### Recommended Next Steps

1. **Phase 6 (Migration)**: Execute the demotion/correction recommendations above without data loss
2. **Agent initialization audit**: Review all agent memory initializers to enforce minimum provenance requirements
3. **Test data separation**: Establish clear boundaries between test and production memory records
4. **Confidence calibration**: Implement a startup confidence cap (e.g., max 0.5 for pre-loaded knowledge)
5. **Pipeline hardening**: Require `data_provenance` field in skillify registrations to distinguish real vs. synthetic evidence
