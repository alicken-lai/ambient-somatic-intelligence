"""
Agent Telemetry — Execution profiling and performance monitoring for agents.

Tracks per-agent metrics:
  - Task completion rates and durations
  - Token consumption patterns
  - Memory recall effectiveness (hit/miss)
  - Governance intervention frequency
  - Error rates and recovery patterns
  - Specialization efficiency

Provides lifecycle hooks for agents to report their activity.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from observability.metrics_collector import MetricsCollector


@dataclass
class TaskRecord:
    """Record of a single task execution."""
    task_id: str
    agent_id: str
    name: str
    started: float = field(default_factory=time.time)
    ended: float | None = None
    status: str = "running"
    tokens_used: int = 0
    memory_recalls: int = 0
    governance_checks: int = 0
    retries: int = 0
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.ended is None:
            return None
        return round((self.ended - self.started) * 1000, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "name": self.name,
            "started": datetime.fromtimestamp(self.started, tz=timezone.utc).isoformat(),
            "ended": datetime.fromtimestamp(self.ended, tz=timezone.utc).isoformat() if self.ended else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "tokens_used": self.tokens_used,
            "memory_recalls": self.memory_recalls,
            "governance_checks": self.governance_checks,
            "retries": self.retries,
            "error": self.error,
        }


@dataclass
class AgentProfile:
    """Accumulated profile for a specific agent."""
    agent_id: str
    domain: str = "general"
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_tokens: int = 0
    total_duration_ms: float = 0
    total_memory_recalls: int = 0
    total_governance_blocks: int = 0
    last_active: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        total = self.tasks_completed + self.tasks_failed
        return self.tasks_completed / total if total else 1.0

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.tasks_completed if self.tasks_completed else 0

    @property
    def avg_tokens_per_task(self) -> float:
        total = self.tasks_completed + self.tasks_failed
        return self.total_tokens / total if total else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": round(self.success_rate, 3),
            "total_tokens": self.total_tokens,
            "avg_tokens_per_task": round(self.avg_tokens_per_task),
            "total_duration_ms": round(self.total_duration_ms, 1),
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "total_memory_recalls": self.total_memory_recalls,
            "total_governance_blocks": self.total_governance_blocks,
            "last_active": datetime.fromtimestamp(self.last_active, tz=timezone.utc).isoformat(),
        }


class AgentTelemetry:
    """
    Agent-level telemetry and execution profiling.

    Usage:
        metrics = MetricsCollector()
        telemetry = AgentTelemetry(metrics)

        # Start a task
        record = telemetry.start_task("frontend-agent", "task-123", "Implement login form")

        # Update during execution
        telemetry.record_tokens("frontend-agent", "task-123", 500)
        telemetry.record_memory_recall("frontend-agent", "task-123")

        # Complete
        telemetry.complete_task("frontend-agent", "task-123", success=True)

        # Query
        profile = telemetry.get_profile("frontend-agent")
        print(f"Success rate: {profile.success_rate:.0%}")
    """

    def __init__(self, metrics: MetricsCollector | None = None):
        self.metrics = metrics or MetricsCollector(persist=False)
        self._profiles: dict[str, AgentProfile] = {}
        self._active_tasks: dict[str, TaskRecord] = {}  # key: "{agent_id}:{task_id}"
        self._completed_tasks: list[TaskRecord] = []
        self._max_history = 200

    def register_agent(self, agent_id: str, domain: str = "general") -> AgentProfile:
        """Register an agent for telemetry tracking."""
        if agent_id not in self._profiles:
            self._profiles[agent_id] = AgentProfile(agent_id=agent_id, domain=domain)
        return self._profiles[agent_id]

    def start_task(self, agent_id: str, task_id: str, name: str) -> TaskRecord:
        """Record the start of a task execution."""
        self.register_agent(agent_id)
        record = TaskRecord(task_id=task_id, agent_id=agent_id, name=name)
        key = f"{agent_id}:{task_id}"
        self._active_tasks[key] = record

        self.metrics.increment(f"agent.{agent_id}.tasks_started")
        self.metrics.increment("agent.total_tasks_started")
        return record

    def complete_task(self, agent_id: str, task_id: str, success: bool = True, error: str | None = None) -> TaskRecord | None:
        """Record task completion."""
        key = f"{agent_id}:{task_id}"
        record = self._active_tasks.pop(key, None)
        if not record:
            return None

        record.ended = time.time()
        record.status = "completed" if success else "failed"
        record.error = error

        profile = self._profiles.get(agent_id)
        if profile:
            profile.last_active = time.time()
            if success:
                profile.tasks_completed += 1
                profile.total_duration_ms += record.duration_ms or 0
            else:
                profile.tasks_failed += 1
            profile.total_tokens += record.tokens_used

        self._completed_tasks.append(record)
        if len(self._completed_tasks) > self._max_history:
            self._completed_tasks = self._completed_tasks[-self._max_history:]

        if success:
            self.metrics.increment(f"agent.{agent_id}.tasks_completed")
            self.metrics.histogram(f"agent.{agent_id}.duration_ms", record.duration_ms or 0)
        else:
            self.metrics.increment(f"agent.{agent_id}.tasks_failed")

        return record

    def record_tokens(self, agent_id: str, task_id: str, tokens: int) -> None:
        """Record token consumption for a task."""
        key = f"{agent_id}:{task_id}"
        record = self._active_tasks.get(key)
        if record:
            record.tokens_used += tokens
        self.metrics.increment(f"agent.{agent_id}.tokens_total", tokens)
        self.metrics.increment("token.total_consumed", tokens)

    def record_memory_recall(self, agent_id: str, task_id: str, hit: bool = True) -> None:
        """Record a memory recall event."""
        key = f"{agent_id}:{task_id}"
        record = self._active_tasks.get(key)
        if record:
            record.memory_recalls += 1

        profile = self._profiles.get(agent_id)
        if profile:
            profile.total_memory_recalls += 1

        suffix = "hit" if hit else "miss"
        self.metrics.increment(f"memory.recall.{suffix}")
        self.metrics.increment(f"agent.{agent_id}.memory_recalls")

    def record_governance_check(self, agent_id: str, task_id: str, result: str) -> None:
        """Record a governance check (allow/block/review)."""
        key = f"{agent_id}:{task_id}"
        record = self._active_tasks.get(key)
        if record:
            record.governance_checks += 1

        if result == "block":
            profile = self._profiles.get(agent_id)
            if profile:
                profile.total_governance_blocks += 1

        self.metrics.increment(f"governance.{result}")
        self.metrics.increment(f"agent.{agent_id}.governance_{result}")

    def get_profile(self, agent_id: str) -> AgentProfile | None:
        """Get agent profile."""
        return self._profiles.get(agent_id)

    def all_profiles(self) -> list[dict[str, Any]]:
        """Get all agent profiles."""
        return [p.to_dict() for p in self._profiles.values()]

    def active_tasks(self) -> list[dict[str, Any]]:
        """Get currently active tasks."""
        return [r.to_dict() for r in self._active_tasks.values()]

    def recent_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recently completed tasks."""
        return [r.to_dict() for r in self._completed_tasks[-limit:]]

    def summary(self) -> dict[str, Any]:
        """Get overall telemetry summary."""
        total_completed = sum(p.tasks_completed for p in self._profiles.values())
        total_failed = sum(p.tasks_failed for p in self._profiles.values())
        total_tokens = sum(p.total_tokens for p in self._profiles.values())

        return {
            "agents_registered": len(self._profiles),
            "active_tasks": len(self._active_tasks),
            "total_completed": total_completed,
            "total_failed": total_failed,
            "overall_success_rate": round(total_completed / (total_completed + total_failed), 3) if (total_completed + total_failed) else 1.0,
            "total_tokens_consumed": total_tokens,
            "agent_profiles": self.all_profiles(),
        }
