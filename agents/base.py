"""
Base Agent — Foundation for all persistent specialized agents.

A BaseAgent provides:
  - Persistent identity and state across sessions
  - Local memory (domain experience, learned patterns)
  - Execution preferences (tool ordering, retry behavior)
  - Capability declaration (what tasks it can handle)
  - Performance tracking (success rates, efficiency)
  - Lifecycle hooks (init, before_task, after_task, shutdown)

Agents are NOT ephemeral sub-agents. They persist, learn, and improve.
"""

from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.isolation import MemorySlice, RetrievalProfile
    from agents.execution_history import ExecutionHistory


AGENTS_STATE_DIR = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os")) / "state" / "agents"


class AgentStatus(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class AgentCapability(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    TESTING = "testing"
    SECURITY = "security"
    MEMORY_MGMT = "memory_management"
    PLANNING = "planning"
    DATABASE = "database"
    DEVOPS = "devops"
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"


@dataclass
class ExecutionPreferences:
    """Agent's preferred execution parameters."""
    max_retries: int = 3
    timeout_seconds: float = 300.0
    preferred_tools: list[str] = field(default_factory=list)
    avoid_patterns: list[str] = field(default_factory=list)
    context_budget_ratio: float = 1.0
    parallelism: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "preferred_tools": self.preferred_tools,
            "avoid_patterns": self.avoid_patterns,
            "context_budget_ratio": self.context_budget_ratio,
            "parallelism": self.parallelism,
        }


@dataclass
class AgentPerformance:
    """Tracked performance metrics for an agent."""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_duration_ms: float = 0
    total_tokens_used: int = 0
    strategies_learned: int = 0
    last_task_time: float = 0

    @property
    def success_rate(self) -> float:
        total = self.tasks_completed + self.tasks_failed
        return self.tasks_completed / total if total else 1.0

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.tasks_completed if self.tasks_completed else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": round(self.success_rate, 3),
            "total_duration_ms": round(self.total_duration_ms, 1),
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "total_tokens_used": self.total_tokens_used,
            "strategies_learned": self.strategies_learned,
        }


