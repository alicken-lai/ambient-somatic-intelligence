# Strategic Memory Architecture

> Ambient OS v0.3.1-alpha — L4 Knowledge Layer Design

---

## 1. Purpose

Strategic memory is the highest layer (L4) of the Ambient OS cognitive
hierarchy. It stores abstract principles—decision heuristics, metacognitive
rules, routing philosophies, and escalation principles—that transcend any
single skill, project, or domain. Strategic memory represents the system's
accumulated wisdom and directly influences how all lower layers operate.

This document defines what strategic memory stores, how knowledge reaches this
level, and the governance requirements that protect it.

---

## 2. What Strategic Memory Stores

### 2.1 Decision Heuristics

Abstract rules for choosing between alternatives when multiple valid paths
exist. Decision heuristics encode the "why" behind choices that have been
validated across multiple contexts.

**Example**: "When two skills have equivalent success rates but different
resource costs, prefer the lower-cost skill unless the higher-cost skill has
demonstrated superior edge-case handling."

### 2.2 Metacognitive Rules

Rules about how to apply other rules. Metacognitive rules govern the cognitive
operations themselves—adjusting how the system captures, consolidates, distills,
and promotes knowledge.

**Example**: "When operating in a high-anomaly environment (salience > 0.75
for more than 10 minutes), increase the attention budget for the `somatic`
domain from 0.30 to 0.45 and reduce `task` from 0.20 to 0.10."

### 2.3 Routing Philosophies

Principles governing how attention, resources, and agent effort are allocated
across domains. Routing philosophies influence the `SalienceEngine`,
`PriorityAllocator`, and `EscalationRouter`.

**Example**: "Governance-related signals should never be throttled regardless
of budget constraints. The `MUST_ATTEND_SALIENCE` threshold (0.85) applies to
governance events even when overall system load is high."

### 2.4 Escalation Principles

Criteria for when the system should involve human operators, escalate to
higher governance levels, or defer action entirely.

**Example**: "If three consecutive skill executions fail in the same domain
within 5 minutes, escalate to human operator before retrying. Do not rely
on automatic retry logic for repeated failures."

---

## 3. How Local Knowledge Becomes Global Doctrine

Strategic rules emerge through a multi-stage abstraction process that ensures
only well-validated, broadly applicable knowledge reaches L4.

### 3.1 The Promotion Path

```
L1 (Episodic)  →  L2 (Instinct)  →  L3 (Skill)  →  L4 (Strategy)
    │                  │                  │                │
    │  Distillation    │  Clustering +    │  Abstraction + │
    │  via pattern     │  governance      │  cross-project │
    │  mining          │  review          │  validation    │
    ▼                  ▼                  ▼                ▼
  Raw events      Atomic rules      Procedures       Principles
```

### 3.2 Cross-Project Promotion

The defining characteristic of L4 promotion is **cross-project validation**.
A pattern that succeeds in one context is an instinct or skill. A pattern that
succeeds across fundamentally different contexts is a strategy.

**Concrete example — Cross-project promotion path**:

| Stage | Context | Observation |
|---|---|---|
| L2 instinct (React) | Frontend project | "Debounce user input events before API calls" |
| L2 instinct (Python) | Backend project | "Rate-limit external API calls with exponential backoff" |
| L2 instinct (Go) | Infrastructure project | "Buffer sensor readings before batch processing" |
| L3 skill | Cross-domain | "Input smoothing: buffer high-frequency events before downstream processing" |
| **L4 strategy** | **Universal** | **"High-frequency input sources should always be smoothed before triggering downstream operations. The smoothing strategy (debounce, rate-limit, or batch) should match the latency tolerance of the consumer."** |

Each step in this chain requires independent validation:
1. Each L2 instinct is validated within its own project context
2. The L3 skill is validated by demonstrating the pattern's applicability across at least 3 contexts
3. The L4 strategy is validated by demonstrating that the abstract principle produces correct decisions when applied to novel contexts

### 3.3 Abstraction Requirements

To qualify for L4, a candidate rule must demonstrate:

1. **Domain independence**: The rule is not tied to a specific language, framework, or tool
2. **Compositional clarity**: The rule can be stated without reference to implementation details
3. **Predictive power**: The rule correctly predicts outcomes in contexts where it has not been explicitly tested
4. **Falsifiability**: The rule can be contradicted by evidence, enabling decay if invalidated

---

## 4. Promotion Conditions

All of the following must be satisfied for L3 → L4 promotion:

### 4.1 Cross-Project Validation

The candidate rule must have been validated in at least **3 distinct project
contexts**. "Distinct" means different in at least two of: programming language,
domain, infrastructure environment, or operational phase.

### 4.2 High Confidence Threshold

All constituent L3 skills must have confidence ≥ 0.90. The candidate strategic
rule must have a projected confidence ≥ 0.90 based on its track record.

### 4.3 Independent Verifier Approval

A verifier that is independent from the implementing agent must approve the
promotion. Per the Guardian Verification Doctrine, the implementer cannot
self-certify. See [`verification_doctrine.md`](./verification_doctrine.md).

### 4.4 Governance Gate

L4 promotion requires the **highest governance level**. This means:

- `MandatoryGate` must classify the action as `REVIEW_REQUIRED` at minimum
- The `PolicyEngine` must evaluate all applicable policies
- The `GovernanceAuditLog` must record the full decision chain
- A human operator must be notified (escalation via `EscalationRouter`)

### 4.5 Reversibility Confirmation

Before promotion is finalized, a rollback path must be confirmed. This includes:

- The ability to demote the strategic rule back to L3
- Verification that no downstream routing or escalation behavior depends
  irreversibly on the new rule
- Documentation of the expected impact of rollback

---

## 5. Reversibility Requirements

Strategic memory modifications are high-impact and must be reversible.

### 5.1 Version History

Every strategic rule maintains a version history. Modifications create new
versions rather than overwriting existing entries. The `archive` storage layer
(TTL 3650d) preserves historical versions for long-term reference.

### 5.2 Rollback Procedure

1. Identify the strategic rule version to restore
2. Verify that downstream dependencies (salience weights, escalation thresholds,
   routing configurations) are compatible with the prior version
3. Submit rollback request through `MandatoryGate`
4. Log the rollback in `GovernanceAuditLog` with full rationale
5. Notify affected subsystems to refresh their cached configurations

### 5.3 Blast Radius Assessment

Before any L4 modification (promotion, update, or rollback), the system must
assess the blast radius—which subsystems, agents, and skills are affected by
the change. This assessment is part of the governance review process.

---

## 6. Auditability Requirements

### 6.1 Decision Trail

Every strategic rule must maintain a complete decision trail:
- **Origin**: Which L3 skills were abstracted to produce the rule
- **Evidence**: Which cross-project validations supported the promotion
- **Approvers**: Which verifiers and governance reviewers approved the promotion
- **Timestamps**: When each stage of promotion occurred
- **Rationale**: Why the rule was deemed strategically valuable

### 6.2 Audit Storage

Strategic memory audit records are stored in `governance/audit/decisions.jsonl`
via `GovernanceAuditLog`. These records are append-only and follow the same
immutability guarantees as all governance records.

### 6.3 Periodic Review

Strategic rules should be periodically reviewed to confirm continued relevance.
If a strategic rule has not been referenced in any decision path within its
decay half-life (90 days for governance-layer, 365 days for archive-layer),
it should be flagged for review.

---

## 7. Explainability Requirements

### 7.1 Human-Readable Rationale

Every strategic rule must include a human-readable explanation of:
- **What** the rule states
- **Why** the rule exists (the evidence chain)
- **When** the rule applies (contextual preconditions)
- **What happens** if the rule is violated (expected failure modes)

### 7.2 Provenance Chain

It must be possible to trace any strategic rule back to its constituent
L3 skills, L2 instincts, and ultimately to the L1 episodic events that
originated the insight. This provenance chain is the primary mechanism for
explainability.

### 7.3 Counter-Evidence Tracking

When evidence contradicts a strategic rule, the contradiction must be recorded
alongside the rule. This enables reviewers to assess whether the rule is
weakening and whether a confidence reduction or retirement is appropriate.

---

## 8. Integration with Governance

### 8.1 MandatoryGate Integration

All L4 operations (creation, modification, rollback) must pass through
`MandatoryGate` (`governance/mandatory_gate.py`). The gate combines:

- `ExecutionValidator` — 4-stage pipeline (policy → anomaly → resource → injection)
- `ToolPermissionMatrix` — Role-based access control
- `GovernanceAuditLog` — Immutable audit trail

### 8.2 PolicyEngine Considerations

The `PolicyEngine` (`governance/policy_engine.py`) maintains 10+ built-in
policies with priority-based conflict resolution. Strategic memory operations
should be classified at priority level 100 (highest) to ensure they are never
overridden by lower-priority policies.

### 8.3 Anomaly Detection

The `AnomalyDetector` (`governance/anomaly_detector.py`) monitors for:
- Failure loops that might indicate a faulty strategic rule
- Unusual action rates that might result from a misconfigured routing philosophy
- Repetition patterns that might indicate a metacognitive rule creating a feedback loop

### 8.4 Human-in-the-Loop

For L4 operations, human notification is mandatory. The `EscalationRouter`
(`attention/escalation_router.py`) must route L4 promotions to the
`ESCALATE` action (threshold 0.75), ensuring human awareness even if automatic
approval criteria are met.

---

## 9. Related Documents

- [`somatic_metacognition_spec_v1.md`](./somatic_metacognition_spec_v1.md) — Master specification
- [`memory_ontology.md`](./memory_ontology.md) — Formal memory layer definitions
- [`verification_doctrine.md`](./verification_doctrine.md) — Guardian Verification Doctrine
- [`skill_evolution.md`](./skill_evolution.md) — Skill evolution pipeline
- [`../../agents/skillify/doctrine/skill_to_strategy.md`](../../agents/skillify/doctrine/skill_to_strategy.md) — L3→L4 evolution doctrine

---

*Strategic memory is the most powerful and most dangerous layer of the cognitive
hierarchy. Its influence is system-wide and its modifications are high-impact.
Every safeguard defined here exists because the cost of a faulty strategic rule
is proportional to its scope—and its scope is the entire system.*
