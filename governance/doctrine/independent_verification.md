# Independent Verification Doctrine

> *"The implementer is an LLM. Verify independently."*

## Core Principle

Large language models can be **confidently wrong**. An LLM that
implements a skill, proposes a strategic rule, or promotes a memory
entry may produce output that _appears_ correct but is subtly flawed.
Independent verification prevents self-reinforcing errors from
propagating through the memory hierarchy.

## Why This Matters

| Risk | Consequence without verification |
|---|---|
| Hallucinated patterns | Invalid L2 instincts fire on noise |
| Overfit skills | L3 skills that only work for one project |
| Circular evidence | A precursor pattern "validated" by the same agent that proposed it |
| Confidence inflation | Auto-promoted entries crowd out genuine knowledge |

## The Four Verification Rules

### Rule 1 — No Self-Certification

The entity that **created** an artifact cannot certify its correctness.
This applies to all promotions beyond L1 (Episodic). Raw episodes at L1
are observational data and may self-certify because they represent
measured reality, not inferred knowledge.

### Rule 2 — Independent Verifier

The verifier must be a **different agent, entity, or human operator**
than the implementer. Identity is tracked via `implementer_id` and
`verifier_id`; the system rejects any verification where these match.

### Rule 3 — Verification Confidence Tracking

The verifier must report a **confidence score** (0.0–1.0) alongside
their approval or rejection. This score indicates how certain the
verifier is in their own assessment:

| Score range | Interpretation |
|---|---|
| 0.0–0.39 | Low confidence — inconclusive, do not use for promotion |
| 0.4–0.69 | Moderate — may be accepted with additional review |
| 0.7–1.0 | High — sufficient for promotion decisions |

### Rule 4 — Low Confidence Blocks Promotion

If the verifier's confidence falls below the policy threshold
(`min_verifier_confidence`, default 0.7), the verification is recorded
but **does not count** as approval. The artifact remains at its current
layer until a higher-confidence verification is obtained.

## Integration Points

### Skill Registration

Before a candidate skill enters the skill registry, a verifier must
approve it. The skill's `governance_level` is set to `PENDING_VERIFICATION`
until approval is received.

### Strategic Memory Promotion (L3 → L4)

Promotion from Skill (L3) to Strategic (L4) represents a system-wide
rule that influences future decision-making. This is the highest-risk
promotion and **always** requires:
- Independent verification with confidence ≥ 0.8
- Documented evidence from at least 3 successful applications
- Governance audit trail entry

### Skillify Proposals

When the Skillify agent proposes a new skill from observed workflows,
the proposal is treated as a verification request. The implementing
Skillify agent cannot approve its own proposal.

## Governance Escalation

If no independent verifier is available (e.g., single-agent deployment
or all available agents have conflicts of interest), the system
**escalates to the human operator**. Under no circumstances may an
artifact auto-promote without verification.

Escalation triggers:
- No verifier available within the configured timeout
- All available verifiers have low confidence
- The artifact's target layer is L4 (Strategic)
- The policy flag `escalate_on_low_confidence` is set

## Audit Requirements

Every verification decision — approval, rejection, escalation, and
re-verification — is recorded in the governance audit trail with:
- Timestamp
- Artifact ID and type
- Implementer ID
- Verifier ID (or "ESCALATED" for human escalation)
- Confidence score
- Decision and reasoning
