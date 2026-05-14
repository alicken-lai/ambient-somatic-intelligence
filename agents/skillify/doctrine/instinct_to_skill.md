# Instinct to Skill — L2 → L3 Evolution Doctrine

> Ambient OS v0.3.1-alpha — Skillify Evolution Doctrine

---

## 1. Overview

This document defines how validated instincts (L2) are assembled into
structured skills (L3) through the Skillify pipeline. The L2 → L3 transition
is where atomic observations become operational capabilities—reusable,
typed, governed procedures that the system can invoke to accomplish tasks.

A skill is not merely a collection of instincts. It is a **governed,
schema-validated, independently-verified procedure** with typed inputs and
outputs, a governance classification, and a complete audit trail.

---

## 2. Clustering Instincts into Skills

### 2.1 The WorkflowCluster

**Reference**: `agents/skillify/workflow_cluster.py`

The `WorkflowCluster` groups related instincts (validated L2 patterns) into
coherent clusters that may represent a compound operational capability.

### 2.2 Similarity Metric

Clustering uses a weighted similarity metric across three dimensions:

| Dimension | Weight | Description |
|---|---|---|
| Step similarity | 0.50 | Overlap in the sequence of workflow steps |
| Schema similarity | 0.30 | Compatibility of input/output types |
| Governance similarity | 0.20 | Alignment of governance classifications |

Two instincts are clustered together when their composite similarity exceeds
the clustering threshold. The algorithm uses this metric to form
`WorkflowClusterGroup` objects.

### 2.3 Skill Potential Scoring

Each cluster is evaluated for its potential to become a viable skill using
a 4-factor weighted score:

| Factor | Weight | Description |
|---|---|---|
| Occurrence | 0.30 | How frequently the clustered pattern appears |
| Success rate | 0.35 | Proportion of successful executions |
| Consistency | 0.20 | Low variance in execution outcomes |
| Breadth | 0.15 | Number of distinct contexts where the pattern was observed |

```
skill_potential = 0.30 × occurrence + 0.35 × success + 0.20 × consistency + 0.15 × breadth
```

Clusters with a `skill_potential` score above the threshold proceed to
candidate generation.

---

## 3. Candidate Generation

### 3.1 The SkillCandidateGenerator

**Reference**: `agents/skillify/skill_candidate_generator.py`

The `SkillCandidateGenerator` transforms validated clusters into formal
`SkillCandidate` objects suitable for governance review.

### 3.2 Candidate Structure

Each `SkillCandidate` includes:

| Field | Description |
|---|---|
| `name` | Unique identifier for the skill |
| `description` | Human-readable explanation of what the skill does |
| `steps` | Ordered sequence of workflow steps |
| `governance_level` | Classification: `ALLOW`, `REVIEW_REQUIRED`, or `BLOCK` |
| `estimated_success_rate` | Projected success based on constituent instincts |
| `supporting_evidence` | References to the L1 events and L2 instincts that support the candidate |

### 3.3 Governance Level Assignment

The generator assigns governance levels based on the risk profile of the
candidate's constituent operations:

| Level | Criteria |
|---|---|
| `ALLOW` | All constituent steps are low-risk, no external effects |
| `REVIEW_REQUIRED` | At least one step modifies state, accesses external resources, or has non-trivial side effects |
| `BLOCK` | Steps include potentially destructive operations (per AGENTS.md: never execute destructive commands) |

### 3.4 Persistence

Generated candidates are persisted to `candidates.jsonl` for audit trail
purposes and to enable asynchronous governance review.

---

## 4. Candidate Validation

### 4.1 The SkillCandidateValidator

**Reference**: `agents/skillify/skill_candidate_validator.py`

The `SkillCandidateValidator` applies rigorous validation before a candidate
may proceed to the registration pipeline.

### 4.2 Validation Criteria

| Criterion | Threshold | Rationale |
|---|---|---|
| Minimum supporting observations | `min_support = 3` | Ensures the skill is not based on insufficient evidence |
| Minimum success rate | `min_success_rate = 0.70` | Ensures the skill is likely to produce positive outcomes |
| Name uniqueness | `name_similarity < 0.85` | Prevents duplicate or near-duplicate skills in the registry |

### 4.3 Simulation-Based Validation

The validator includes a `simulate()` method that performs simulation-based
testing:

1. Construct a controlled execution environment
2. Execute the candidate skill's step sequence with synthetic inputs
3. Verify outputs match expected patterns from historical data
4. Record `SimulationResult` with pass/fail status and confidence

The `CandidateValidation` result includes both the criteria-based assessment
and the simulation outcome.

### 4.4 Validation Outcomes

| Outcome | Meaning | Next Step |
|---|---|---|
| **Pass** | All criteria met, simulation successful | Proceed to registration pipeline |
| **Conditional pass** | Criteria met but simulation inconclusive | May proceed with reduced confidence |
| **Fail** | One or more criteria not met | Candidate returned for further evidence gathering |

---

## 5. Registration Pipeline

### 5.1 The SkillRegistrationPipeline

**Reference**: `agents/skillify/skill_registration_pipeline.py`

The registration pipeline manages the full lifecycle of skill adoption
through a governed, auditable process.

### 5.2 Pipeline Stages

#### Stage 1: Propose

```python
propose(candidate: SkillCandidate) → ProposalResult
```

