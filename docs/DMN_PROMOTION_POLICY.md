# DMN Promotion Policy

Phase: 1G.5 DMN Memory Governance Review  
Date: 2026-06-09  
Status: Policy only. No DMN behavior is changed by this document.

## Purpose

This policy defines when an event, observation, or working-memory item may become durable DMN memory or higher governance memory.

Promotion is the act of turning transient context into governed experience. Promotion must be explicit, auditable, reversible by correction or tombstone, and never treated as proof that the promoted content is true.

## Memory Classes

| Class | Meaning | Promotion Role |
| --- | --- | --- |
| Working Memory | Active task context, local assumptions, current evidence, and temporary state. | May propose DMN candidates but is not durable by default. |
| DMN Memory | Append-only durable project memory for history, preferences, incidents, repeated topics, unresolved ambiguity, and architecture decisions. | Receives promoted records with source and reason. |
| Governance Memory | Constitutional rules, review outcomes, safety doctrine, Guardian-relevant decisions, and repository policy. | Requires the highest evidence and review bar. |

## Candidate Promotion Criteria

A record may become a promotion candidate when at least one criterion applies:

| Criterion | Meaning | Typical Target |
| --- | --- | --- |
| Anomaly detected | A meaningful abnormal event was observed and may recur or affect safety. | DMN memory; governance memory if safety-significant. |
| Repeated observation | The same pattern appears across multiple events, sessions, contexts, or agents. | DMN memory; possibly L2 instinct candidate. |
| Governance significance | The event changes review, risk, safety, or policy interpretation. | Governance memory. |
| Replay significance | The record is needed to reconstruct a decision, incident, test, or failure. | DMN memory with replay pointer. |
| Human-confirmed importance | The operator explicitly marks the information as important or persistent. | DMN memory or governance memory depending on scope. |
| Guardian-reviewed event | Guardian classified, allowed, blocked, escalated, or observed the event. | DMN memory; governance memory if policy-relevant. |

## Existing Promotion Evidence

Repository code already defines sequential cognitive promotion:

| Transition | Evidence | Requirement Summary |
| --- | --- | --- |
| L1 Episodic -> L2 Instinct | `memory/ontology/promotion_rules.py` and `promotion_chain_validator.py` | Minimum confidence 0.7, recurrence 3, no active contradictions. |
| L2 Instinct -> L3 Skill | Same | Minimum confidence 0.8, recurrence 5, governance required, cross-context validation. |
| L3 Skill -> L4 Strategic | Same | Minimum confidence 0.9, recurrence 10, governance required, independent verifier required. |

`memory/ontology/promotion_engine.py` stores promotion candidates, approval results, governance decision IDs, verifier IDs, and audit records. `promotion_guard.py` blocks invalid chain skips and records violations.

## Required Promotion Metadata

Future promoted DMN records or wrappers should preserve:

- `record_id`
- `source_record_ids`
- `source_layer`
- `target_layer`
- `promotion_reason`
- `promotion_criteria`
- `confidence`
- `confidence_rationale`
- `occurrence_count`
- `contradiction_count`
- `governance_decision_id`
- `guardian_review_id`
- `verifier_id`
- `replay_pointer`
- `privacy_class`
- `retention_policy`
- `created_by`
- `created_at`

## Promotion Rules

1. Working memory does not become durable memory automatically.
2. Promotion must preserve source identity and source evidence.
3. Promotion into governance memory requires explicit governance rationale.
4. A recalled memory cannot promote itself.
5. Vector similarity cannot justify promotion by itself.
6. Active contradictions block promotion until reviewed.
7. Strategic or governance-level promotion requires independent verification.
8. Historical DMN records may be wrapped for promotion evidence, but must not be rewritten.

## Blocking Conditions

Promotion must be blocked when:

- The source is unknown.
- The record contains sensitive or restricted data without review.
- The record cannot explain why it matters.
- The record has no replay pointer or replay-unavailable reason.
- Contradiction count is greater than zero and unresolved.
- The target layer skips the approved promotion chain.
- The promoter and verifier are the same for strategic promotion.

## Review Expectations

Low-risk DMN promotion may be reviewed by the project owner or an assigned reviewer.

Medium-risk promotion, including memory used by future recall systems, requires governance review.

High-risk promotion, including Guardian-impacting, safety-impacting, cross-node, or governance memory, requires human approval and independent verification.
