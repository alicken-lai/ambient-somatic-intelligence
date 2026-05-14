# Observation to Instinct — L1 → L2 Evolution Doctrine

> Ambient OS v0.3.1-alpha — Skillify Evolution Doctrine

---

## 1. Overview

This document defines how raw episodic events (L1) are transformed into
reusable instincts (L2) through the Skillify pipeline. The L1 → L2 transition
is the foundational evolution step—it is where the system first distills
experience into knowledge.

An instinct is an atomic, confidence-scored observation that has been validated
through repeated occurrence and cross-session stability. Instincts are the
building blocks from which skills (L3) are eventually assembled.

---

## 2. Workflow Observation — Capturing L1 Events

### 2.1 The WorkflowObserver

**Reference**: `agents/skillify/workflow_observer.py`

The `WorkflowObserver` captures raw workflow events as they occur during agent
execution. It is a passive observer—it records but does not filter, judge, or
modify events.

**Captured data per event** (`WorkflowStep` / `WorkflowEvent`):

| Field | Type | Description |
|---|---|---|
| `workflow_id` | str | Unique identifier for the workflow instance |
| `step_name` | str | Human-readable step identifier |
| `tool_used` | str | Which tool was invoked |
| `parameters` | dict | Input parameters passed to the tool |
| `result` | dict | Output produced by the tool |
| `duration_ms` | float | Execution time in milliseconds |
| `success` | bool | Whether the step succeeded |
| `timestamp` | str | ISO 8601 timestamp |
| `session_id` | str | Identifier for the session context |
| `context` | dict | Additional contextual metadata |

### 2.2 Storage

Events are persisted to `observations.jsonl` in append-only mode, consistent
with the AGENTS.md mandate that memory is append-only at the capture layer.

### 2.3 No Filtering at Capture

The observer captures all events without prejudice. Filtering and relevance
assessment happen downstream in the pattern mining stage. This ensures that
the system never discards potentially valuable signal before it has been
analyzed.

---

## 3. Pattern Detection — Mining Recurring Patterns

### 3.1 The SkillifyPatternMiner

**Reference**: `agents/skillify/pattern_miner.py`

The `SkillifyPatternMiner` analyzes accumulated observations to detect
recurring patterns. It operates on the full observation corpus and produces
`WorkflowPattern` objects.

### 3.2 Mining Process

1. **Load observations**: Read the full `observations.jsonl` corpus
2. **Sequence extraction**: Identify repeated step sequences across workflows
3. **Frequency analysis**: Count occurrences of each candidate pattern
4. **Variation scoring**: Assess pattern stability using:
   ```
   variation = 0.6 × sequence_similarity + 0.4 × duration_similarity
   ```
5. **Threshold filtering**: Retain only patterns meeting `min_support`
6. **Output**: `WorkflowPattern` objects with occurrence count, success rate,
   and context metadata

### 3.3 The min_support Parameter

The `min_support` parameter is the minimum number of times a pattern must
appear before it is considered for instinct candidacy. This is configurable
and should be tuned based on:

- **Volume of observations**: Higher-traffic domains may warrant higher
  thresholds to filter noise
- **Domain criticality**: Safety-critical domains may warrant lower thresholds
  to catch important patterns early
- **Confidence requirements**: Higher `min_support` produces higher initial
  confidence scores

---

## 4. Criteria for Instinct Candidacy

A detected pattern becomes an instinct candidate when it meets all of the
following criteria:

### 4.1 Minimum Occurrence Threshold

The pattern must appear at least `min_support` times (as configured in
`SkillifyPatternMiner`). This ensures that the observation is not an artifact
of a single session or a one-time coincidence.

### 4.2 Minimum Success Rate

The pattern's occurrences must demonstrate a positive outcome rate above a
configurable threshold. A pattern that occurs frequently but fails often is
not a reliable instinct—it is noise or a misidentified anti-pattern.

### 4.3 Stable Environmental Context

The pattern must hold across the relevant environmental signature bands.
The somatic subsystem (`memory/somatic/`) provides environmental context
through `EnvironmentalSignature`, which quantizes system state into 5 bands:

| Band | Source |
|---|---|
| CPU utilization | System load |
| Memory utilization | Available/total RAM |
| Disk utilization | Storage capacity |
| System load | Load average |
| Process count | Active processes |

