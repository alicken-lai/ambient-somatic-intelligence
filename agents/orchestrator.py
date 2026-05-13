"""
Agent Orchestrator — Multi-agent coordination and intelligent task dispatch.

Responsibilities:
  - Analyze incoming tasks and determine required capabilities
  - Route tasks to the best-suited specialist(s)
  - Coordinate multi-agent workflows (parallel or sequential)
  - Aggregate results from multiple agents
  - Handle failures with fallback routing
  - Track orchestration performance

Integrates with:
  - AgentRegistry: find available specialists
  - TaskGraph: build dependency-aware execution plans
  - Governance: validate before dispatch
  - Observability: trace multi-agent execution
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from agents.base import BaseAgent, AgentStatus
from agents.registry import AgentRegistry


@dataclass
class DispatchResult:
    """Result of dispatching a task to an agent."""
    task: dict[str, Any]
    agent_id: str
    agent_name: str
    confidence: float
    result: dict[str, Any] | None = None
    started: float = field(default_factory=time.time)
    ended: float | None = None
    status: str = "pending"

    @property
    def duration_ms(self) -> float | None:
        if self.ended is None:
            return None
        return round((self.ended - self.started) * 1000, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "confidence": round(self.confidence, 3),
            "status": self.status,
            "duration_ms": self.duration_ms,
            "result": self.result,
        }


@dataclass
class OrchestrationPlan:
    """A plan for executing a complex task across multiple agents."""
    task: dict[str, Any]
    stages: list[list[dict[str, Any]]] = field(default_factory=list)
    mode: str = "sequential"  # sequential, parallel, mixed

    def add_stage(self, subtasks: list[dict[str, Any]]) -> None:
        self.stages.append(subtasks)

    @property
    def total_subtasks(self) -> int:
        return sum(len(stage) for stage in self.stages)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "mode": self.mode,
            "stages": len(self.stages),
            "total_subtasks": self.total_subtasks,
            "plan": self.stages,
        }


class AgentOrchestrator:
    """
    Coordinates multi-agent task execution.

    Usage:
        registry = AgentRegistry()
        # ... register agents ...
        orchestrator = AgentOrchestrator(registry)

        # Simple dispatch (single agent)
        result = orchestrator.dispatch({
            "type": "implement",
            "domain": "frontend",
            "description": "Build login form with validation"
        })

        # Multi-agent dispatch (parallel)
        results = orchestrator.dispatch_parallel([
            {"type": "implement", "domain": "frontend", "description": "Login UI"},
            {"type": "implement", "domain": "backend", "description": "Auth API"},
            {"type": "test", "domain": "testing", "description": "Auth tests"},
        ])

        # Complex orchestration
        plan = orchestrator.plan_execution({
            "type": "feature",
            "description": "User authentication system",
            "subtasks": [...]
        })
        results = orchestrator.execute_plan(plan)
    """

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self._dispatch_history: list[DispatchResult] = []
        self._max_history = 100

    def dispatch(self, task: dict[str, Any]) -> DispatchResult:
        """Dispatch a single task to the best agent."""
        agent = self.registry.find_best(task)
        if not agent:
            return DispatchResult(
                task=task,
                agent_id="none",
                agent_name="No suitable agent",
                confidence=0.0,
                status="no_agent_found",
            )

        confidence = agent.can_handle(task)
        dr = DispatchResult(
            task=task,
            agent_id=agent.agent_id,
            agent_name=agent.name,
            confidence=confidence,
        )

        try:
            result = agent.run_task(task)
            dr.result = result
            dr.status = result.get("status", "completed")
            dr.ended = time.time()
        except Exception as e:
            dr.status = "error"
            dr.result = {"error": str(e)}
            dr.ended = time.time()

        self._dispatch_history.append(dr)
        if len(self._dispatch_history) > self._max_history:
            self._dispatch_history = self._dispatch_history[-self._max_history:]

        return dr

    def dispatch_parallel(self, tasks: list[dict[str, Any]]) -> list[DispatchResult]:
        """Dispatch multiple independent tasks (best-effort parallel via sequential for now)."""
        results: list[DispatchResult] = []
        for task in tasks:
            result = self.dispatch(task)
            results.append(result)
        return results

    def dispatch_with_fallback(self, task: dict[str, Any], max_attempts: int = 3) -> DispatchResult:
        """Dispatch with fallback to alternative agents on failure."""
        tried: set[str] = set()

        for _ in range(max_attempts):
            agents = self._rank_agents(task)
            agent = None
            for _, a in agents:
                if a.agent_id not in tried:
                    agent = a
                    break

            if not agent:
                return DispatchResult(
                    task=task,
                    agent_id="none",
                    agent_name="All agents exhausted",
                    confidence=0.0,
                    status="all_agents_failed",
                )

            tried.add(agent.agent_id)
            confidence = agent.can_handle(task)
            dr = DispatchResult(
                task=task,
                agent_id=agent.agent_id,
                agent_name=agent.name,
                confidence=confidence,
            )

            try:
                result = agent.run_task(task)
                dr.result = result
                dr.status = result.get("status", "completed")
                dr.ended = time.time()

                if dr.status != "error":
                    self._dispatch_history.append(dr)
                    return dr
            except Exception as e:
                dr.status = "error"
                dr.result = {"error": str(e)}
                dr.ended = time.time()

        dr.status = "all_retries_exhausted"
        self._dispatch_history.append(dr)
        return dr

    def plan_execution(self, task: dict[str, Any]) -> OrchestrationPlan:
        """Create an execution plan for a complex multi-agent task."""
        plan = OrchestrationPlan(task=task)
        subtasks = task.get("subtasks", [])

        if not subtasks:
            plan.add_stage([task])
            plan.mode = "sequential"
            return plan

        independent: list[dict[str, Any]] = []
        dependent: list[dict[str, Any]] = []

        for st in subtasks:
            if st.get("depends_on"):
                dependent.append(st)
            else:
                independent.append(st)

        if independent:
            plan.add_stage(independent)
            plan.mode = "parallel" if len(independent) > 1 else "sequential"

        if dependent:
            plan.add_stage(dependent)
            plan.mode = "mixed" if independent else "sequential"

        return plan

    def execute_plan(self, plan: OrchestrationPlan) -> list[DispatchResult]:
        """Execute an orchestration plan stage by stage."""
        all_results: list[DispatchResult] = []

        for stage in plan.stages:
            stage_results = self.dispatch_parallel(stage)
            all_results.extend(stage_results)

            if any(r.status == "error" for r in stage_results):
                break

        return all_results

    def stats(self) -> dict[str, Any]:
        """Get orchestration statistics."""
        if not self._dispatch_history:
            return {"total_dispatches": 0}

        completed = [d for d in self._dispatch_history if d.status == "completed"]
        failed = [d for d in self._dispatch_history if d.status == "error"]
        durations = [d.duration_ms for d in completed if d.duration_ms]

        agent_usage: dict[str, int] = {}
        for d in self._dispatch_history:
            agent_usage[d.agent_id] = agent_usage.get(d.agent_id, 0) + 1

        return {
            "total_dispatches": len(self._dispatch_history),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": round(len(completed) / len(self._dispatch_history), 3),
            "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else 0,
            "agent_usage": agent_usage,
            "avg_confidence": round(
                sum(d.confidence for d in self._dispatch_history) / len(self._dispatch_history), 3
            ),
        }

    def _rank_agents(self, task: dict[str, Any]) -> list[tuple[float, BaseAgent]]:
        """Rank all agents by suitability for a task."""
        candidates: list[tuple[float, BaseAgent]] = []
        for agent in self.registry.all_agents():
            if agent.status == AgentStatus.OFFLINE:
                continue
            score = agent.can_handle(task)
            if score > 0:
                candidates.append((score, agent))
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates
