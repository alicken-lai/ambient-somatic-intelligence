# Guardian Verification Doctrine

> Ambient OS v0.3.1-alpha — Independent Verification Requirements

---

## 1. Core Principle

> **"The implementer is an LLM. Verify independently."**

Every knowledge promotion, skill registration, and strategic rule adoption in
Ambient OS is produced by a language model. Language models are capable but
fundamentally unreliable as self-assessors. They exhibit systematic biases
toward overconfidence, pattern-completion artifacts, and plausible-but-incorrect
reasoning.

The Guardian Verification Doctrine exists to counteract these failure modes
through a single, non-negotiable requirement: **the entity that produces a
result must never be the sole entity that certifies that result.**

---

## 2. Verification Axioms

### Axiom 1 — The Implementer Cannot Self-Certify

An agent that generates an instinct, skill, or strategic rule is prohibited
from approving its own output. Self-certification is treated as a governance
violation.

**Rationale**: LLMs are prone to confirmation bias. The same reasoning process
that produced an incorrect result will often "verify" it as correct.

### Axiom 2 — The Verifier Must Be Independent

The verifying entity must operate with independent context and, ideally,
independent reasoning. "Independent" means:

- **Different execution context**: The verifier should not share the same
  conversation history or prompt chain as the implementer
- **Different evaluation criteria**: The verifier should check against
  objective criteria (test results, policy compliance, schema validity)
  rather than subjective quality assessment
- **No shared incentive**: The verifier should not benefit from approving
  the implementer's output

### Axiom 3 — Verification Confidence Must Be Tracked

Every verification produces a confidence score. This score reflects the
verifier's assessment of the correctness, safety, and applicability of the
verified artifact. Confidence scores are:

- Recorded in the `GovernanceAuditLog`
- Used as input to promotion decisions
- Subject to decay over time if not re-validated

### Axiom 4 — Low Confidence Blocks Promotion

If verification confidence falls below the required threshold for a given
promotion level, the promotion is blocked. The thresholds are:

| Promotion | Minimum Verification Confidence |
|---|---|
| L1 → L2 (Instinct) | 0.60 |
| L2 → L3 (Skill) | 0.70 |
| L3 → L4 (Strategy) | 0.90 |

A blocked promotion is not a failure—it is the system working as designed.
The candidate remains at its current layer and may be re-submitted after
additional evidence is gathered.

---

## 3. Integration Points

### 3.1 Skill Registration

The `SkillRegistrationPipeline` (`agents/skillify/skill_registration_pipeline.py`)
enforces verification at the registration gate:

```
Pipeline: propose → approve → register
                      │
                      ▼
              Reviewer identity required
              Governance audit logged
              Rollback path preserved
```

The `approve()` method requires a `reviewer` parameter identifying the
approving entity. The `ProposalResult` and `ApprovalResult` dataclasses
track the full lifecycle.

**Known gap**: The current implementation of `approve()` accepts any string
as the `reviewer` parameter without verifying the identity or independence
of the reviewer. This means:
- An implementer agent could pass its own identifier as the reviewer
- There is no cryptographic or structural guarantee of reviewer independence
- The audit log records the reviewer string but cannot verify its authenticity

**Recommended remediation** (tracked for future implementation):
1. Introduce a reviewer identity registry with unique, non-forgeable identifiers
2. Enforce that `reviewer_id != implementer_id` at the pipeline level
3. Require reviewer identity to be attested through the governance system
4. Add a `verification_confidence` field to `ApprovalResult`

### 3.2 Strategic Memory Promotion

L3 → L4 promotion requires the highest verification bar. The verifier must:

1. Confirm cross-project validation evidence
2. Assess the strategic rule's domain independence
3. Evaluate the blast radius of the promotion
4. Record a confidence score ≥ 0.90
5. Submit approval through `MandatoryGate`

See [`strategic_memory.md`](./strategic_memory.md) for full L4 promotion
requirements.

### 3.3 Skillify Proposals

The Skillify pipeline (`agents/skillify/`) is a proposer, not an approver.
Skillify's role is strictly limited to:

