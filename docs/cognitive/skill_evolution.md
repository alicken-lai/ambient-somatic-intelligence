# Skill Evolution Pipeline

> Ambient OS v0.3.1-alpha — Knowledge Promotion Across Cognitive Layers

---

## 1. Purpose

This document defines the complete pipeline through which raw experience (L1)
evolves into reusable instincts (L2), structured skills (L3), and ultimately
strategic principles (L4). Each transition is governed, auditable, and
reversible. The pipeline embodies the core Ambient OS philosophy: the system
becomes smarter through disciplined promotion, not through accumulation.

---

## 2. Pipeline Overview

```
L1 (Episodic)                    L2 (Instinct)
┌──────────────┐                ┌──────────────┐
│ Raw sessions │  ──Distill──▶  │ Atomic rules │
│ Logs         │                │ Trigger conds│
│ Sensor events│                │ Confidence   │
│ Traces       │                │ scored       │
└──────────────┘                └──────┬───────┘
                                       │
                                   Promote
                                       │
                                       ▼
L3 (Skill)                      L4 (Strategic)
┌──────────────┐                ┌──────────────┐
│ Clustered    │  ──Abstract──▶ │ Decision     │
│ workflows    │                │ heuristics   │
│ Typed schema │                │ Routing      │
│ Governed     │                │ philosophies │
└──────────────┘                └──────────────┘
```

---

## 3. L1 → L2: Observe → Detect → Generate Instinct Candidate

### 3.1 Observation (L1 Capture)

The `WorkflowObserver` (`agents/skillify/workflow_observer.py`) captures raw
workflow events as they occur:

- Each event records: `workflow_id`, `step_name`, `tool_used`, `parameters`,
  `result`, `duration_ms`, `success`, `timestamp`, `session_id`, `context`
- Events are persisted to `observations.jsonl` (append-only)
- No filtering or judgment occurs at this stage—all events are captured

### 3.2 Pattern Detection (L1 → L2 Candidate)

The `SkillifyPatternMiner` (`agents/skillify/pattern_miner.py`) analyzes
accumulated observations to detect recurring patterns:

- **Minimum support**: Configurable threshold (`min_support`) — a pattern must
  appear at least this many times to be considered
- **Variation scoring**: `0.6 × sequence_similarity + 0.4 × duration_similarity`
- **Output**: `WorkflowPattern` objects containing the pattern template,
  occurrence count, success rate, and context metadata

### 3.3 Instinct Candidate Generation

When a pattern meets the minimum support threshold and demonstrates cross-session
stability, it becomes an instinct candidate:

- **Confidence initialization**: Based on occurrence (0.30), success rate (0.35),
  consistency (0.20), and breadth (0.15)
- **Contextual applicability**: Environmental signatures from the somatic
  subsystem constrain where the instinct applies
- **Governance review**: The candidate must be verified before it is accepted
  as a formal L2 instinct

### 3.4 Governance Gate: L1 → L2

| Requirement | Details |
|---|---|
| Minimum occurrences | `min_support` in `SkillifyPatternMiner` |
| Success rate | Must demonstrate positive outcomes |
| Environmental stability | Pattern must hold across relevant environmental bands |
| Cross-session validation | Pattern must appear in multiple independent sessions |
| Verification confidence | ≥ 0.60 (per Verification Doctrine) |

**Reference**: [`observation_to_instinct.md`](../../agents/skillify/doctrine/observation_to_instinct.md)

---

## 4. L2 → L3: Validate → Cluster → Register Skill

### 4.1 Clustering (L2 → L3 Candidate)

The `WorkflowCluster` (`agents/skillify/workflow_cluster.py`) groups related
instincts into coherent skill candidates:

- **Similarity metric**: `0.5 × step_similarity + 0.3 × schema_similarity + 0.2 × governance_similarity`
- **Skill potential scoring**: `0.30 × occurrence + 0.35 × success + 0.20 × consistency + 0.15 × breadth`
- **Output**: `WorkflowClusterGroup` objects containing clustered patterns,
  aggregate metrics, and a `skill_potential` score

### 4.2 Candidate Generation

The `SkillCandidateGenerator` (`agents/skillify/skill_candidate_generator.py`)
transforms validated clusters into formal skill candidates:

- Generates `SkillCandidate` objects with: name, description, steps,
  governance level, estimated success rate, supporting evidence
- Assigns governance classification: `ALLOW`, `REVIEW_REQUIRED`, or `BLOCK`
- Persists candidates to `candidates.jsonl`

### 4.3 Candidate Validation

The `SkillCandidateValidator` (`agents/skillify/skill_candidate_validator.py`)
applies rigorous validation criteria:

| Criterion | Threshold |
|---|---|
| Minimum supporting observations | `min_support = 3` |
| Minimum success rate | `min_success_rate = 0.70` |
| Name uniqueness | `name_similarity < 0.85` against existing skills |

Validation includes simulation-based testing (`simulate()`) to verify that
the candidate skill produces expected outcomes under controlled conditions.

### 4.4 Registration Pipeline

The `SkillRegistrationPipeline` (`agents/skillify/skill_registration_pipeline.py`)
manages the full lifecycle:

```
propose()  →  approve()  →  register()
   │              │              │
   ▼              ▼              ▼
ProposalResult  ApprovalResult  RegistrationResult
   │              │              │
   │   Reviewer   │   Skill      │
   │   identity   │   Registry   │
   │   required   │   updated    │
   │              │              │
   └──── Rollback path preserved via rollback() ────┘
```

**Critical constraints**:
- `approve()` requires a `reviewer` parameter — the implementer must not
  approve its own work (see [`verification_doctrine.md`](./verification_doctrine.md))
- No auto-registration: Skillify proposes, governance approves, the pipeline
  registers
- Rollback is always available via `rollback()`

### 4.5 Governance Gate: L2 → L3

| Requirement | Details |
|---|---|
| Constituent confidence | All instincts must have confidence ≥ 0.70 |
| Cluster coherence | Similarity threshold met in `WorkflowCluster` |
| Candidate validation | Passes `SkillCandidateValidator` checks |
| Schema validation | Passes `SkillValidator` structural checks |
| Governance review | `SkillRegistrationPipeline.approve()` by independent reviewer |
| Verification confidence | ≥ 0.70 (per Verification Doctrine) |

**Reference**: [`instinct_to_skill.md`](../../agents/skillify/doctrine/instinct_to_skill.md)

---

## 5. L3 → L4: Abstract → Validate Cross-Project → Adopt Strategy

### 5.1 Abstraction

When a skill demonstrates consistent success across multiple contexts, it
becomes a candidate for strategic abstraction. The abstraction process:

1. Identifies the **invariant principle** underlying the skill's success
2. Strips domain-specific details to produce a context-independent rule
3. Assesses the rule's **predictive power** in untested contexts
4. Formulates the rule in human-readable, auditable language

### 5.2 Cross-Project Validation

The defining requirement for L4 promotion is validation across fundamentally
different contexts:

- Minimum **3 distinct project contexts** (different in at least 2 of:
  language, domain, infrastructure, operational phase)
- Each context must independently confirm the principle's validity
- Evidence must be recorded and traceable to specific L1 events

### 5.3 Governance Gate: L3 → L4

| Requirement | Details |
|---|---|
| Cross-project validation | ≥ 3 distinct project contexts |
| Confidence threshold | All constituent skills must have confidence ≥ 0.90 |
| Independent verifier | Separate from the implementing agent |
| Highest governance gate | `MandatoryGate` + `PolicyEngine` + human notification |
| Reversibility | Confirmed rollback path before finalization |
| Blast radius assessment | Documented impact analysis |
| Verification confidence | ≥ 0.90 (per Verification Doctrine) |

**Reference**: [`skill_to_strategy.md`](../../agents/skillify/doctrine/skill_to_strategy.md)

---

## 6. Skillify's Role: Propose Only

Skillify (`agents/skillify/`) is a discovery engine, not an authority. Its
pipeline follows a strict separation of concerns:

| Stage | Skillify's Action | Authority |
|---|---|---|
| Observe | Captures workflow events | Autonomous |
| Mine | Detects recurring patterns | Autonomous |
| Cluster | Groups related patterns | Autonomous |
| Generate | Creates skill candidates | Autonomous |
| Validate | Checks minimum criteria | Autonomous |
| **Propose** | **Submits for governance review** | **Proposal only** |
| Approve | — | **Governance (independent reviewer)** |
| Register | — | **Pipeline (after approval)** |

Skillify **must never**:
- Auto-register skills without governance review
- Approve its own proposals
- Mutate routing tables, escalation rules, or attention weights
- Bypass the `MandatoryGate` for any operation

This separation ensures that the system's operational behavior changes only
through deliberate, governed, and reversible decisions.

---

## 7. Cross-Reference: Skillify Pipeline Components

| Component | Path | Pipeline Stage |
|---|---|---|
| WorkflowObserver | `agents/skillify/workflow_observer.py` | Observe (L1 capture) |
| SkillifyPatternMiner | `agents/skillify/pattern_miner.py` | Mine (L1 → L2 candidate) |
| WorkflowCluster | `agents/skillify/workflow_cluster.py` | Cluster (L2 → L3 candidate) |
| SkillCandidateGenerator | `agents/skillify/skill_candidate_generator.py` | Generate (L3 candidate) |
| SkillCandidateValidator | `agents/skillify/skill_candidate_validator.py` | Validate (L3 quality gate) |
| SkillRegistrationPipeline | `agents/skillify/skill_registration_pipeline.py` | Propose → Approve → Register |

---

## 8. Related Documents

- [`somatic_metacognition_spec_v1.md`](./somatic_metacognition_spec_v1.md) — Master specification
- [`memory_ontology.md`](./memory_ontology.md) — Formal memory layer definitions
- [`strategic_memory.md`](./strategic_memory.md) — Strategic memory architecture
- [`verification_doctrine.md`](./verification_doctrine.md) — Guardian Verification Doctrine
- [`../../agents/skillify/doctrine/`](../../agents/skillify/doctrine/) — Skillify evolution doctrine (implementation-level)

---

*The skill evolution pipeline is the engine of bounded adaptive cognition.
Each transition gate exists because unverified knowledge is worse than no
knowledge—it consumes resources, biases decisions, and erodes trust. The
pipeline's discipline is what makes the system's growth reliable.*
