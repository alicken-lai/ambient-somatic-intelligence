# Memory Ontology

> Ambient OS v0.3.1-alpha — Formal Memory Layer Definitions

---

## 1. Purpose

This document defines the formal ontology for Ambient OS's 4-layer cognitive
memory hierarchy and its mapping to the existing 6-layer storage engine. The
ontology governs how knowledge is classified, retained, promoted, and decayed
across the system.

---

## 2. Layer Definitions

### L1 — Raw Episodic Memory

**Content types**:
- Sessions (agent interactions, tool invocations, user exchanges)
- Logs (system events, daemon output, error traces)
- Sensor events (`SensorEpisode`: 20-field dataclass including severity, signal types, environmental signature)
- Transcripts (conversation history, decision rationale)
- Execution traces (`ExecutionTracer` spans with timing, status, parent-child relationships)

**Properties**:
| Property | Value |
|---|---|
| Granularity | Individual, unprocessed events |
| Mutability | Append-only (per AGENTS.md mandate) |
| Retention | TTL-governed; eviction by age or capacity |
| Confidence | Not applicable (raw data has no confidence score) |
| Governance | None required for capture; append-only guarantee |

**Storage mapping**: `episodic` (TTL 30d, decay half-life 7d), `scratchpad` (TTL 24h, decay half-life 12h)

### L2 — Instinct Memory

**Content types**:
- Atomic reusable observations (single, self-contained insights)
- Trigger rules (condition → action mappings)
- Contextual applicability metadata (environment, domain, platform constraints)

**Properties**:
| Property | Value |
|---|---|
| Granularity | Single observation or rule |
| Mutability | Confidence can be updated; content is immutable once created |
| Retention | Confidence-gated; decays on inactivity or contradiction |
| Confidence | Required; initialized on creation, updated on reuse |
| Governance | Verification required before creation from L1 |

**Examples**:

| Instinct | Domain | Confidence |
|---|---|---|
| "Validate input schema before processing external payloads" | Software engineering | 0.92 |
| "Repeated vibration anomaly at 2.3 Hz precedes bearing failure" | Industrial sensing | 0.78 |
| "Thermal drift above 3°C/min correlates with memory pressure" | System monitoring | 0.85 |
| "API rate limits reset at UTC midnight, not local midnight" | Integration | 0.95 |
| "Process restart within 60s of OOM indicates memory leak, not transient spike" | Operations | 0.88 |

**Storage mapping**: `semantic` (TTL 365d, decay half-life 180d), `procedural` (TTL 180d, decay half-life 30d)

### L3 — Skill Memory

**Content types**:
- Clustered workflows (multi-step procedures assembled from validated instincts)
- Reusable procedures (typed inputs/outputs via `SkillSchema`)
- Compound operational patterns (sequences of tool invocations with governance metadata)

**Properties**:
| Property | Value |
|---|---|
| Granularity | Multi-step procedure with formal schema |
| Mutability | Versioned; new versions require governance approval |
| Retention | Usage-metric-gated; success rate and frequency tracked |
| Confidence | Composite of constituent instincts + execution history |
| Governance | Registration requires `SkillRegistrationPipeline.approve()` |

**Formal structure** (from `skills/core/skill_schema.py`):

```
SkillSchema:
  name: str                      # unique identifier
  description: str               # human-readable purpose
  version: str                   # semantic version
  inputs: list[SkillInput]       # typed input parameters
  outputs: list[SkillOutput]     # typed output parameters
  metadata: SkillMetadata        # tags, governance level, resource requirements
  governance_level: GovernanceLevel  # ALLOW / REVIEW_REQUIRED / BLOCK_WITHOUT_APPROVAL
```

**Storage mapping**: `procedural` (TTL 180d, decay half-life 30d), `semantic` (TTL 365d, decay half-life 180d)

### L4 — Strategic Memory

**Content types**:
- Decision heuristics (abstract rules guiding choice between alternatives)
- Metacognitive rules (rules about how to apply other rules)
- Routing philosophies (principles governing attention allocation and escalation)
- Escalation principles (criteria for when to involve human operators)

**Properties**:
| Property | Value |
|---|---|
| Granularity | Abstract principle, cross-domain applicability |
| Mutability | Highest governance bar for modification |
| Retention | Longest-lived; archived for historical reference even after retirement |
| Confidence | Highest threshold required for promotion |
| Governance | Highest-level: independent verification + cross-project validation + governance approval |

**Storage mapping**: `governance` (TTL 365d, decay half-life 90d), `archive` (TTL 3650d, decay half-life 365d)

---

## 3. Confidence Tracking Rules

### Initialization

When an instinct is first distilled from L1 episodic data, its confidence is
initialized based on:

| Factor | Weight | Description |
|---|---|---|
| Occurrence frequency | 0.30 | How often the pattern was observed |
| Success rate | 0.35 | Proportion of occurrences that led to positive outcomes |
| Consistency | 0.20 | Low variance across occurrences |
| Breadth | 0.15 | Number of distinct contexts in which the pattern appeared |

