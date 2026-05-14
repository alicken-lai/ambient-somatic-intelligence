"""
Replay Engine — Design for replaying system execution from traces.

Provides the data model and planning infrastructure for replaying causal
chains, exporting/importing traces, capturing snapshots, and diffing
execution paths. This is the structural foundation; full replay execution
is deferred to a future phase.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from observability.cognitive_trace_v2.causal_trace_schema import (
    CausalChain,
    CausalEvent,
    CausalEventType,
)
from observability.cognitive_trace_v2.decision_provenance import DecisionProvenanceTracker
from observability.cognitive_trace_v2.execution_lineage import ExecutionLineageTracer

logger = logging.getLogger(__name__)


@dataclass
class ReplaySnapshot:
    snapshot_id: str
    timestamp: float
    system_state: dict[str, Any]
    active_agents: list[str]
    memory_summary: dict[str, Any]
    governance_state: dict[str, Any]
    attention_level: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "system_state": self.system_state,
            "active_agents": self.active_agents,
            "memory_summary": self.memory_summary,
            "governance_state": self.governance_state,
            "attention_level": self.attention_level,
        }


@dataclass
class ReplayStep:
    step_index: int
    event: CausalEvent
    action: str
    requires: list[str]
    can_simulate: bool
    side_effects: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "event_id": self.event.event_id,
            "event_type": self.event.event_type.value,
            "action": self.action,
            "requires": self.requires,
            "can_simulate": self.can_simulate,
            "side_effects": self.side_effects,
        }


@dataclass
class ReplayPlan:
    plan_id: str
    chain_id: str
    steps: list[ReplayStep]
    required_state: dict[str, Any]
    estimated_duration_ms: float
    feasible: bool
    blockers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "chain_id": self.chain_id,
            "steps": [s.to_dict() for s in self.steps],
            "required_state": self.required_state,
            "estimated_duration_ms": self.estimated_duration_ms,
            "feasible": self.feasible,
            "blockers": self.blockers,
        }


@dataclass
class ReplayValidation:
    valid: bool
    missing_state: list[str]
    missing_events: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "missing_state": self.missing_state,
            "missing_events": self.missing_events,
            "warnings": self.warnings,
        }


@dataclass
class ExecutionDiff:
    chain_a_id: str
    chain_b_id: str
    common_events: int
    divergence_point: str | None
    a_only_events: list[str]
    b_only_events: list[str]
    outcome_diff: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_a_id": self.chain_a_id,
            "chain_b_id": self.chain_b_id,
            "common_events": self.common_events,
            "divergence_point": self.divergence_point,
            "a_only_events": self.a_only_events,
            "b_only_events": self.b_only_events,
            "outcome_diff": self.outcome_diff,
        }


_SIMULATABLE_TYPES: set[CausalEventType] = {
    CausalEventType.GOVERNANCE_CHECK,
    CausalEventType.GOVERNANCE_DECISION,
    CausalEventType.MEMORY_RECALL,
    CausalEventType.CONTEXT_ASSEMBLY,
    CausalEventType.CONTEXT_INJECTION,
    CausalEventType.ENTROPY_ASSESSMENT,
    CausalEventType.ISOLATION_CHECK,
    CausalEventType.ATTENTION_CHANGE,
    CausalEventType.DRIFT_DETECTION,
}

_SIDE_EFFECT_MAP: dict[CausalEventType, list[str]] = {
    CausalEventType.TASK_DISPATCH: ["task_queue"],
    CausalEventType.TASK_EXECUTION: ["agent_state", "file_system"],
    CausalEventType.TASK_COMPLETION: ["task_queue", "metrics"],
    CausalEventType.MEMORY_STORE: ["memory_layers"],
    CausalEventType.SIGNAL_EMISSION: ["signal_bus"],
    CausalEventType.BUS_EVENT: ["event_bus"],
    CausalEventType.AGENT_DECISION: ["agent_state"],
    CausalEventType.FEEDBACK_DETECTION: ["feedback_state"],
}


class ReplayEngine:

    def __init__(
        self,
        lineage_tracer: ExecutionLineageTracer,
        provenance_tracker: DecisionProvenanceTracker,
    ) -> None:
        self._lineage = lineage_tracer
        self._provenance = provenance_tracker
        self._snapshots: list[ReplaySnapshot] = []

    def capture_snapshot(self) -> ReplaySnapshot:
        active_traces = self._lineage.get_active_traces()
        event_count = self._lineage.event_count()
        decision_count = self._provenance.decision_count()

        snapshot = ReplaySnapshot(
            snapshot_id=uuid.uuid4().hex,
            timestamp=time.time(),
            system_state={
                "event_count": event_count,
                "decision_count": decision_count,
                "active_trace_count": len(active_traces),
            },
            active_agents=_extract_active_agents(self._lineage, active_traces),
            memory_summary={"total_events": event_count},
            governance_state={"decisions_tracked": decision_count},
            attention_level="normal",
        )
        self._snapshots.append(snapshot)

        logger.debug("Captured snapshot %s events=%d", snapshot.snapshot_id, event_count)
        return snapshot

    def build_replay_plan(self, chain_id: str) -> ReplayPlan:
        chain = self._lineage.get_chain(chain_id)
        if chain is None:
            return ReplayPlan(
                plan_id=uuid.uuid4().hex,
                chain_id=chain_id,
                steps=[],
                required_state={},
                estimated_duration_ms=0.0,
                feasible=False,
                blockers=[f"Chain {chain_id} not found"],
            )

        steps: list[ReplayStep] = []
        required_state: dict[str, Any] = {}
        blockers: list[str] = []
        total_estimated_ms = 0.0

        for idx, event in enumerate(chain.events):
            requires = [event.parent_event_id] if event.parent_event_id else []
            can_simulate = event.event_type in _SIMULATABLE_TYPES
            side_effects = _SIDE_EFFECT_MAP.get(event.event_type, [])

            if not can_simulate and event.event_type == CausalEventType.TASK_EXECUTION:
                blockers.append(f"Step {idx}: task execution cannot be auto-replayed (event {event.event_id[:12]})")

            step = ReplayStep(
                step_index=idx,
                event=event,
                action=event.action,
                requires=[r for r in requires if r],
                can_simulate=can_simulate,
                side_effects=side_effects,
            )
            steps.append(step)
            total_estimated_ms += event.duration_ms or 1.0

        for subsystem in chain.subsystems_involved:
            required_state[subsystem] = "initialized"

        feasible = len(blockers) == 0

        plan = ReplayPlan(
            plan_id=uuid.uuid4().hex,
            chain_id=chain_id,
            steps=steps,
            required_state=required_state,
            estimated_duration_ms=total_estimated_ms,
            feasible=feasible,
            blockers=blockers,
        )

        logger.debug(
            "Built replay plan %s steps=%d feasible=%s blockers=%d",
            plan.plan_id, len(steps), feasible, len(blockers),
        )
        return plan

    def validate_replay(self, plan: ReplayPlan) -> ReplayValidation:
        missing_state: list[str] = []
        missing_events: list[str] = []
        warnings: list[str] = []

        for subsystem, requirement in plan.required_state.items():
            if requirement == "initialized":
                pass

        seen_ids: set[str] = set()
        for step in plan.steps:
            seen_ids.add(step.event.event_id)
            for req_id in step.requires:
                if req_id not in seen_ids:
                    existing = self._lineage.get_event(req_id)
                    if existing is None:
                        missing_events.append(req_id)

            if not step.can_simulate:
                warnings.append(
                    f"Step {step.step_index} ({step.event.event_type.value}) "
                    f"cannot be simulated — requires manual intervention"
                )

        valid = len(missing_state) == 0 and len(missing_events) == 0

        return ReplayValidation(
            valid=valid,
            missing_state=missing_state,
            missing_events=missing_events,
            warnings=warnings,
        )

    def export_trace(self, chain_id: str, format: str = "jsonl") -> str:
        chain = self._lineage.get_chain(chain_id)
        if chain is None:
            raise ValueError(f"Chain {chain_id} not found")

        if format == "jsonl":
            lines = [json.dumps(e.to_dict(), ensure_ascii=False) for e in chain.events]
            return "\n".join(lines)
        elif format == "json":
            return json.dumps(chain.to_dict(), ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_trace(self, data: str, format: str = "jsonl") -> CausalChain:
        if format == "jsonl":
            events: list[CausalEvent] = []
            for line in data.strip().split("\n"):
                if line.strip():
                    event_dict = json.loads(line)
                    events.append(CausalEvent.from_dict(event_dict))
        elif format == "json":
            chain_dict = json.loads(data)
            events = [CausalEvent.from_dict(e) for e in chain_dict.get("events", [])]
        else:
            raise ValueError(f"Unsupported format: {format}")

        if not events:
            raise ValueError("No events found in imported data")

        root = events[0]
        return CausalChain.from_events(
            chain_id=root.root_event_id or root.event_id,
            root=root,
            events=events,
            outcome=root.outcome or "imported",
        )

    def diff_executions(self, chain_a_id: str, chain_b_id: str) -> ExecutionDiff:
        chain_a = self._lineage.get_chain(chain_a_id)
        chain_b = self._lineage.get_chain(chain_b_id)

        if chain_a is None or chain_b is None:
            missing = []
            if chain_a is None:
                missing.append(chain_a_id)
            if chain_b is None:
                missing.append(chain_b_id)
            raise ValueError(f"Chain(s) not found: {', '.join(missing)}")

        a_types = [(e.event_type, e.source_subsystem, e.action) for e in chain_a.events]
        b_types = [(e.event_type, e.source_subsystem, e.action) for e in chain_b.events]

        common = 0
        divergence_point: str | None = None
        for i, (at, bt) in enumerate(zip(a_types, b_types)):
            if at == bt:
                common += 1
            else:
                divergence_event = chain_a.events[i] if i < len(chain_a.events) else chain_b.events[i]
                divergence_point = divergence_event.event_id
                break

        a_event_sigs = {(e.event_type, e.action) for e in chain_a.events}
        b_event_sigs = {(e.event_type, e.action) for e in chain_b.events}

        a_only = [
            e.event_id for e in chain_a.events
            if (e.event_type, e.action) not in b_event_sigs
        ]
        b_only = [
            e.event_id for e in chain_b.events
            if (e.event_type, e.action) not in a_event_sigs
        ]

        outcome_diff: dict[str, Any] = {
            "chain_a_outcome": chain_a.outcome,
            "chain_b_outcome": chain_b.outcome,
            "same_outcome": chain_a.outcome == chain_b.outcome,
            "chain_a_depth": chain_a.depth,
            "chain_b_depth": chain_b.depth,
            "chain_a_event_count": len(chain_a.events),
            "chain_b_event_count": len(chain_b.events),
        }

        return ExecutionDiff(
            chain_a_id=chain_a_id,
            chain_b_id=chain_b_id,
            common_events=common,
            divergence_point=divergence_point,
            a_only_events=a_only,
            b_only_events=b_only,
            outcome_diff=outcome_diff,
        )

    def get_snapshots(self) -> list[ReplaySnapshot]:
        return list(self._snapshots)


def _extract_active_agents(
    lineage: ExecutionLineageTracer,
    active_trace_ids: list[str],
) -> list[str]:
    agents: set[str] = set()
    for tid in active_trace_ids:
        descendants = lineage.get_descendants(tid)
        for event in descendants:
            if event.agent_id:
                agents.add(event.agent_id)
    return sorted(agents)
