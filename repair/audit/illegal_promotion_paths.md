# P1.5 Reality Repair Sprint — Phase 1: Illegal Promotion Path Audit

**Generated**: 2026-05-14T13:30:00+08:00
**Context**: Reality Score 0.6645 (UNSTABLE), False Strategy Resistance 0.65 (needed >0.90)

---

## Executive Summary

7 illegal promotion paths identified across 4 source files. The primary vulnerability is **not in the PromotionEngine** (which correctly enforces single-hop rules), but in:

1. **Direct construction bypasses** — Schema dataclasses allow L3/L4 entries to be created without any promotion chain validation
2. **Level-skip paths in SomaticOntologyBridge** — L2→L4 promotions skip L3 entirely
3. **Missing chain continuity checks** — No mechanism verifies that a promotion candidate has a complete prior-layer history

---

## HIGH Risk Paths (3)

### ILP-001: L2→L4 Skip via `propose_escalation_strategy`

| Field | Value |
|-------|-------|
| File | `memory/somatic/ontology_bridge.py` |
| Function | `SomaticOntologyBridge.propose_escalation_strategy` |
| Transition | L2_INSTINCT → L4_STRATEGIC |
| Lines | 217–246 |

**How it works**: Accepts any precursor pattern with `confidence >= 0.8` and creates a `PromotionCandidate` with `current_layer=2, proposed_layer=4`. No verification that a corresponding L3 skill entry exists.

**Impact**: Allows "instinct-like" precursor patterns to jump directly to strategic status, bypassing the skill validation layer that provides cross-context verification and execution counting.

---

### ILP-002: L2→L4 Batch Skip via `scan_promotion_candidates`

| Field | Value |
|-------|-------|
| File | `memory/somatic/ontology_bridge.py` |
| Function | `SomaticOntologyBridge.scan_promotion_candidates` (precursors loop) |
| Transition | L2_INSTINCT → L4_STRATEGIC |
| Lines | 294–307 |

**How it works**: Same mechanism as ILP-001 but operates in batch mode during full scans. Iterates all precursors and creates L2→L4 candidates at scale.

**Impact**: Amplified version of ILP-001 — during a system-wide promotion scan, multiple precursor patterns could be proposed for L4 simultaneously without L3 intermediary.

---

### ILP-004: Direct L4 Construction via `StrategicEntry`

| Field | Value |
|-------|-------|
| File | `memory/ontology/strategic_schema.py` |
| Function | `StrategicEntry.__init__` / `StrategicEntry.from_dict` |
| Transition | NONE → L4_STRATEGIC |
| Lines | 13–67 |

**How it works**: The dataclass constructor accepts any values with no validation. `source_skills` can be empty, `governance_approval_id` defaults to `""`, `verifier_id` defaults to `""`, and `confidence` can be set to `1.0`.

**Impact**: This is the **root cause** of the P1 findings. Agent memory initialization used this path to inject 5 strategies at confidence 1.0 with zero promotion chain evidence. The entries FE-STRAT-001, FE-STRAT-002, and AGENT-DEC-001 all exploited this structural vulnerability.

---

## MEDIUM Risk Paths (3)

### ILP-003: L1→L3 Skip via `map_cluster_to_l3`

| Field | Value |
|-------|-------|
| File | `memory/somatic/ontology_bridge.py` |
| Function | `SomaticOntologyBridge.map_cluster_to_l3` |
| Transition | L1_EPISODIC → L3_SKILL |
| Lines | 183–215 |

**How it works**: Episode clusters (containing L1 episode IDs) are mapped directly to L3 without verifying that the underlying episodes have been promoted to L2 instincts first.

**Impact**: Raw episodic data can bypass instinct formation and appear as validated skills.

---

### ILP-005: Direct L3 Construction via `SkillMemoryEntry`

| Field | Value |
|-------|-------|
| File | `memory/ontology/skill_schema.py` |
| Function | `SkillMemoryEntry.__init__` / `SkillMemoryEntry.from_dict` |
| Transition | NONE → L3_SKILL |
| Lines | 13–85 |

**How it works**: `source_instincts` field is a plain list with no referential integrity check. Any caller can create an L3 entry with empty or fabricated instinct references.

**Impact**: Enables creation of "skill" entries without proven instinct precursors (as seen with FE-FAIL-001).

---

### ILP-006: Confidence Injection via Skillify Pipeline

| Field | Value |
|-------|-------|
| File | `agents/skillify/skill_registration_pipeline.py` |
| Function | `SkillRegistrationPipeline._try_skill_registry` |
| Transition | NONE → L3_SKILL (via SkillRegistry) |
| Lines | 397–431 |

**How it works**: The pipeline trusts the candidate's self-declared `evidence` dict (occurrence_count, success_rate) without cross-referencing actual episodic records. The SKILLIFY-BATCH test data used fabricated evidence claims.

**Impact**: Skills can be registered with inflated confidence based on synthetic evidence.

---

## LOW Risk Paths (1)

### ILP-007: Missing Chain Continuity in `approve_promotion`

| Field | Value |
|-------|-------|
| File | `memory/ontology/promotion_engine.py` |
| Function | `PromotionEngine.approve_promotion` |
| Transition | Any → Any+1 |
| Lines | 164–243 |

**How it works**: Validates governance_decision_id and verifier_id, but never checks that the referenced `entry_id` actually has a proven promotion chain from prior layers.

**Impact**: Lower risk because the PromotionEngine's `scan_candidates` method already validates layer membership, but a direct caller of `approve_promotion` with a fabricated `PromotionCandidate` could bypass this.

---

## Architectural Root Causes

1. **No write-time enforcement** — The schema dataclasses are pure data carriers with no promotion-chain validation at construction time. Any code path that creates `StrategicEntry` or `SkillMemoryEntry` bypasses all promotion gates.

2. **Bridge allows level skipping** — The SomaticOntologyBridge maps somatic entities to ontology layers using its own rules that don't enforce the sequential L1→L2→L3→L4 chain.

3. **No chain continuity validation** — Even within the PromotionEngine, there's no mechanism to verify that a candidate's claimed source_layer entry has its own valid promotion history.

---

## Recommended Fixes (Phases 2–3)

| Fix | Target |
|-----|--------|
| `PromotionChainValidator` | Enforce sequential transitions, reject level skips |
| `PromotionGuard` | Wrap all promotion operations with chain validation |
| `StrategicWriteGate` | Block any direct L4 write without full chain provenance |
| `PromotionViolation` logging | Record all blocked attempts for audit |

---

*Audit completed. No files were modified. All findings are based on static code analysis.*