class BaseAgent(ABC):
    """
    Abstract base for all persistent specialized agents.

    Subclasses must implement:
      - domain: str property
      - capabilities: list of AgentCapability
      - can_handle(task): whether this agent can handle a given task
      - execute(task): perform the task and return result
    """

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.status = AgentStatus.IDLE
        self.preferences = ExecutionPreferences()
        self.performance = AgentPerformance()
        self.created_at = time.time()
        self._state_dir = AGENTS_STATE_DIR / agent_id
        self._strategies: list[dict[str, Any]] = []
        self._patterns: list[dict[str, Any]] = []

        self._memory_slice: MemorySlice | None = None
        self._retrieval_profile: RetrievalProfile | None = None
        self._execution_history: ExecutionHistory | None = None

    @property
    @abstractmethod
    def domain(self) -> str:
        """Agent's specialization domain."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> list[AgentCapability]:
        """List of capabilities this agent provides."""
        ...

    @abstractmethod
    def can_handle(self, task: dict[str, Any]) -> float:
        """
        Evaluate if this agent can handle a task.
        Returns confidence score 0.0-1.0.
        """
        ...

    @abstractmethod
    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a task and return result."""
        ...

    def before_task(self, task: dict[str, Any]) -> None:
        """Hook called before task execution."""
        self.status = AgentStatus.BUSY

    def after_task(self, task: dict[str, Any], result: dict[str, Any]) -> None:
        """Hook called after task execution."""
        self.status = AgentStatus.IDLE
        self.performance.last_task_time = time.time()

    def learn_strategy(self, strategy: dict[str, Any]) -> None:
        """Record a successful strategy for future reuse."""
        strategy["learned_at"] = time.time()
        self._strategies.append(strategy)
        self.performance.strategies_learned += 1
        if len(self._strategies) > 50:
            self._strategies = self._strategies[-50:]

    def learn_pattern(self, pattern: dict[str, Any]) -> None:
        """Record a recognized pattern."""
        pattern["observed_at"] = time.time()
        self._patterns.append(pattern)
        if len(self._patterns) > 100:
            self._patterns = self._patterns[-100:]

    def find_strategy(self, task_type: str) -> dict[str, Any] | None:
        """Find a previously successful strategy for a task type."""
        for s in reversed(self._strategies):
            if s.get("task_type") == task_type:
                return s
        return None

    @property
    def memory_slice(self) -> "MemorySlice | None":
        """Isolated memory slice for this agent (set by IsolationManager)."""
        return self._memory_slice

    @memory_slice.setter
    def memory_slice(self, value: "MemorySlice") -> None:
        self._memory_slice = value

    @property
    def retrieval_profile(self) -> "RetrievalProfile | None":
        """Domain-specific retrieval profile (set by IsolationManager)."""
        return self._retrieval_profile

    @retrieval_profile.setter
    def retrieval_profile(self, value: "RetrievalProfile") -> None:
        self._retrieval_profile = value

    @property
    def execution_history(self) -> "ExecutionHistory":
        """Persistent execution history (lazy-initialized)."""
        if self._execution_history is None:
            from agents.execution_history import ExecutionHistory as EH
            self._execution_history = EH(self.agent_id)
        return self._execution_history

    def run_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Full task lifecycle: before → execute → after → record → learn."""
        self.before_task(task)
        start = time.time()

        try:
            result = self.execute(task)
            duration_ms = (time.time() - start) * 1000
            result["duration_ms"] = round(duration_ms, 1)
            result["agent_id"] = self.agent_id

            self.performance.tasks_completed += 1
            self.performance.total_duration_ms += duration_ms

            if result.get("strategy"):
                self.learn_strategy(result["strategy"])

            self._record_execution(task, result, duration_ms)
            self.after_task(task, result)
            return result

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            self.performance.tasks_failed += 1
            self.status = AgentStatus.IDLE
            error_result = {
                "agent_id": self.agent_id,
                "status": "error",
                "error": str(e),
                "duration_ms": round(duration_ms, 1),
            }
            self._record_execution(task, error_result, duration_ms)
            return error_result

    def _record_execution(self, task: dict[str, Any], result: dict[str, Any], duration_ms: float) -> None:
        """Record task execution to persistent history."""
        try:
            strategy_info = result.get("strategy", {})
            self.execution_history.record(
                task_type=task.get("type", "unknown"),
                description=task.get("description", "")[:200],
                status=result.get("status", "unknown"),
                duration_ms=duration_ms,
                tokens_used=result.get("tokens_used", 0),
                strategy=strategy_info.get("approach", "") if isinstance(strategy_info, dict) else str(strategy_info),
                metadata={"task_domain": task.get("domain", ""), "agent_id": self.agent_id},
            )
        except Exception:
            pass

    def save_state(self) -> None:
        """Persist agent state to disk."""
        self._state_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "agent_id": self.agent_id,
            "name": self.name,
            "domain": self.domain,
            "status": self.status.value,
            "created_at": datetime.fromtimestamp(self.created_at, tz=timezone.utc).isoformat(),
            "preferences": self.preferences.to_dict(),
            "performance": self.performance.to_dict(),
            "strategies": self._strategies[-20:],
            "patterns": self._patterns[-20:],
            "saved_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        filepath = self._state_dir / "state.json"
        with open(filepath, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> bool:
        """Load persisted state from disk."""
        filepath = self._state_dir / "state.json"
        if not filepath.exists():
            return False
        try:
            with open(filepath) as f:
                state = json.load(f)
            perf = state.get("performance", {})
            self.performance.tasks_completed = perf.get("tasks_completed", 0)
            self.performance.tasks_failed = perf.get("tasks_failed", 0)
            self.performance.total_duration_ms = perf.get("total_duration_ms", 0)
            self.performance.total_tokens_used = perf.get("total_tokens_used", 0)
            self.performance.strategies_learned = perf.get("strategies_learned", 0)
            self._strategies = state.get("strategies", [])
            self._patterns = state.get("patterns", [])
            return True
        except (json.JSONDecodeError, OSError):
            return False

    def profile(self) -> dict[str, Any]:
        """Get agent profile summary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "domain": self.domain,
            "status": self.status.value,
            "capabilities": [c.value for c in self.capabilities],
            "performance": self.performance.to_dict(),
            "strategies_count": len(self._strategies),
            "patterns_count": len(self._patterns),
            "preferences": self.preferences.to_dict(),
        }
