# Verifier Protocol

This document specifies how an independent verifier evaluates artifacts
submitted for promotion through the memory ontology.

## Verifier Identity Requirements

1. **Distinct identity**: The verifier's `verifier_id` must differ from
   the artifact's `implementer_id`. The system enforces this
   programmatically.
2. **Capability match**: The verifier should have domain knowledge
   relevant to the artifact type (e.g., a somatic-domain verifier for
   anomaly fingerprints).
3. **No conflict of interest**: The verifier must not have authored any
   of the evidence supporting the promotion candidate.

## Verification Steps

A verifier follows this checklist when evaluating an artifact:

### Step 1 — Context Review

- Read the `VerificationRequest.context` dict to understand what the
  artifact does, why it was proposed, and what evidence supports it.
- Review the artifact's confidence history via
  `SomaticConfidenceTracker.get_history()`.

### Step 2 — Evidence Validation

- Confirm that the supporting evidence (episode counts, similarity
  scores, occurrence counts) matches reality.
- Cross-reference with the somatic episode store if applicable.
- Check for circular reasoning (artifact referencing its own output as
  evidence).

### Step 3 — Boundary Testing

- Identify edge cases that could cause the artifact to produce
  incorrect results.
- For skills: test with inputs outside the training distribution.
- For fingerprints: check whether the pattern could be noise.
- For strategic rules: assess blast radius if the rule is wrong.

### Step 4 — Confidence Assessment

Assign a confidence score (0.0–1.0) based on:

| Factor | Weight |
|---|---|
| Evidence quality | 40% |
| Edge case robustness | 30% |
| Alignment with existing knowledge | 20% |
| Clarity of the artifact's scope | 10% |

### Step 5 — Decision

- **Approve**: The artifact meets all criteria and the verifier is
  confident in its correctness.
- **Reject**: The artifact has blocking issues that must be resolved.
- **Inconclusive**: The verifier cannot determine correctness with
  sufficient confidence (confidence < 0.4).

## Confidence Scoring

The verifier must report a single confidence float (0.0–1.0):

- **0.0–0.39**: "I cannot determine if this is correct."
- **0.4–0.69**: "This is probably correct but I have reservations."
- **0.7–0.89**: "I am confident this is correct."
- **0.9–1.0**: "I am highly confident and have verified thoroughly."

## Rejection Criteria

An artifact **must** be rejected if any of the following are true:

1. The supporting evidence is fabricated or circular.
2. The artifact contradicts established L3/L4 knowledge.
3. The artifact's scope is unbounded (could affect unrelated domains).
4. The confidence history shows repeated failures without correction.
5. The artifact was previously rejected and resubmitted without changes.

## Appeal Process

1. The implementer may submit an **appeal** with additional evidence.
2. The appeal is assigned to a **different verifier** than the original
   rejector (to prevent deadlocks).
3. If the appeal verifier also rejects, the artifact is marked as
   `PERMANENTLY_REJECTED` and may only be reconsidered after a
   material change (new evidence, code fix, etc.).
4. At most 2 appeal rounds are permitted per artifact.

## Audit Requirements

The following are recorded for every verification:

| Field | Description |
|---|---|
| `request_id` | Unique ID of the verification request |
| `artifact_id` | The artifact being verified |
| `artifact_type` | Type of artifact (skill, fingerprint, etc.) |
| `implementer_id` | Who created the artifact |
| `verifier_id` | Who verified it |
| `confidence` | Verifier's confidence score |
| `approved` | Boolean decision |
| `findings` | What the verifier observed |
| `recommendations` | Suggestions for improvement |
| `blocking_issues` | Issues that prevented approval |
| `verified_at` | Timestamp of the verification |

All audit records are immutable once written.
