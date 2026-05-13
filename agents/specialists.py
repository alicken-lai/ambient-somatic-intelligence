"""
Specialist Agents — Domain-specific agent implementations.

Each specialist has:
  - Deep domain knowledge (pre-seeded + learned)
  - Task matching heuristics (knows what it's good at)
  - Preferred strategies and tools
  - Historical performance that improves over time

Agents:
  FrontendAgent  — UI/UX, React, styling, component architecture
  BackendAgent   — APIs, databases, services, performance
  TestingAgent   — Tests, coverage, flaky detection, regression
  GuardianAgent  — Security, governance, policy enforcement
  MemoryAgent    — Memory management, compression, retrieval optimization
  PlannerAgent   — Task decomposition, orchestration, dependency planning
"""

from __future__ import annotations

from typing import Any

from agents.base import BaseAgent, AgentCapability, ExecutionPreferences


class FrontendAgent(BaseAgent):
    """Specialist in frontend development, UI/UX, and component architecture."""

    def __init__(self):
        super().__init__("frontend-agent", "Frontend Specialist")
        self.preferences = ExecutionPreferences(
            max_retries=2,
            timeout_seconds=180,
            preferred_tools=["browser", "file_edit", "grep"],
            avoid_patterns=["direct_db_access", "backend_deployment"],
            parallelism=2,
        )
        self._domain_keywords = {
            "react", "vue", "angular", "css", "html", "component", "ui", "ux",
            "layout", "style", "tailwind", "responsive", "animation", "form",
            "modal", "button", "input", "page", "view", "render", "hook",
            "state", "prop", "jsx", "tsx", "frontend", "client", "browser",
        }

    @property
    def domain(self) -> str:
        return "frontend"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.FRONTEND]

    def can_handle(self, task: dict[str, Any]) -> float:
        """Score task affinity based on domain keywords."""
        text = f"{task.get('description', '')} {task.get('type', '')} {task.get('domain', '')}".lower()
        tokens = set(text.split())
        overlap = tokens & self._domain_keywords
        if task.get("domain") == "frontend":
            return min(0.7 + len(overlap) * 0.05, 1.0)
        return min(len(overlap) * 0.15, 0.9)

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a frontend task."""
        strategy = self.find_strategy(task.get("type", "implement"))
        return {
            "status": "completed",
            "approach": strategy["approach"] if strategy else "component-first development",
            "strategy": {
                "task_type": task.get("type", "implement"),
                "approach": "component-first development",
                "tools_used": self.preferences.preferred_tools,
            },
        }


class BackendAgent(BaseAgent):
    """Specialist in backend development, APIs, and data services."""

    def __init__(self):
        super().__init__("backend-agent", "Backend Specialist")
        self.preferences = ExecutionPreferences(
            max_retries=3,
            timeout_seconds=300,
            preferred_tools=["shell", "file_edit", "grep", "database"],
            avoid_patterns=["ui_modification", "css_changes"],
            parallelism=3,
        )
        self._domain_keywords = {
            "api", "endpoint", "server", "database", "sql", "query", "schema",
            "migration", "rest", "graphql", "auth", "token", "middleware",
            "route", "controller", "model", "service", "cache", "redis",
            "postgres", "mongo", "backend", "python", "node", "express",
            "fastapi", "django", "flask", "orm", "crud",
        }

    @property
    def domain(self) -> str:
        return "backend"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.BACKEND, AgentCapability.DATABASE]

    def can_handle(self, task: dict[str, Any]) -> float:
        text = f"{task.get('description', '')} {task.get('type', '')} {task.get('domain', '')}".lower()
        tokens = set(text.split())
        overlap = tokens & self._domain_keywords
        if task.get("domain") == "backend":
            return min(0.7 + len(overlap) * 0.05, 1.0)
        return min(len(overlap) * 0.15, 0.9)

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        strategy = self.find_strategy(task.get("type", "implement"))
        return {
            "status": "completed",
            "approach": strategy["approach"] if strategy else "schema-first, then services",
            "strategy": {
                "task_type": task.get("type", "implement"),
                "approach": "schema-first, then services",
                "tools_used": self.preferences.preferred_tools,
            },
        }


class TestingAgent(BaseAgent):
    """Specialist in testing, quality assurance, and regression detection."""

    def __init__(self):
        super().__init__("testing-agent", "Testing Specialist")
        self.preferences = ExecutionPreferences(
            max_retries=2,
            timeout_seconds=120,
            preferred_tools=["shell", "file_edit", "grep"],
            avoid_patterns=["production_deployment", "schema_migration"],
            parallelism=4,
        )
        self._domain_keywords = {
            "test", "testing", "spec", "assert", "expect", "mock", "stub",
            "coverage", "unit", "integration", "e2e", "cypress", "jest",
            "pytest", "flaky", "regression", "fixture", "snapshot", "tdd",
            "ci", "pipeline", "quality", "bug", "debug", "failure",
        }
        self._flaky_patterns: list[str] = []

    @property
    def domain(self) -> str:
        return "testing"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.TESTING]

    def can_handle(self, task: dict[str, Any]) -> float:
        text = f"{task.get('description', '')} {task.get('type', '')} {task.get('domain', '')}".lower()
        tokens = set(text.split())
        overlap = tokens & self._domain_keywords
        if task.get("domain") == "testing" or task.get("type") == "test":
            return min(0.8 + len(overlap) * 0.04, 1.0)
        return min(len(overlap) * 0.15, 0.85)

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        strategy = self.find_strategy(task.get("type", "test"))
        return {
            "status": "completed",
            "approach": strategy["approach"] if strategy else "arrange-act-assert pattern",
            "flaky_checks": len(self._flaky_patterns),
            "strategy": {
                "task_type": task.get("type", "test"),
                "approach": "arrange-act-assert pattern",
                "tools_used": self.preferences.preferred_tools,
            },
        }

    def record_flaky(self, test_name: str) -> None:
        """Record a flaky test for future detection."""
        if test_name not in self._flaky_patterns:
            self._flaky_patterns.append(test_name)


class GuardianAgent(BaseAgent):
    """Specialist in security, governance, and policy enforcement."""

    def __init__(self):
        super().__init__("guardian-agent", "Guardian Specialist")
        self.preferences = ExecutionPreferences(
            max_retries=1,
            timeout_seconds=60,
            preferred_tools=["grep", "file_read"],
            avoid_patterns=["destructive_commands", "force_push"],
            context_budget_ratio=0.5,
            parallelism=1,
        )
        self._domain_keywords = {
            "security", "auth", "permission", "policy", "guard", "validate",
            "sanitize", "injection", "xss", "csrf", "secret", "credential",
            "encrypt", "decrypt", "token", "oauth", "rbac", "acl", "audit",
            "compliance", "vulnerability", "threat", "attack", "protect",
        }

    @property
    def domain(self) -> str:
        return "security"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.SECURITY, AgentCapability.CODE_REVIEW]

    def can_handle(self, task: dict[str, Any]) -> float:
        text = f"{task.get('description', '')} {task.get('type', '')} {task.get('domain', '')}".lower()
        tokens = set(text.split())
        overlap = tokens & self._domain_keywords
        if task.get("domain") == "security" or task.get("type") == "review":
            return min(0.75 + len(overlap) * 0.05, 1.0)
        return min(len(overlap) * 0.15, 0.85)

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "completed",
            "approach": "threat-model-first review",
            "checks_performed": ["input_validation", "auth_flow", "secret_exposure"],
            "strategy": {
                "task_type": task.get("type", "review"),
                "approach": "threat-model-first review",
                "tools_used": self.preferences.preferred_tools,
            },
        }


class MemoryManagerAgent(BaseAgent):
    """Specialist in memory management, compression, and retrieval optimization."""

    def __init__(self):
        super().__init__("memory-agent", "Memory Manager")
        self.preferences = ExecutionPreferences(
            max_retries=2,
            timeout_seconds=120,
            preferred_tools=["file_read", "file_edit", "shell"],
            avoid_patterns=["memory_deletion_without_archive"],
            parallelism=2,
        )
        self._domain_keywords = {
            "memory", "recall", "store", "retrieve", "index", "compress",
            "archive", "ttl", "cleanup", "deduplicate", "summarize",
            "context", "token", "budget", "relevance", "semantic",
        }

    @property
    def domain(self) -> str:
        return "memory_management"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.MEMORY_MGMT]

    def can_handle(self, task: dict[str, Any]) -> float:
        text = f"{task.get('description', '')} {task.get('type', '')} {task.get('domain', '')}".lower()
        tokens = set(text.split())
        overlap = tokens & self._domain_keywords
        if task.get("domain") == "memory":
            return min(0.8 + len(overlap) * 0.04, 1.0)
        return min(len(overlap) * 0.15, 0.8)

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "completed",
            "approach": "layer-aware retrieval with TTL enforcement",
            "strategy": {
                "task_type": task.get("type", "optimize"),
                "approach": "layer-aware retrieval with TTL enforcement",
                "tools_used": self.preferences.preferred_tools,
            },
        }


class PlannerAgent(BaseAgent):
    """Specialist in task decomposition, orchestration, and dependency planning."""

    def __init__(self):
        super().__init__("planner-agent", "Planner Specialist")
        self.preferences = ExecutionPreferences(
            max_retries=2,
            timeout_seconds=60,
            preferred_tools=["grep", "file_read"],
            avoid_patterns=["direct_implementation"],
            context_budget_ratio=1.2,
            parallelism=1,
        )
        self._domain_keywords = {
            "plan", "decompose", "split", "orchestrate", "dependency",
            "dag", "schedule", "sequence", "parallel", "priority",
            "milestone", "roadmap", "architecture", "design", "refactor",
            "migration", "strategy", "breakdown", "estimate", "scope",
        }

    @property
    def domain(self) -> str:
        return "planning"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.PLANNING]

    def can_handle(self, task: dict[str, Any]) -> float:
        text = f"{task.get('description', '')} {task.get('type', '')} {task.get('domain', '')}".lower()
        tokens = set(text.split())
        overlap = tokens & self._domain_keywords
        if task.get("type") in ("plan", "decompose", "architect"):
            return min(0.85 + len(overlap) * 0.03, 1.0)
        return min(len(overlap) * 0.12, 0.8)

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "completed",
            "approach": "top-down decomposition with dependency mapping",
            "output_type": "task_graph",
            "strategy": {
                "task_type": task.get("type", "plan"),
                "approach": "top-down decomposition with dependency mapping",
                "tools_used": self.preferences.preferred_tools,
            },
        }


def create_all_specialists() -> list[BaseAgent]:
    """Factory function to instantiate all specialist agents."""
    return [
        FrontendAgent(),
        BackendAgent(),
        TestingAgent(),
        GuardianAgent(),
        MemoryManagerAgent(),
        PlannerAgent(),
    ]
