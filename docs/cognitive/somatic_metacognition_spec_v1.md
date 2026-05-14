# Somatic Metacognition Specification v1

> Ambient OS v0.3.1-alpha — Cognitive Doctrine Master Document

---

## 1. Overview

Ambient OS is a locally-running cognitive operating system that augments human
operators through persistent memory, environmental awareness, and disciplined
skill evolution. Its cognitive doctrine is grounded in **bounded adaptive
cognition**: the system becomes smarter through disciplined memory consolidation
and governed skill promotion—not through larger context windows or unbounded
accumulation.

This specification defines the **4-layer memory ontology**, the **7 cognitive
operations** that transform raw experience into reusable knowledge, and the
governance principles that ensure every transformation is auditable, reversible,
and independently verified.

### Core Philosophy — Bounded Adaptive Cognition

Traditional LLM-based systems rely on ever-growing context to maintain
coherence. Ambient OS rejects this approach. Instead, it employs a tiered memory
architecture where raw experience is progressively distilled into higher-order
knowledge through explicit promotion gates. Each promotion requires independent
verification and governance approval. Knowledge that fails to prove its worth
decays naturally.

The result is a system whose effective intelligence grows through the *quality*
of its retained knowledge, not the *quantity* of its stored data.

---

## 2. The 4-Layer Memory Hierarchy

The cognitive ontology defines four layers of progressively abstract knowledge.
Each layer has distinct storage semantics, lifecycle rules, and governance
requirements.

### L1 — Raw Episodic Memory

| Property | Value |
|---|---|
| **Content** | Sessions, logs, sensor events, transcripts, execution traces |
| **Granularity** | Individual events, raw and unprocessed |
| **Lifecycle** | Short-lived; subject to TTL-based eviction |
| **Governance** | Append-only; no promotion gate required for capture |

L1 is the ground truth of the system. Every interaction, every sensor reading,
every execution trace begins here. L1 data is high-volume and ephemeral—it
exists to be observed and consolidated, not to be retained indefinitely.

**Maps to existing storage layers**: `episodic` (TTL 30d), `scratchpad` (TTL 24h)

### L2 — Instinct Memory

| Property | Value |
|---|---|
| **Content** | Atomic reusable observations, trigger rules, contextual applicability |
| **Granularity** | Single, self-contained insights with confidence scores |
| **Lifecycle** | Medium-lived; confidence-gated retention |
| **Governance** | Requires verification before promotion from L1 |

Instincts are the first level of distilled knowledge. An instinct captures a
single, atomic observation that has been validated through repeated occurrence
or cross-context verification. Each instinct carries a confidence score that
determines its retention and eligibility for further promotion.

Examples:
- "Validate input schema before processing external payloads"
- "Repeated vibration anomaly at 2.3 Hz precedes bearing failure"
- "Thermal drift above 3°C/min correlates with memory pressure"

**Maps to existing storage layers**: `semantic` (TTL 365d), `procedural` (TTL 180d)

### L3 — Skill Memory

| Property | Value |
|---|---|
| **Content** | Clustered workflows, reusable procedures, compound operational patterns |
| **Granularity** | Multi-step procedures with typed inputs/outputs |
| **Lifecycle** | Long-lived; governed by usage metrics and validation history |
| **Governance** | Requires governance gate for registration |

Skills are structured, reusable procedures assembled from validated instincts.
A skill has a formal schema (`SkillSchema`), typed inputs and outputs, metadata
for routing, and a governance classification. Skills are the primary unit of
operational capability in Ambient OS.

**Maps to existing storage layers**: `procedural` (TTL 180d), `semantic` (TTL 365d)

### L4 — Strategic Memory

| Property | Value |
|---|---|
| **Content** | Decision heuristics, metacognitive rules, routing philosophies, escalation principles |
| **Granularity** | Abstract principles applicable across domains and contexts |
| **Lifecycle** | Long-lived; highest governance requirements for modification |
| **Governance** | Requires highest-level verification and governance approval |

Strategic memory represents the system's accumulated wisdom—abstract principles
that guide decision-making across all domains. Strategic rules are derived from
patterns observed across multiple skills, projects, and contexts. They influence
routing, escalation, and resource allocation at the system level.

**Maps to existing storage layers**: `governance` (TTL 365d), `archive` (TTL 3650d)

---

## 3. The 7 Cognitive Operations

These operations define how knowledge flows through the 4-layer hierarchy.

### 3.1 Capture

**Direction**: External → L1

