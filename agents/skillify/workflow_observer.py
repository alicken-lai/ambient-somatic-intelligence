"""
Workflow Observer — Observe and record workflow executions for pattern mining.

Records workflow events as they happen, persisting them as JSONL for
downstream analysis by the PatternMiner and clustering pipeline.

Storage: agents/skillify/observations.jsonl
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
OBSERVATIONS_PATH = AMBIENT_ROOT / "agents" / "skillify" / "observations.jsonl"


@dataclass
class WorkflowStep:
    """A single step within a workflow execution."""
    step_name: str
    module: str
    function: str
    duration_ms: float
    success: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_name": self.step_name,
            "module": self.module,
            "function": self.function,
            "duration_ms": round(self.duration_ms, 1),
            "success": self.success,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> WorkflowStep:
        return WorkflowStep(
            step_name=data.get("step_name", ""),
            module=data.get("module", ""),
            function=data.get("function", ""),
            duration_ms=data.get("duration_ms", 0.0),
            success=data.get("success", True),
        )


@dataclass
class WorkflowEvent:
    """A complete workflow execution event."""
    event_id: str
    timestamp: datetime
    workflow_type: str
    steps: list[WorkflowStep]
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    success: bool
    duration_ms: float
    agent_id: str | None = None
    governance_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "workflow_type": self.workflow_type,
            "steps": [s.to_dict() for s in self.steps],
            "inputs": self.inputs,
            "outputs": self.outputs,
            "success": self.success,
            "duration_ms": round(self.duration_ms, 1),
            "agent_id": self.agent_id,
            "governance_checks": self.governance_checks,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> WorkflowEvent:
        ts_raw = data.get("timestamp", "")
        if isinstance(ts_raw, str):
            try:
                ts = datetime.fromisoformat(ts_raw)
            except ValueError:
                ts = datetime.now(timezone.utc)
        else:
            ts = datetime.now(timezone.utc)

        return WorkflowEvent(
            event_id=data.get("event_id", str(uuid.uuid4())),
            timestamp=ts,
            workflow_type=data.get("workflow_type", "unknown"),
            steps=[WorkflowStep.from_dict(s) for s in data.get("steps", [])],
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            success=data.get("success", True),
            duration_ms=data.get("duration_ms", 0.0),
            agent_id=data.get("agent_id"),
            governance_checks=data.get("governance_checks", []),
        )

    @staticmethod
    def create(
        workflow_type: str,
        steps: list[WorkflowStep],
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        success: bool,
        duration_ms: float,
        agent_id: str | None = None,
        governance_checks: list[str] | None = None,
    ) -> WorkflowEvent:
        """Factory for creating a new event with auto-generated id and timestamp."""
        return WorkflowEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            workflow_type=workflow_type,
            steps=steps,
            inputs=inputs,
            outputs=outputs,
            success=success,
            duration_ms=duration_ms,
            agent_id=agent_id,
            governance_checks=governance_checks or [],
        )


class WorkflowObserver:
    """
    Observe and record workflow executions.

    Persists observations as append-only JSONL and supports querying
    by workflow type, time range, and success status.

    Usage:
        observer = WorkflowObserver()
        observer.observe(event)
        recent = observer.recent(10)
        filtered = observer.query(workflow_type="anomaly_detection", success=True)
    """

    def __init__(self, storage_path: Path | str | None = None):
        self._storage_path = Path(storage_path) if storage_path else OBSERVATIONS_PATH
        self._events: list[WorkflowEvent] = []
        self._load()

    def observe(self, workflow_event: WorkflowEvent) -> None:
        """Record a workflow execution event."""
        self._events.append(workflow_event)
        self._append_to_disk(workflow_event)
        logger.debug(
            "Observed workflow event %s (type=%s, success=%s)",
            workflow_event.event_id,
            workflow_event.workflow_type,
            workflow_event.success,
        )

    def query(
        self,
        workflow_type: str | None = None,
        success: bool | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[WorkflowEvent]:
        """Query observed events with optional filters."""
        results = self._events

        if workflow_type is not None:
            results = [e for e in results if e.workflow_type == workflow_type]

        if success is not None:
            results = [e for e in results if e.success == success]

        if since is not None:
            results = [e for e in results if e.timestamp >= since]

        if until is not None:
            results = [e for e in results if e.timestamp <= until]

        if agent_id is not None:
            results = [e for e in results if e.agent_id == agent_id]

        return results[-limit:]

    def recent(self, n: int = 10) -> list[WorkflowEvent]:
        """Get the N most recent workflow events."""
        return list(reversed(self._events[-n:]))

    def count(self) -> int:
        """Total number of observed events."""
        return len(self._events)

    def workflow_types(self) -> list[str]:
        """List distinct workflow types observed."""
        return sorted({e.workflow_type for e in self._events})

    def all_events(self) -> list[WorkflowEvent]:
        """Return all stored events."""
        return list(self._events)

    def _append_to_disk(self, event: WorkflowEvent) -> None:
        """Append a single event to the JSONL file."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._storage_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Failed to persist workflow event: %s", e)

    def _load(self) -> None:
        """Load previously observed events from disk."""
        if not self._storage_path.exists():
            return
        try:
            with self._storage_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        self._events.append(WorkflowEvent.from_dict(data))
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug("Skipping malformed observation record: %s", e)
        except OSError as e:
            logger.warning("Failed to load observations: %s", e)
