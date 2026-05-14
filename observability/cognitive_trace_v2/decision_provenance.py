"""
Decision Provenance — Reconstruct WHY decisions were made.

Tracks governance decisions, agent routing, memory selection, and attention
shifts with full context: inputs, alternatives considered, chosen action,
and the reasoning path that led to the decision.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from observability.cognitive_trace_v2.causal_trace_schema import CausalEvent
from observability.cognitive_trace_v2.execution_lineage import ExecutionLineageTracer

logger = logging.getLogger(__name__)


@dataclass
class DecisionRecord:
    decision_id: str
    decision_type: str
    event_id: str
    agent_id: str | None
    task_id: str | None
    inputs: dict[str, Any]
    alternatives: list[dict[str, Any]]
    chosen: str
    reason: str
    confidence: float
    timestamp: float
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "inputs": self.inputs,
            "alternatives": self.alternatives,
            "chosen": self.chosen,
            "reason": self.reason,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class ReasoningStep:
    step_index: int
    subsystem: str
    action: str
    input_summary: str
    output_summary: str
    duration_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "subsystem": self.subsystem,
            "action": self.action,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "duration_ms": self.duration_ms,
        }


@dataclass
class ReasoningPath:
    decision_id: str
    steps: list[ReasoningStep]
    total_depth: int
    subsystems_consulted: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "steps": [s.to_dict() for s in self.steps],
            "total_depth": self.total_depth,
            "subsystems_consulted": self.subsystems_consulted,
        }


@dataclass
class DecisionProvenance:
    decision: DecisionRecord
    causal_chain: list[CausalEvent]
    prior_decisions: list[DecisionRecord]
    memory_context: list[dict[str, Any]]
    governance_context: dict[str, Any] | None
    full_lineage: list[CausalEvent]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "causal_chain_length": len(self.causal_chain),
            "prior_decisions_count": len(self.prior_decisions),
            "memory_context_count": len(self.memory_context),
            "has_governance_context": self.governance_context is not None,
            "full_lineage_length": len(self.full_lineage),
        }


class DecisionProvenanceTracker:

    def __init__(self, lineage_tracer: ExecutionLineageTracer) -> None:
        self._lineage = lineage_tracer
        self._decisions: dict[str, DecisionRecord] = {}
        self._by_event: dict[str, str] = {}
        self._by_type: dict[str, list[str]] = defaultdict(list)
        self._by_task: dict[str, list[str]] = defaultdict(list)
        self._decision_order: list[str] = []

    def record_decision(self, decision: DecisionRecord) -> str:
        self._decisions[decision.decision_id] = decision
        self._by_event[decision.event_id] = decision.decision_id
        self._by_type[decision.decision_type].append(decision.decision_id)
        if decision.task_id:
            self._by_task[decision.task_id].append(decision.decision_id)
        self._decision_order.append(decision.decision_id)

        logger.debug(
            "Recorded decision %s type=%s chosen=%s confidence=%.2f",
            decision.decision_id, decision.decision_type,
            decision.chosen, decision.confidence,
        )
        return decision.decision_id

    def get_provenance(self, decision_id: str) -> DecisionProvenance:
        decision = self._decisions.get(decision_id)
        if decision is None:
            raise ValueError(f"Decision {decision_id} not found")

        lineage = self._lineage.get_lineage(decision.event_id)

        prior_decisions: list[DecisionRecord] = []
        for event in lineage:
            linked_decision_id = self._by_event.get(event.event_id)
            if linked_decision_id and linked_decision_id != decision_id:
                linked = self._decisions.get(linked_decision_id)
                if linked:
                    prior_decisions.append(linked)

        memory_context: list[dict[str, Any]] = []
        for event in lineage:
            if event.event_type.value in ("memory_recall", "context_injection"):
                memory_context.append({
                    "event_id": event.event_id,
                    "action": event.action,
                    "payload": event.payload,
                })

        governance_context: dict[str, Any] | None = None
        for event in lineage:
            if event.event_type.value in ("governance_check", "governance_decision"):
                governance_context = {
                    "event_id": event.event_id,
                    "action": event.action,
                    "outcome": event.outcome,
                    "payload": event.payload,
                }
                break

        return DecisionProvenance(
            decision=decision,
            causal_chain=lineage,
            prior_decisions=prior_decisions,
            memory_context=memory_context,
            governance_context=governance_context,
            full_lineage=lineage,
        )

    def get_decision_chain(self, decision_id: str) -> list[DecisionRecord]:
        decision = self._decisions.get(decision_id)
        if decision is None:
            return []

        lineage = self._lineage.get_lineage(decision.event_id)
        chain: list[DecisionRecord] = []
        for event in lineage:
            linked_id = self._by_event.get(event.event_id)
            if linked_id:
                linked = self._decisions.get(linked_id)
                if linked:
                    chain.append(linked)
        return chain

    def get_decisions_by_type(self, decision_type: str) -> list[DecisionRecord]:
        ids = self._by_type.get(decision_type, [])
        return [self._decisions[did] for did in ids if did in self._decisions]

    def get_decisions_for_task(self, task_id: str) -> list[DecisionRecord]:
        ids = self._by_task.get(task_id, [])
        return [self._decisions[did] for did in ids if did in self._decisions]

    def reconstruct_reasoning(self, decision_id: str) -> ReasoningPath:
        decision = self._decisions.get(decision_id)
        if decision is None:
            raise ValueError(f"Decision {decision_id} not found")

        lineage = self._lineage.get_lineage(decision.event_id)
        steps: list[ReasoningStep] = []
        subsystems_seen: list[str] = []

        for idx, event in enumerate(lineage):
            step = ReasoningStep(
                step_index=idx,
                subsystem=event.source_subsystem,
                action=event.action,
                input_summary=_summarize_payload(event.payload),
                output_summary=event.outcome or "pending",
                duration_ms=event.duration_ms or 0.0,
            )
            steps.append(step)
            if event.source_subsystem not in subsystems_seen:
                subsystems_seen.append(event.source_subsystem)

        return ReasoningPath(
            decision_id=decision_id,
            steps=steps,
            total_depth=len(steps),
            subsystems_consulted=subsystems_seen,
        )

    def decision_count(self) -> int:
        return len(self._decisions)

    def get_decision(self, decision_id: str) -> DecisionRecord | None:
        return self._decisions.get(decision_id)


def _summarize_payload(payload: dict[str, Any], max_len: int = 120) -> str:
    if not payload:
        return "(empty)"
    parts = [f"{k}={v}" for k, v in list(payload.items())[:5]]
    summary = ", ".join(parts)
    if len(summary) > max_len:
        summary = summary[: max_len - 3] + "..."
    return summary
