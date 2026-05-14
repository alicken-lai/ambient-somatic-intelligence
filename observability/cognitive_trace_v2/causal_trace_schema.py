"""
Causal Trace Schema — Unified causal trace model linking ALL system events.

Every traceable event in Ambient OS conforms to the CausalEvent dataclass.
Events form directed acyclic graphs via parent_event_id / root_event_id,
enabling full causal reconstruction of any system behaviour.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CausalEventType(str, Enum):
    TASK_DISPATCH = "task_dispatch"
    TASK_EXECUTION = "task_execution"
    TASK_COMPLETION = "task_completion"
    GOVERNANCE_CHECK = "governance_check"
    GOVERNANCE_DECISION = "governance_decision"
    MEMORY_RECALL = "memory_recall"
    MEMORY_STORE = "memory_store"
    CONTEXT_ASSEMBLY = "context_assembly"
    CONTEXT_INJECTION = "context_injection"
    SIGNAL_EMISSION = "signal_emission"
    SIGNAL_HANDLING = "signal_handling"
    ATTENTION_CHANGE = "attention_change"
    BUS_EVENT = "bus_event"
    AGENT_DECISION = "agent_decision"
    ISOLATION_CHECK = "isolation_check"
    ENTROPY_ASSESSMENT = "entropy_assessment"
    FEEDBACK_DETECTION = "feedback_detection"
    DRIFT_DETECTION = "drift_detection"


@dataclass
class CausalEvent:
    event_id: str
    event_type: CausalEventType
    timestamp: float
    source_subsystem: str
    source_component: str
    action: str
    parent_event_id: str | None
    root_event_id: str | None
    generation: int
    agent_id: str | None
    task_id: str | None
    payload: dict[str, Any]
    outcome: str | None
    duration_ms: float | None
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "source_subsystem": self.source_subsystem,
            "source_component": self.source_component,
            "action": self.action,
            "parent_event_id": self.parent_event_id,
            "root_event_id": self.root_event_id,
            "generation": self.generation,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "payload": self.payload,
            "outcome": self.outcome,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CausalEvent:
        return cls(
            event_id=data["event_id"],
            event_type=CausalEventType(data["event_type"]),
            timestamp=data["timestamp"],
            source_subsystem=data["source_subsystem"],
            source_component=data["source_component"],
            action=data["action"],
            parent_event_id=data.get("parent_event_id"),
            root_event_id=data.get("root_event_id"),
            generation=data.get("generation", 0),
            agent_id=data.get("agent_id"),
            task_id=data.get("task_id"),
            payload=data.get("payload", {}),
            outcome=data.get("outcome"),
            duration_ms=data.get("duration_ms"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CausalChain:
    chain_id: str
    root_event: CausalEvent
    events: list[CausalEvent]
    depth: int
    total_duration_ms: float
    subsystems_involved: set[str]
    agents_involved: set[str]
    outcome: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "root_event": self.root_event.to_dict(),
            "events": [e.to_dict() for e in self.events],
            "depth": self.depth,
            "total_duration_ms": self.total_duration_ms,
            "subsystems_involved": sorted(self.subsystems_involved),
            "agents_involved": sorted(self.agents_involved),
            "outcome": self.outcome,
        }

    @classmethod
    def from_events(cls, chain_id: str, root: CausalEvent, events: list[CausalEvent], outcome: str) -> CausalChain:
        depth = max((e.generation for e in events), default=0)
        durations = [e.duration_ms for e in events if e.duration_ms is not None]
        total_duration = sum(durations)
        subsystems = {e.source_subsystem for e in events}
        agents = {e.agent_id for e in events if e.agent_id}
        return cls(
            chain_id=chain_id,
            root_event=root,
            events=events,
            depth=depth,
            total_duration_ms=total_duration,
            subsystems_involved=subsystems,
            agents_involved=agents,
            outcome=outcome,
        )


@dataclass
class TraceSession:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    started_at: float = field(default_factory=time.time)
    events: list[CausalEvent] = field(default_factory=list)
    chains: list[CausalChain] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "event_count": len(self.events),
            "chain_count": len(self.chains),
            "metadata": self.metadata,
        }
