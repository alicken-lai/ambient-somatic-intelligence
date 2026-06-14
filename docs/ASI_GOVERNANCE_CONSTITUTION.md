# ASI Governance Constitution

## Purpose

Ambient Somatic Intelligence (ASI) is governed AI infrastructure. This document defines the repository-wide operating constitution for future contributors, agents, and reviewers.

This repository must prioritize stability, auditability, replayability, governance, and long-term memory integrity over feature velocity, novelty, complexity, or experimentation without controls.

## Project Vision

ASI is not a chatbot project. It is an experimental platform for Ambient OS, somatic intelligence, memory governance, environmental sensing, replayable execution, auditable agent systems, local AI infrastructure, and human-AI governance.

The project exists to make AI systems safer, more accountable, more replayable, and more governable, not merely more autonomous.

## Governance Principles

1. Core governance systems are more important than new features.
2. Experimental technologies must enter through experimental layers first.
3. Experimental components must not directly modify governance behavior.
4. Memory is structured experience, not chat history.
5. Vector recall is evidence, not truth.
6. Guardian decisions must never depend solely on vector similarity.
7. Every important decision must be replayable.
8. Every memory transformation must be auditable.
9. Cross-node synchronization must be local first, minimum disclosure, interruptible, and replayable.
10. Any change that increases capability while reducing control is a regression.

## Protected Zones

The following areas are protected by default and should be treated as frozen unless a governed change path is followed:

- `guardian/`
- `governance/`
- `replay/`
- `runtime/`
- `kernel/`
- `dmn_scoring/`
- `memory_promotion/`
- `agent_decision_policy/`

Protected-zone changes require:

1. A clearly defined purpose.
2. Tests or objective verification evidence.
3. A rollback plan.
4. A decision log entry.
5. Memory compatibility analysis.
6. Guardian safety review.

## Experimental Zones

New infrastructure starts in experimental or documentation zones:

- `experiments/`
- `memory/vector/`
- `adapters/`
- `docs/`
- `tests/`
- `prototypes/`

Experimental work must remain bounded. It may gather evidence, produce candidate designs, or validate assumptions. It must not silently change production behavior, Guardian decisions, memory promotion, or runtime execution.

## Memory Philosophy

Memory is an auditable system of structured experience. It is not equivalent to transcript storage and must not be treated as a raw dump of conversation history.

Memory records should preserve:

- The source of the observation.
- The reason for retention.
- Confidence or uncertainty.
- Replay references where available.
- Governance state and review context.

Memory promotion must be earned through governed criteria. Strategic memory must not be injected ad hoc.

## Replay Philosophy

Important decisions must be reconstructable. Replay is the ability to explain what happened, why it happened, what evidence existed at the time, what memory was recalled, and which governance rule applied.

Replay artifacts must preserve failures, gaps, uncertainty, and rejected paths. Auditability is weakened when the repository only records successful outcomes.

## Guardian Philosophy

Guardian is the safety review and boundary-enforcement layer. Guardian is not an automation accelerator and must not be bypassed for convenience.

Guardian decisions must remain explainable, conservative, and independent from any single evidence source. Vector similarity, local heuristics, or generated analysis may inform Guardian review, but they must not become sole authority for action.

## TurboVec Policy

TurboVec is approved only as compressed vector recall infrastructure.

TurboVec is not:

- DMN Memory.
- Guardian.
- Governance.
- A source of truth.
- A decision layer.

TurboVec may store embeddings efficiently and retrieve candidate memories efficiently. It may produce candidate recall. It must not trigger autonomous action or directly modify Guardian behavior.

TurboVec adoption must follow the approved integration plan in `docs/TURBOVEC_INTEGRATION_PLAN.md`.

## Synchronization Policy

Cross-node synchronization must be local first, minimum disclosure, interruptible, and replayable.

Synchronization may include:

- Summaries.
- Embeddings or embedding references.
- Anomaly tags.
- Confidence values.
- Replay references.
- Governance metadata.

Synchronization must avoid raw audio, personal identifiers, sensitive information, full sensor streams, and unnecessary raw data replication.

## Escalation Policy

Escalate when a change:

- Touches a protected zone.
- Changes runtime behavior.
- Changes Guardian logic.
- Changes memory scoring or promotion behavior.
- Introduces new dependencies.
- Expands external data flow.
- Increases autonomy or action capability.
- Reduces replayability, auditability, or human control.

Escalated changes require a decision log entry, rollback plan, test or verification evidence, and approval according to `docs/PR_REVIEW_GATE.md`.