These weights align with the `skill_potential` scoring in
`agents/skillify/workflow_cluster.py`.

### Update Rules

- **Successful reuse**: Confidence increases by `min(0.05, (1.0 - current) * 0.1)`
- **Failed reuse**: Confidence decreases by `max(0.05, current * 0.1)`
- **Contradiction**: Confidence immediately drops by 0.20 and triggers review
- **Cross-context validation**: Successful use in a new context provides a `0.10` boost

### Confidence Thresholds

| Threshold | Value | Effect |
|---|---|---|
| Minimum retention | 0.30 | Below this, instinct is marked for decay |
| Skill promotion eligible | 0.70 | Minimum confidence for L2 → L3 promotion |
| Strategy promotion eligible | 0.90 | Minimum confidence for L3 → L4 promotion |
| Governance bypass (ALLOW-level only) | 0.95 | May skip REVIEW_REQUIRED gate for ALLOW-level operations |

---

## 4. Promotion Conditions

Promotion from a lower layer to a higher layer requires meeting **all**
applicable conditions:

### L1 → L2 (Episodic → Instinct)

1. **Repeated validation**: Pattern observed at least `min_support` times (configurable in `SkillifyPatternMiner`, default varies by domain)
2. **Cross-session stability**: Pattern must appear across multiple independent sessions
3. **Environmental consistency**: Pattern must hold across the relevant environmental signature bands
4. **Verifier acknowledgment**: An independent verification step confirms the observation is not an artifact

### L2 → L3 (Instinct → Skill)

1. **Confidence threshold**: Constituent instincts must each meet the 0.70 minimum
2. **Cluster validation**: Instincts must form a coherent cluster (similarity ≥ threshold in `WorkflowCluster`)
3. **Candidate validation**: Must pass `SkillCandidateValidator` checks (min_support=3, min_success_rate=0.70)
4. **Governance review**: Must be proposed through `SkillRegistrationPipeline` and approved by a reviewer
5. **No auto-registration**: Skillify may propose but never directly register

### L3 → L4 (Skill → Strategy)

1. **Cross-project validation**: Pattern must succeed across multiple distinct projects or domains
2. **High confidence**: Minimum 0.90 confidence across all constituent skills
3. **Independent verifier approval**: A verifier separate from the implementing agent must approve
4. **Highest governance gate**: Must pass the most stringent governance review
5. **Reversibility confirmed**: A rollback path must exist before promotion is finalized

---

## 5. Decay Conditions

Knowledge decays when it fails to demonstrate continued relevance.

### Contradiction

New evidence directly invalidates an existing instinct, skill, or strategy.
Contradiction triggers:
- Immediate confidence reduction (−0.20)
- Flagging for governance review
- If confidence drops below retention threshold (0.30), the entry is evicted

### Inactivity

Extended period without access or successful reuse. Decay follows per-layer
half-lives defined in `memory/memory_kernel.py`:

| Storage Layer | Half-life | Cognitive Layer |
|---|---|---|
| `scratchpad` | 12 hours | L1 |
| `episodic` | 7 days | L1 |
| `procedural` | 30 days | L2 / L3 |
| `semantic` | 180 days | L2 / L3 |
| `governance` | 90 days | L4 |
| `archive` | 365 days | L4 |

### Failed Reuse

Repeated application failures reduce confidence. Three consecutive failures
at the same confidence level trigger an immediate review. If the review does
not restore confidence, the entry decays to the next lower layer or is evicted.

---

## 6. Mapping to Existing 6-Layer Storage

The cognitive ontology (4 layers) maps onto the existing storage engine
(6 layers) as follows:

```
Cognitive Layer    Storage Layer(s)           TTL        Layer Weight
─────────────────────────────────────────────────────────────────────
L1 Episodic        episodic                   30 days    1.0
                   scratchpad                 24 hours   0.2

L2 Instinct        semantic                   365 days   2.0
                   procedural                 180 days   1.6

L3 Skill           procedural                 180 days   1.6
                   semantic                   365 days   2.0

L4 Strategic       governance                 365 days   1.3
                   archive                    3650 days  0.1
```

The `layer_weight` values (from `memory/memory_kernel.py`) influence recall
scoring. Higher weights mean the Memory Kernel preferentially surfaces
knowledge from those storage layers when computing relevance scores.

Note that L2 and L3 share `semantic` and `procedural` storage layers. The
distinction between instincts and skills is maintained through metadata tagging
and schema structure, not through separate storage backends.

---

## 7. Related Documents

- [`somatic_metacognition_spec_v1.md`](./somatic_metacognition_spec_v1.md) — Master specification
- [`strategic_memory.md`](./strategic_memory.md) — Strategic memory architecture
- [`verification_doctrine.md`](./verification_doctrine.md) — Guardian Verification Doctrine
- [`skill_evolution.md`](./skill_evolution.md) — Skill evolution pipeline

---

*This ontology is the authoritative definition for memory classification in
Ambient OS. All subsystems that create, promote, or decay knowledge must conform
to these definitions.*