Raw events enter the system through sensors, agent interactions, and execution
traces. Capture is append-only and ungated—every event is recorded faithfully.

**Implementation touchpoints**:
- `memory/somatic/sensor_episode.py` — `SensorEpisode` (20-field dataclass)
- `memory/somatic/somatic_episode_store.py` — `SomaticEpisodeStore` (JSONL-backed, max 10,000 episodes)
- `agents/skillify/workflow_observer.py` — `WorkflowObserver` (observations.jsonl)
- `observability/execution_tracer.py` — `ExecutionTracer` (OpenTelemetry-inspired spans)

### 3.2 Consolidate

**Direction**: L1 → L1 (internal)

Related episodic events are grouped and indexed for efficient retrieval. The
Memory Kernel's 6-dimension scoring enables relevance-based consolidation:

| Dimension | Weight |
|---|---|
| `semantic_overlap` | 0.30 |
| `tag_match` | 0.20 |
| `exact_match` | 0.15 |
| `recency_decay` | 0.15 |
| `access_frequency` | 0.10 |
| `content_quality` | 0.10 |

**Implementation touchpoints**:
- `memory/memory_kernel.py` — `MemoryKernel.recall()`, `ScoringWeights`
- `memory/somatic/pattern_similarity.py` — `PatternSimilarity` (5-factor weighted clustering)

### 3.3 Distill

**Direction**: L1 → L2

Repeated or significant patterns in episodic memory are extracted as candidate
instincts. Distillation requires meeting minimum occurrence thresholds and
demonstrating cross-session stability.

**Implementation touchpoints**:
- `agents/skillify/pattern_miner.py` — `SkillifyPatternMiner.mine()` (min_support threshold)
- `memory/somatic/precursor_matcher.py` — `PrecursorMatcher` (type 0.70 + env 0.30 scoring)

### 3.4 Promote

**Direction**: L2 → L3 → L4

Validated knowledge advances to higher layers through explicit governance gates.
Promotion conditions include:

- **L2 → L3**: Confidence threshold met, cross-session validation passed, governance review approved
- **L3 → L4**: Cross-project validation, independent verifier approval, highest governance gate

Each promotion is logged, auditable, and reversible.

**Implementation touchpoints**:
- `agents/skillify/skill_registration_pipeline.py` — `SkillRegistrationPipeline` (propose → approve → register)
- `governance/mandatory_gate.py` — `MandatoryGate` (unified policy enforcement)
- `governance/execution_validator.py` — `ExecutionValidator` (4-stage validation pipeline)

### 3.5 Decay

**Direction**: Any layer → lower layer or eviction

Knowledge that fails to prove its continued relevance decays naturally. Decay
conditions include:

- **Contradiction**: New evidence invalidates an existing instinct or skill
- **Inactivity**: Extended period without access or successful reuse
- **Failed reuse**: Repeated application failures reduce confidence below retention threshold

Decay is governed by per-layer half-lives:

| Layer | Half-life |
|---|---|
| `scratchpad` (L1) | 12 hours |
| `episodic` (L1) | 7 days |
| `procedural` (L2/L3) | 30 days |
| `governance` (L4) | 90 days |
| `semantic` (L2/L3) | 180 days |
| `archive` (L4) | 365 days |

**Implementation touchpoints**:
- `memory/memory_kernel.py` — `DECAY_HALF_LIVES`, `_apply_recency_decay()`

### 3.6 Verification

**Direction**: Cross-cutting (all promotions)

Every promotion requires independent verification. The **Guardian Verification
Doctrine** mandates that an implementer cannot self-certify its own output. A
separate verifier must confirm the validity, safety, and correctness of the
promoted knowledge.

See: [`verification_doctrine.md`](./verification_doctrine.md)

**Implementation touchpoints**:
- `governance/execution_validator.py` — `ExecutionValidator` (4-stage pipeline: policy → anomaly → resource → injection)
- `governance/mandatory_gate.py` — `MandatoryGate` (single entry point)
- `governance/anomaly_detector.py` — `AnomalyDetector` (failure loops, rate limits, repetition detection)

### 3.7 Self-Reference

**Direction**: L4 → cognitive operations (feedback loop)

Strategic memory influences how the cognitive operations themselves behave.
Routing philosophies stored in L4 can adjust salience weights, escalation
thresholds, and promotion criteria. This is the metacognitive feedback loop—the
system's ability to reason about its own reasoning.

