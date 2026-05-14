"""
Agent Registry — Discovery, registration, and coordination of agents.

The registry is the "phone book" for the agent system:
  - Register agents with their capabilities
  - Find the best agent for a given task
  - Track agent availability and health
  - Route tasks to appropriate specialists
"""

from __future__ import annotations

import time
from typing import Any

from agents.base import BaseAgent, AgentCapability, AgentStatus


class AgentRegistry:
    """
    Central registry for all persistent agents.

    Usage:
        registry = AgentRegistry()
        registry.register(frontend_agent)
        registry.register(backend_agent)

        # Find best agent for a task
        task = {"type": "implement", "domain": "frontend", "description": "Build login form"}
        agent = registry.find_best(task)

        # Find all agents with a capability
        testers = registry.find_by_capability(AgentCapability.TESTING)
    """

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._capability_index: dict[AgentCapability, list[str]] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register an agent."""
        self._agents[agent.agent_id] = agent

        for cap in agent.capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = []
            if agent.agent_id not in self._capability_index[cap]:
                self._capability_index[cap].append(agent.agent_id)

        agent.load_state()

    def unregister(self, agent_id: str) -> None:
        """Remove an agent from registry."""
        agent = self._agents.pop(agent_id, None)
        if agent:
            for cap in agent.capabilities:
                agents = self._capability_index.get(cap, [])
                if agent_id in agents:
                    agents.remove(agent_id)

    def get(self, agent_id: str) -> BaseAgent | None:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def find_best(self, task: dict[str, Any]) -> BaseAgent | None:
        """Find the best available agent for a task."""
        candidates: list[tuple[float, BaseAgent]] = []

        for agent in self._agents.values():
            if agent.status == AgentStatus.OFFLINE:
                continue
            confidence = agent.can_handle(task)
            if confidence > 0:
                availability_bonus = 0.2 if agent.status == AgentStatus.IDLE else 0
                experience_bonus = min(agent.performance.tasks_completed * 0.01, 0.2)
                score = confidence + availability_bonus + experience_bonus
                candidates.append((score, agent))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def find_by_capability(self, capability: AgentCapability) -> list[BaseAgent]:
        """Find all agents with a specific capability."""
        agent_ids = self._capability_index.get(capability, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def find_available(self) -> list[BaseAgent]:
        """Find all idle agents."""
        return [a for a in self._agents.values() if a.status == AgentStatus.IDLE]

    def all_agents(self) -> list[BaseAgent]:
        """Get all registered agents."""
        return list(self._agents.values())

    def status_report(self) -> dict[str, Any]:
        """Get registry status."""
        by_status: dict[str, int] = {}
        by_domain: dict[str, int] = {}
        for agent in self._agents.values():
            by_status[agent.status.value] = by_status.get(agent.status.value, 0) + 1
            by_domain[agent.domain] = by_domain.get(agent.domain, 0) + 1

        return {
            "total_agents": len(self._agents),
            "by_status": by_status,
            "by_domain": by_domain,
            "capabilities_covered": [c.value for c in self._capability_index if self._capability_index[c]],
            "agents": [a.profile() for a in self._agents.values()],
        }

    def save_all(self) -> int:
        """Persist all agent states."""
        saved = 0
        for agent in self._agents.values():
            try:
                agent.save_state()
                saved += 1
            except Exception:
                pass
        return saved

    def load_all(self) -> int:
        """Load all agent states from disk."""
        loaded = 0
        for agent in self._agents.values():
            if agent.load_state():
                loaded += 1
        return loaded
