"""
Agent Decision Logger — Structured audit trail of agent decision-making.

Records every significant decision an agent makes during task execution:
  - Which strategy was chosen and why
  - What memories were consulted
  - What governance checks were performed
  - Confidence level and reasoning

Integration points:
  - IntegrationBus wires agent task execution to auto-record decisions
  - AgentDecisionLog is available via AmbientKernel.observability.decision_log
  - Stored as JSONL at observability/decisions/agent_decisions.jsonl
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
DECISIONS_DIR = AMBIENT_ROOT / "observability" / "decisions"
DECISIONS_LOG = DECISIONS_DIR / "agent_decisions.jsonl"


@dataclass
class DecisionEvent:
    """A single agent decision record."""
    agent_id: str
    task: str
    strategy_chosen: str
    memories_consulted: list[dict[str, Any]]
    governance_result: str
    confidence: float
    reasoning: str
    timestamp: float = field(default_factory=time.time)
    decision_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.decision_id:
            self.decision_id = f"dec_{int(self.timestamp * 1000)}"

    @property
    def memories_count(self) -> int:
        return len(self.memories_consulted)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "agent_id": self.agent_id,
            "task": self.task,
            "strategy_chosen": self.strategy_chosen,
            "memories_consulted": self.memories_consulted,
            "memories_count": self.memories_count,
            "governance_result": self.governance_result,
            "confidence": round(self.confidence, 4),
            "reasoning": self.reasoning,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
            "metadata": self.metadata,
        }


class AgentDecisionLog:
    """
    Records and queries agent decision events for observability.

    Usage:
        log = AgentDecisionLog()

        log.log_decision(
            agent_id="frontend-agent",
            task="implement login page",
            strategy_chosen="component-first",
            memories_consulted=[{"content": "...", "score": 0.9}],
            governance_result="ALLOW",
            confidence=0.85,
            reasoning="Prior experience with similar UI tasks favors component-first",
        )

        decisions = log.query_by_agent("frontend-agent")
        stats = log.stats()
    """

    def __init__(self, persist: bool = True, max_events: int = 500):
        self._events: list[DecisionEvent] = []
        self._max_events = max_events
        self._persist = persist

        if persist:
            DECISIONS_DIR.mkdir(parents=True, exist_ok=True)

    def log_decision(
        self,
        agent_id: str,
        task: str,
        strategy_chosen: str,
        memories_consulted: list[dict[str, Any]] | None = None,
        governance_result: str = "ALLOW",
        confidence: float = 1.0,
        reasoning: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> DecisionEvent:
        """Record an agent decision event."""
        event = DecisionEvent(
            agent_id=agent_id,
            task=task,
            strategy_chosen=strategy_chosen,
            memories_consulted=memories_consulted or [],
            governance_result=governance_result,
            confidence=max(0.0, min(1.0, confidence)),
            reasoning=reasoning,
            metadata=metadata or {},
        )

        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        if self._persist:
            self._persist_event(event)

        return event

    def query_by_agent(
        self,
        agent_id: str,
        limit: int = 20,
        since: float | None = None,
    ) -> list[dict[str, Any]]:
        """Get decisions for a specific agent."""
        filtered = [
            e for e in self._events
            if e.agent_id == agent_id
            and (since is None or e.timestamp >= since)
        ]
        filtered.sort(key=lambda e: e.timestamp, reverse=True)
        return [e.to_dict() for e in filtered[:limit]]

    def query_by_time(
        self,
        start: float,
        end: float | None = None,
        agent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get decisions within a time window."""
        end = end or time.time()
        filtered = [
            e for e in self._events
            if start <= e.timestamp <= end
            and (agent_id is None or e.agent_id == agent_id)
        ]
        filtered.sort(key=lambda e: e.timestamp, reverse=True)
        return [e.to_dict() for e in filtered]

    def stats(self) -> dict[str, Any]:
        """Aggregate decision statistics."""
        if not self._events:
            return {
                "total_decisions": 0,
                "unique_agents": 0,
                "by_agent": {},
                "by_governance": {},
                "avg_confidence": 0.0,
                "avg_memories_per_decision": 0.0,
            }

        by_agent: dict[str, int] = defaultdict(int)
        by_governance: dict[str, int] = defaultdict(int)
        total_confidence = 0.0
        total_memories = 0

        for e in self._events:
            by_agent[e.agent_id] += 1
            by_governance[e.governance_result] += 1
            total_confidence += e.confidence
            total_memories += e.memories_count

        total = len(self._events)

        return {
            "total_decisions": total,
            "unique_agents": len(by_agent),
            "by_agent": dict(by_agent),
            "by_governance": dict(by_governance),
            "avg_confidence": round(total_confidence / total, 4),
            "avg_memories_per_decision": round(total_memories / total, 2),
        }

    def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get the most recent decision events."""
        return [e.to_dict() for e in self._events[-limit:]]

    def _persist_event(self, event: DecisionEvent) -> None:
        """Append event to disk as JSONL."""
        try:
            with DECISIONS_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            pass