- **Observing** workflow patterns (`WorkflowObserver`)
- **Mining** recurring patterns (`SkillifyPatternMiner`)
- **Clustering** related patterns (`WorkflowCluster`)
- **Generating** skill candidates (`SkillCandidateGenerator`)
- **Validating** candidates against minimum criteria (`SkillCandidateValidator`)
- **Proposing** candidates for governance review (`SkillRegistrationPipeline.propose()`)

Skillify must **never**:
- Call `approve()` on its own proposals
- Directly register skills without governance review
- Modify routing tables or escalation rules automatically

---

## 4. Verification Methods

### 4.1 Structural Verification

Check that the artifact conforms to its expected schema and constraints:
- Skill schemas are validated by `SkillValidator` (`skills/core/skill_validator.py`)
- Inputs and outputs match declared types
- Governance level is appropriately assigned
- Memory effects are declared and validated

### 4.2 Behavioral Verification

Check that the artifact produces correct results when executed:
- Simulation-based testing via `SkillCandidateValidator.simulate()`
- Cross-reference with historical execution traces
- Comparison against known-good outcomes

### 4.3 Policy Verification

Check that the artifact complies with governance policies:
- `ExecutionValidator` 4-stage pipeline (policy → anomaly → resource → injection)
- `PolicyEngine` rule evaluation
- `ToolPermissionMatrix` access control verification

### 4.4 Cross-Context Verification

Check that the artifact holds across different contexts:
- Different projects or domains
- Different environmental signatures
- Different operational phases (per `OperationalPhase` in attention system)

---

## 5. Governance Cross-References

| Component | Path | Role in Verification |
|---|---|---|
| MandatoryGate | `governance/mandatory_gate.py` | Single entry point for all governed actions |
| ExecutionValidator | `governance/execution_validator.py` | 4-stage validation pipeline |
| PolicyEngine | `governance/policy_engine.py` | Rule-based policy evaluation (10+ policies, priority-based) |
| AnomalyDetector | `governance/anomaly_detector.py` | Behavioral anomaly detection (failure loops, rate limits) |
| GovernanceAuditLog | `governance/audit_log.py` | Append-only decision and incident records |
| ToolPermissionMatrix | `governance/tool_permission_matrix.py` | Role-based tool access (ALLOWED/DENIED/REQUIRES_REVIEW) |

---

## 6. Failure Modes and Mitigations

### 6.1 Rubber-Stamp Verification

**Risk**: A verifier approves without meaningful review.

**Mitigation**: Verification must include specific evidence (test results,
policy check outcomes, confidence scores). The audit log records what evidence
was provided. Empty or formulaic approvals should be flagged by the anomaly
detector.

### 6.2 Collusion

**Risk**: Implementer and verifier coordinate to bypass verification.

**Mitigation**: The reviewer identity gap (Section 3.1) is acknowledged as a
current limitation. Until cryptographic identity is implemented, operational
controls include:
- Audit log review by human operators
- Periodic sampling of approval decisions
- Anomaly detection for approval patterns (e.g., same reviewer always
  approving the same implementer)

### 6.3 Verification Drift

**Risk**: Verification criteria become stale as the system evolves.

**Mitigation**: Verification criteria are themselves subject to the L4 strategic
memory lifecycle. If verification criteria fail to catch known-bad artifacts,
they can be updated through the standard governance process.

### 6.4 Over-Verification

**Risk**: Excessive verification requirements block legitimate knowledge
promotion, making the system unable to learn.

**Mitigation**: Confidence thresholds are tuned to balance safety against
learning speed. The decay mechanism ensures that knowledge which cannot be
verified in a timely manner is naturally forgotten rather than permanently
blocked.

---

## 7. Related Documents

- [`somatic_metacognition_spec_v1.md`](./somatic_metacognition_spec_v1.md) — Master specification
- [`memory_ontology.md`](./memory_ontology.md) — Formal memory layer definitions
- [`strategic_memory.md`](./strategic_memory.md) — Strategic memory architecture
- [`skill_evolution.md`](./skill_evolution.md) — Skill evolution pipeline

---

*Verification is the immune system of the cognitive architecture. Without it,
the system's knowledge base would be as unreliable as the LLMs that populate
it. With it, unreliable components compose into a reliable whole—not by
eliminating error, but by ensuring that no error goes unchallenged.*