A pattern that only appears under a very specific environmental signature
may still be valid but should have its contextual applicability restricted
accordingly.

### 4.4 Cross-Session Validation

The pattern must appear across multiple independent sessions (`session_id`
values). A pattern confined to a single session may reflect session-specific
behavior rather than a general principle.

---

## 5. Confidence Initialization

When an instinct candidate is created, its initial confidence score is
computed as a weighted combination of four factors:

| Factor | Weight | Computation |
|---|---|---|
| Occurrence frequency | 0.30 | Normalized count relative to observation corpus size |
| Success rate | 0.35 | Proportion of occurrences with `success = True` |
| Consistency | 0.20 | Inverse of variation across occurrences (low variance = high consistency) |
| Breadth | 0.15 | Number of distinct sessions / environmental contexts |

These weights align with the `skill_potential` scoring used downstream in
`WorkflowCluster` (`agents/skillify/workflow_cluster.py`), ensuring
consistency across the promotion pipeline.

### Confidence Range Interpretation

| Range | Interpretation |
|---|---|
| 0.90 – 1.00 | Very high confidence; strong candidate for rapid promotion |
| 0.70 – 0.89 | High confidence; eligible for L3 skill promotion |
| 0.50 – 0.69 | Moderate confidence; needs further validation |
| 0.30 – 0.49 | Low confidence; at risk of decay if not reinforced |
| 0.00 – 0.29 | Below retention threshold; will be evicted |

---

## 6. Governance Review Requirement

Per the Guardian Verification Doctrine (see `docs/cognitive/verification_doctrine.md`),
the transition from L1 to L2 requires verification:

1. **The pattern miner proposes**: Skillify identifies the candidate and
   computes initial confidence
2. **An independent verifier reviews**: The candidate is assessed against
   objective criteria (occurrence data, success rate, environmental stability)
3. **Verification confidence is recorded**: The verifier's confidence assessment
   (minimum 0.60 for L1 → L2) is logged
4. **The audit trail is updated**: `GovernanceAuditLog` records the proposal,
   review, and outcome

The verifier must not be the same agent instance that ran the pattern mining.
See the Verification Doctrine's known gap regarding reviewer identity
enforcement.

---

## 7. Post-Creation Lifecycle

Once an instinct is accepted into L2:

- **Successful reuse** increases confidence (capped increment)
- **Failed reuse** decreases confidence (proportional decrement)
- **Contradiction** triggers immediate confidence reduction and review
- **Inactivity** triggers gradual decay per storage-layer half-lives
- **Cross-context validation** in new environments provides confidence boost
- **Reaching confidence ≥ 0.70** makes the instinct eligible for L3 skill
  promotion through the clustering pipeline

---

## 8. Code References

| Component | Path | Role |
|---|---|---|
| WorkflowObserver | `agents/skillify/workflow_observer.py` | L1 event capture |
| WorkflowStep | `agents/skillify/workflow_observer.py` | Event data model |
| WorkflowEvent | `agents/skillify/workflow_observer.py` | Event wrapper |
| SkillifyPatternMiner | `agents/skillify/pattern_miner.py` | Pattern detection |
| WorkflowPattern | `agents/skillify/pattern_miner.py` | Pattern data model |
| EnvironmentalSignature | `memory/somatic/environmental_signature.py` | Environmental context |
| SensorEpisode | `memory/somatic/sensor_episode.py` | Sensor event model |
| PrecursorMatcher | `memory/somatic/precursor_matcher.py` | Precursor detection |

---

## 9. Related Documents

- [`instinct_to_skill.md`](./instinct_to_skill.md) — L2 → L3 evolution
- [`skill_to_strategy.md`](./skill_to_strategy.md) — L3 → L4 evolution
- [`docs/cognitive/skill_evolution.md`](../../../docs/cognitive/skill_evolution.md) — Full pipeline overview
- [`docs/cognitive/verification_doctrine.md`](../../../docs/cognitive/verification_doctrine.md) — Verification requirements
- [`docs/cognitive/memory_ontology.md`](../../../docs/cognitive/memory_ontology.md) — Memory layer definitions

---

*The L1 → L2 transition is where noise becomes signal. The discipline applied
here—minimum thresholds, cross-session validation, environmental stability,
governance review—determines the quality of everything that follows. A system
built on unreliable instincts produces unreliable skills and dangerous
strategies.*