Skillify submits a validated candidate for governance review. The
`ProposalResult` records:
- The candidate details
- Proposal timestamp
- Proposer identity
- Initial governance classification

#### Stage 2: Approve

```python
approve(proposal_id: str, reviewer: str) → ApprovalResult
```

An independent reviewer evaluates the proposal and renders an approval
decision. The `ApprovalResult` records:
- Reviewer identity
- Approval decision (approved / rejected / deferred)
- Review rationale
- Approval timestamp

**Critical requirement**: The `reviewer` parameter identifies the approving
entity. Per the Guardian Verification Doctrine:
- The reviewer **must not** be the same agent that proposed the skill
- The reviewer **must** evaluate the proposal against objective criteria
- The review **must** be logged in the governance audit trail

**Known gap**: The current implementation accepts any string as the `reviewer`
parameter without verifying independence. See
`docs/cognitive/verification_doctrine.md` Section 3.1 for details and
remediation plan.

#### Stage 3: Register

```python
register(approval_id: str) → RegistrationResult
```

After approval, the skill is registered in the `SkillRegistry`
(`skills/core/skill_registry.py`). The `RegistrationResult` records:
- Registration timestamp
- Registry location
- Assigned skill ID
- Rollback token

#### Rollback

```python
rollback(registration_id: str) → bool
```

Any registered skill can be rolled back, removing it from the active
registry. Rollback preserves the audit trail—the skill's history remains
in the governance log even after removal.

### 5.3 The Explicit Governance Gate

The registration pipeline enforces a hard governance boundary between
Skillify (the proposer) and the governance system (the approver):

```
Skillify's boundary                 Governance's boundary
┌─────────────────────┐            ┌──────────────────────┐
│ observe             │            │                      │
│ mine                │            │ approve()            │
│ cluster             │  propose   │   ↓                  │
│ generate            │ ────────▶  │ MandatoryGate check  │
│ validate            │            │   ↓                  │
│                     │            │ register()           │
└─────────────────────┘            └──────────────────────┘
```

### 5.4 No Auto-Registration

Skillify is **prohibited** from:
- Calling `approve()` on its own proposals
- Calling `register()` without a prior `approve()` result
- Bypassing the registration pipeline to insert skills directly into `SkillRegistry`
- Modifying the `SkillRouter` routing table without governance approval

This constraint is constitutional—it derives from AGENTS.md ("Ask Guardian
before external action") and the Guardian Verification Doctrine ("The
implementer cannot self-certify").

---

## 6. Post-Registration Lifecycle

Once registered, a skill enters the active lifecycle:

- **Invocation**: The `SkillRouter` (`skills/core/skill_router.py`) may select
  the skill for execution based on tag matching and governance clearance
- **Monitoring**: Execution results are tracked and fed back into confidence
  scoring
- **Success** reinforces confidence and validates the promotion decision
- **Failure** reduces confidence; repeated failures may trigger rollback review
- **Evolution**: Skills with consistently high confidence across multiple
  contexts become candidates for L4 strategic abstraction

---

## 7. Code References

| Component | Path | Role |
|---|---|---|
| WorkflowCluster | `agents/skillify/workflow_cluster.py` | Instinct clustering |
| WorkflowClusterGroup | `agents/skillify/workflow_cluster.py` | Cluster data model |
| SkillCandidateGenerator | `agents/skillify/skill_candidate_generator.py` | Candidate creation |
| SkillCandidate | `agents/skillify/skill_candidate_generator.py` | Candidate data model |
| SkillCandidateValidator | `agents/skillify/skill_candidate_validator.py` | Candidate validation |
| CandidateValidation | `agents/skillify/skill_candidate_validator.py` | Validation result model |
| SimulationResult | `agents/skillify/skill_candidate_validator.py` | Simulation outcome model |
| SkillRegistrationPipeline | `agents/skillify/skill_registration_pipeline.py` | Registration lifecycle |
| ProposalResult | `agents/skillify/skill_registration_pipeline.py` | Proposal outcome model |
| ApprovalResult | `agents/skillify/skill_registration_pipeline.py` | Approval outcome model |
| RegistrationResult | `agents/skillify/skill_registration_pipeline.py` | Registration outcome model |
| SkillRegistry | `skills/core/skill_registry.py` | Skill storage and lookup |
| SkillRouter | `skills/core/skill_router.py` | Skill selection and routing |
| SkillValidator | `skills/core/skill_validator.py` | Schema and execution validation |
| MandatoryGate | `governance/mandatory_gate.py` | Governance entry point |

---

## 8. Related Documents

- [`observation_to_instinct.md`](./observation_to_instinct.md) — L1 → L2 evolution
- [`skill_to_strategy.md`](./skill_to_strategy.md) — L3 → L4 evolution
- [`docs/cognitive/skill_evolution.md`](../../../docs/cognitive/skill_evolution.md) — Full pipeline overview
- [`docs/cognitive/verification_doctrine.md`](../../../docs/cognitive/verification_doctrine.md) — Verification requirements
- [`docs/cognitive/memory_ontology.md`](../../../docs/cognitive/memory_ontology.md) — Memory layer definitions

---

*The L2 → L3 transition is where knowledge becomes capability. The governance
gate at this boundary is not bureaucracy—it is the mechanism that prevents a
pattern-matching system from autonomously modifying its own operational
behavior. Without this gate, a confident-but-wrong pattern could propagate
into the skill registry and affect real operations. The gate is the price of
reliability.*
