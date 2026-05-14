# Skill to Strategy — L3 → L4 Evolution Doctrine

> Ambient OS v0.3.1-alpha — Skillify Evolution Doctrine

---

## 1. Overview

This document defines how successful skills (L3) may be abstracted into
strategic rules (L4)—the highest layer of the Ambient OS cognitive hierarchy.
Strategic rules influence system-wide behavior: routing philosophies,
escalation principles, attention allocation, and metacognitive feedback loops.

**This is the FUTURE pathway.** The L3 → L4 promotion is aspirational in the
current release. The foundational infrastructure is being built in parallel
(see `memory/ontology/promotion_engine.py`). This document defines the
target architecture and constraints that the implementation must satisfy.

---

## 2. What L3 → L4 Abstraction Means

A skill operates in a specific domain with typed inputs and outputs. A
strategic rule operates across all domains as an abstract principle. The
L3 → L4 transition strips away domain-specific details and extracts the
invariant insight.

### Example

| Layer | Content |
|---|---|
| L3 Skill (React) | "When rendering a list with >100 items, use virtualization to maintain 60fps" |
| L3 Skill (Python) | "When processing a dataset with >10K records, use streaming to avoid memory exhaustion" |
| L3 Skill (Go) | "When handling >1K concurrent connections, use connection pooling to prevent file descriptor exhaustion" |
| **L4 Strategy** | **"When a resource-consuming operation scales linearly with input size, introduce a bounded-resource pattern (virtualization, streaming, pooling) before the input size reaches the resource ceiling. The specific pattern should match the resource type (rendering budget, memory, file descriptors)."** |

The strategic rule is:
- **Domain-independent**: Applies to frontend, backend, and infrastructure
- **Composable**: Can be applied to novel contexts not yet encountered
- **Predictive**: Correctly anticipates the right approach for new situations
- **Falsifiable**: Could be disproven by evidence of a domain where linear
  scaling is acceptable

---

## 3. Criteria for Strategy Promotion

### 3.1 Consistent Success Across Multiple Contexts

The candidate rule must be derived from skills that have demonstrated
consistent success. "Consistent" means:

- Success rate ≥ 0.90 across all constituent skills
- No unexplained failures in the most recent evaluation window
- Stable performance across different environmental signatures
  (CPU load, memory pressure, process count)

### 3.2 Cross-Project Validation

The defining requirement for L4 promotion. The candidate must have been
validated in at least **3 distinct project contexts**, where "distinct" means
different in at least two of:

| Dimension | Examples |
|---|---|
| Programming language | React/TypeScript, Python, Go, Rust |
| Domain | Frontend UI, backend API, data pipeline, infrastructure |
| Infrastructure environment | Local development, staging, production, containerized |
| Operational phase | Development, deployment, monitoring, incident response |

Each project context must independently confirm that the abstracted principle
produces correct outcomes.

### 3.3 Verifier Approval

Per the Guardian Verification Doctrine (`docs/cognitive/verification_doctrine.md`):

- An independent verifier must approve the promotion
- The verifier must be separate from the agent that proposed the abstraction
- Verification confidence must be ≥ 0.90 (the highest threshold)
- The verifier must assess domain independence, predictive power, and
  falsifiability

### 3.4 High Confidence Threshold

All constituent L3 skills must carry confidence ≥ 0.90. The candidate
strategic rule itself must have projected confidence ≥ 0.90 based on:

- Track record of constituent skills
- Cross-project validation evidence
- Verifier assessment
- Absence of contradicting evidence

---

## 4. Strategy Storage Format

Strategic rules are stored with the following structure:

| Field | Type | Description |
|---|---|---|
| `rule_id` | str | Unique identifier |
| `statement` | str | Human-readable rule statement |
| `domain` | str | "universal" or a constrained domain scope |
| `confidence` | float | Current confidence score (0.0 – 1.0) |
| `version` | int | Monotonically increasing version number |
| `constituent_skills` | list[str] | Skill IDs that were abstracted into this rule |
| `evidence_chain` | list[dict] | Cross-project validation records |
| `verifier_id` | str | Identity of the approving verifier |
| `verification_confidence` | float | Verifier's confidence assessment |
| `promotion_timestamp` | str | ISO 8601 timestamp of promotion |
| `rationale` | str | Human-readable explanation of why this rule was promoted |
| `preconditions` | list[str] | Conditions under which the rule applies |
| `failure_modes` | list[str] | Known situations where the rule may not hold |
| `rollback_token` | str | Token for reverting the promotion |

Strategic rules are stored in the `governance` storage layer (TTL 365d) with
archival copies in the `archive` layer (TTL 3650d).

---

## 5. Governance Requirements for L4 Promotion

L4 promotion requires the **highest governance level** in the system. This
reflects the outsized impact of strategic rules on system-wide behavior.

### 5.1 MandatoryGate Pipeline

All L4 promotions must pass through `MandatoryGate`
(`governance/mandatory_gate.py`), which executes:

1. **PolicyEngine evaluation**: All applicable policies are checked, with
   L4 operations classified at the highest priority level
2. **AnomalyDetector scan**: Verify no anomalous patterns in the promotion
   request (e.g., sudden batch promotion of many rules)
3. **ToolPermissionMatrix check**: Verify the promoting agent has the
   required role permissions
4. **Audit logging**: Full decision chain recorded in
   `governance/audit/decisions.jsonl`

### 5.2 ExecutionValidator 4-Stage Check

The `ExecutionValidator` (`governance/execution_validator.py`) runs its
complete pipeline:

1. **Policy check**: Does the promotion comply with all governance policies?
2. **Anomaly check**: Is the promotion request itself anomalous?
3. **Resource protection**: Does the new rule risk resource exhaustion
   (e.g., by redirecting too much attention budget)?
4. **Injection detection**: Is the rule's statement free of adversarial
   content?

### 5.3 Human Notification

L4 promotions trigger mandatory escalation via the `EscalationRouter`
(`attention/escalation_router.py`). The salience of an L4 promotion event
exceeds the `ESCALATE` threshold (0.75), ensuring human operators are notified
even if automatic approval criteria are met.

### 5.4 Reversibility Requirement

Before any L4 promotion is finalized:

1. A rollback token must be generated
2. The blast radius must be assessed (which subsystems reference the rule?)
3. A rollback procedure must be documented
4. The system must confirm that no irreversible downstream effects will
   occur upon rollback

---

## 6. Impact on System Behavior

Strategic rules influence the following subsystems:

### 6.1 Attention System

- `SalienceEngine` (`attention/salience_engine.py`): Strategic rules may
  adjust the 9-factor salience weights (novelty, anomaly, recurrence,
  historical, governance, somatic, memory, operator, temporal_decay)
- `PriorityAllocator` (`attention/priority_allocator.py`): Strategic rules
  may adjust domain budget allocation (somatic 0.30, governance 0.25,
  task 0.20, memory 0.15, external 0.10)
- `EscalationRouter` (`attention/escalation_router.py`): Strategic rules may
  adjust escalation thresholds (attend 0.30, escalate 0.75, throttle limit 15,
  ignore 0.10)

### 6.2 Governance System

- `PolicyEngine` (`governance/policy_engine.py`): Strategic rules may
  introduce new policies or adjust policy priorities
- `MandatoryGate` (`governance/mandatory_gate.py`): Strategic rules may
  influence how the gate evaluates certain categories of actions

### 6.3 Skill Routing

- `SkillRouter` (`skills/core/skill_router.py`): Strategic rules may
  influence skill selection criteria, fallback chain behavior, or governance
  clearance requirements

### 6.4 Memory System

- `MemoryKernel` (`memory/memory_kernel.py`): Strategic rules may adjust
  scoring weights, decay parameters, or deduplication thresholds

---

## 7. Implementation Status

### 7.1 What Exists

- The conceptual framework is defined (this document)
- The L1 → L2 and L2 → L3 pipelines are implemented and operational
- The governance infrastructure (`MandatoryGate`, `ExecutionValidator`,
  `PolicyEngine`, `GovernanceAuditLog`) is in place
- The attention system's adjustable thresholds are ready to receive
  strategic directives

### 7.2 What Is Being Built

- `memory/ontology/promotion_engine.py` — The promotion engine that will
  manage L3 → L4 transitions programmatically. This is being built in
  parallel by another workstream.

### 7.3 What Is Not Yet Built

- Cross-project validation infrastructure (mechanism for sharing evidence
  across project boundaries)
- Strategic rule storage backend (dedicated storage within the governance
  and archive layers)
- Automated blast radius assessment
- Strategic rule conflict detection (what happens when two strategic rules
  contradict each other?)
- Metacognitive feedback loops (L4 rules modifying cognitive operation
  parameters at runtime)

### 7.4 Path Forward

The implementation will proceed incrementally:

1. **Phase A**: `promotion_engine.py` provides the core L3 → L4 transition
   mechanism
2. **Phase B**: Cross-project validation infrastructure enables evidence
   sharing
3. **Phase C**: Strategic rule storage and retrieval within the memory
   system
4. **Phase D**: Runtime integration with attention, governance, and routing
   subsystems
5. **Phase E**: Metacognitive feedback loops (L4 → cognitive operations)

Each phase requires its own governance review and documentation update.

---

## 8. Code References

| Component | Path | Role |
|---|---|---|
| PromotionEngine | `memory/ontology/promotion_engine.py` | L3 → L4 transition engine (in development) |
| MandatoryGate | `governance/mandatory_gate.py` | Governance entry point |
| ExecutionValidator | `governance/execution_validator.py` | 4-stage validation pipeline |
| PolicyEngine | `governance/policy_engine.py` | Policy evaluation (10+ policies) |
| GovernanceAuditLog | `governance/audit_log.py` | Immutable audit trail |
| AnomalyDetector | `governance/anomaly_detector.py` | Behavioral anomaly detection |
| SalienceEngine | `attention/salience_engine.py` | 9-factor attention scoring |
| PriorityAllocator | `attention/priority_allocator.py` | Domain budget allocation |
| EscalationRouter | `attention/escalation_router.py` | Threshold-based escalation |
| SkillRouter | `skills/core/skill_router.py` | Skill selection and routing |
| MemoryKernel | `memory/memory_kernel.py` | 6-layer storage engine |
| SkillRegistrationPipeline | `agents/skillify/skill_registration_pipeline.py` | Upstream registration |

---

## 9. Related Documents

- [`observation_to_instinct.md`](./observation_to_instinct.md) — L1 → L2 evolution
- [`instinct_to_skill.md`](./instinct_to_skill.md) — L2 → L3 evolution
- [`docs/cognitive/strategic_memory.md`](../../../docs/cognitive/strategic_memory.md) — Strategic memory architecture
- [`docs/cognitive/skill_evolution.md`](../../../docs/cognitive/skill_evolution.md) — Full pipeline overview
- [`docs/cognitive/verification_doctrine.md`](../../../docs/cognitive/verification_doctrine.md) — Verification requirements
- [`docs/cognitive/somatic_metacognition_spec_v1.md`](../../../docs/cognitive/somatic_metacognition_spec_v1.md) — Master specification

---

*The L3 → L4 transition is the most consequential promotion in the cognitive
hierarchy. A faulty instinct affects one observation. A faulty skill affects
one procedure. A faulty strategy affects the entire system. The governance
requirements here are the highest not because we distrust the system, but
because we respect the scope of what strategic rules can do. The aspiration
is a system that genuinely learns from its experience—but only when that
learning has been earned through evidence, validation, and independent
verification.*