**Implementation touchpoints**:
- `attention/salience_engine.py` — `SalienceEngine` (9-factor scoring, adjustable weights)
- `attention/escalation_router.py` — `EscalationRouter` (threshold-based routing: ATTEND/DEFER/ESCALATE/THROTTLE/IGNORE)
- `attention/priority_allocator.py` — `PriorityAllocator` (domain budget allocation)

---

## 4. Governance Integration Principles

Every cognitive operation that modifies knowledge above L1 must pass through
governance gates. This is not optional—it is a constitutional requirement of
Ambient OS (see `AGENTS.md`).

### Mandatory Gate Pipeline

All actions flow through `MandatoryGate`, which combines:

1. **ExecutionValidator** — 4-stage policy + anomaly + resource + injection check
2. **ToolPermissionMatrix** — Role-based tool access (ALLOWED/DENIED/REQUIRES_REVIEW)
3. **GovernanceAuditLog** — Append-only audit trail (decisions.jsonl + incidents.jsonl)

### Risk Classification

| Level | Value | Implication |
|---|---|---|
| `ALLOW` | 0 | Proceed without review |
| `REVIEW_REQUIRED` | 1 | Human or verifier must approve |
| `BLOCK` | 2 | Action prohibited |

### Governance at Each Layer Transition

| Transition | Gate Requirement |
|---|---|
| L1 → L2 (Distill) | Minimum: pattern verification |
| L2 → L3 (Promote to Skill) | Required: governance review + `SkillRegistrationPipeline.approve()` |
| L3 → L4 (Promote to Strategy) | Required: highest-level governance + independent verifier + cross-project validation |

---

## 5. Bounded Adaptive Cognition Philosophy

### Principles

1. **Finite capacity, infinite discipline.** The system operates within bounded
   storage and attention budgets. Intelligence grows through the quality of
   retained knowledge, not through accumulation.

2. **Promotion over accumulation.** Raw data is not hoarded—it is either
   promoted to a higher layer of abstraction or allowed to decay.

3. **Every promotion is earned.** Knowledge advances only through demonstrated
   value, independent verification, and governance approval.

4. **Decay is healthy.** Knowledge that fails to prove its worth is naturally
   forgotten. This prevents stale or contradicted knowledge from polluting
   higher layers.

5. **Metacognition is bounded.** The system reasons about its own reasoning
   through L4 strategic rules, but this self-reference is itself governed and
   auditable. There are no unbounded recursive loops.

6. **Safety first, always.** Per `AGENTS.md`: never execute destructive
   commands, ask Guardian before external actions, all actions are logged,
   memory is append-only at the capture layer.

---

## 6. Cross-Reference Map

| Module | Path | Role in Cognitive Architecture |
|---|---|---|
| Memory Kernel | `memory/memory_kernel.py` | 6-layer storage engine, scoring, decay |
| Somatic Subsystem | `memory/somatic/` | Environmental episodic memory (L1) |
| Skill Schemas | `skills/core/` | Skill definition, registry, routing, validation |
| Skillify Pipeline | `agents/skillify/` | Skill discovery and evolution (L1→L2→L3) |
| Salience Engine | `attention/salience_engine.py` | 9-factor attention scoring |
| Priority Allocator | `attention/priority_allocator.py` | Finite budget allocation |
| Escalation Router | `attention/escalation_router.py` | Threshold-based routing |
| Mandatory Gate | `governance/mandatory_gate.py` | Unified governance entry point |
| Execution Validator | `governance/execution_validator.py` | 4-stage validation pipeline |
| Policy Engine | `governance/policy_engine.py` | 10+ built-in policies |
| Anomaly Detector | `governance/anomaly_detector.py` | Behavioral anomaly detection |
| Audit Log | `governance/audit_log.py` | Append-only decision trail |
| Execution Tracer | `observability/execution_tracer.py` | OpenTelemetry-inspired tracing |
| Agent Telemetry | `observability/agent_telemetry.py` | Per-agent profiling |
| System Report | `observability/system_report.py` | Aggregated health reporting |

---

## 7. Related Documents

- [`memory_ontology.md`](./memory_ontology.md) — Formal memory layer definitions and mapping
- [`strategic_memory.md`](./strategic_memory.md) — Strategic memory architecture
- [`verification_doctrine.md`](./verification_doctrine.md) — Guardian Verification Doctrine
- [`skill_evolution.md`](./skill_evolution.md) — Skill evolution pipeline
- [`agents/skillify/doctrine/`](../../agents/skillify/doctrine/) — Skillify evolution doctrine

---

*This document is the master specification for Ambient OS cognitive architecture.
All cognitive subsystems must conform to the principles defined herein.*
