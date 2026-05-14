"""
Agent Isolation Layer — Memory isolation and domain-specific retrieval.

Enforces that agents CANNOT share raw context directly. Each agent gets:

  MemorySlice     — A filtered view of MemoryKernel scoped to the agent's domain.
                    Wraps MemoryKernel.recall() with auto-filtering by tags and layers.

  RetrievalProfile — Domain-specific retrieval configuration including preferred
                     layers, required tags, and scoring weight overrides.

  AgentIsolationManager — Registry of slices and profiles. Provides get_slice()
                          and get_profile() with strict ownership enforcement.

RULE: Agents must NOT share raw context directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from memory.memory_kernel import MemoryKernel, RecallResult, ScoringWeights


@dataclass
class RetrievalProfile:
    """Domain-specific retrieval configuration for an agent.

    Controls which memory layers and tags an agent prefers when recalling,
    plus optional scoring weight overrides for the MemoryKernel.
    """
    agent_id: str
    domain: str
    preferred_layers: list[str] = field(default_factory=list)
    required_tags: list[str] = field(default_factory=list)
    scoring_overrides: dict[str, float] = field(default_factory=dict)
    max_results: int = 15
    token_budget: int = 16_000

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "preferred_layers": self.preferred_layers,
            "required_tags": self.required_tags,
            "scoring_overrides": self.scoring_overrides,
            "max_results": self.max_results,
            "token_budget": self.token_budget,
        }


class MemorySlice:
    """
    Filtered, isolated view of the MemoryKernel for a single agent.

    A MemorySlice auto-applies the agent's RetrievalProfile when recalling,
    ensuring each agent only sees memories relevant to its domain. Direct
    cross-agent memory access is not possible through slices.
    """

    def __init__(self, agent_id: str, memory_kernel: "MemoryKernel", profile: RetrievalProfile):
        self._agent_id = agent_id
        self._kernel = memory_kernel
        self._profile = profile

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def profile(self) -> RetrievalProfile:
        return self._profile

    def recall(
        self,
        query: str,
        max_results: int | None = None,
        extra_tags: list[str] | None = None,
        layer_override: list[str] | None = None,
        token_budget: int | None = None,
    ) -> "RecallResult":
        """Recall memories filtered by this agent's retrieval profile.

        The profile's preferred layers and required tags are always applied.
        Callers can narrow further with extra_tags or layer_override but
        cannot escape the profile's scoping.
        """
        from memory.memory_kernel import ScoringWeights

        layers = layer_override if layer_override else self._profile.preferred_layers or None
        tags = list(self._profile.required_tags)
        if extra_tags:
            tags.extend(extra_tags)

        scoring_weights = None
        if self._profile.scoring_overrides:
            scoring_weights = ScoringWeights(**self._profile.scoring_overrides)

        original_weights = self._kernel.weights
        if scoring_weights:
            self._kernel.weights = scoring_weights

        try:
            result = self._kernel.recall(
                query=query,
                max_results=max_results or self._profile.max_results,
                token_budget=token_budget or self._profile.token_budget,
                layer_filter=layers,
                required_tags=tags if tags else None,
            )
        finally:
            if scoring_weights:
                self._kernel.weights = original_weights

        return result

    def store(
        self,
        content: str,
        tags: list[str] | None = None,
        layer: str | None = None,
    ) -> dict[str, Any]:
        """Store a memory record, auto-tagged with agent domain."""
        combined_tags = list(self._profile.required_tags[:3])
        if tags:
            combined_tags.extend(tags)
        combined_tags = list(dict.fromkeys(combined_tags))

        return self._kernel.store(
            content=content,
            tags=combined_tags,
            source=f"agent:{self._agent_id}",
            layer=layer,
        )

    def stats(self) -> dict[str, Any]:
        """Get memory stats filtered to this agent's domain."""
        probe = self.recall("", max_results=1, token_budget=100)
        return {
            "agent_id": self._agent_id,
            "domain": self._profile.domain,
            "preferred_layers": self._profile.preferred_layers,
            "required_tags": self._profile.required_tags,
            "probe_candidates": probe.total_candidates,
        }


class AgentIsolationManager:
    """
    Manages memory isolation boundaries for all agents.

    Each registered agent gets its own MemorySlice backed by the shared
    MemoryKernel but filtered through the agent's RetrievalProfile.
    Cross-agent access is explicitly denied.
    """

    def __init__(self, memory_kernel: "MemoryKernel"):
        self._kernel = memory_kernel
        self._profiles: dict[str, RetrievalProfile] = {}
        self._slices: dict[str, MemorySlice] = {}

    def register(self, profile: RetrievalProfile) -> MemorySlice:
        """Register an agent's retrieval profile and create its memory slice."""
        agent_id = profile.agent_id
        self._profiles[agent_id] = profile
        mem_slice = MemorySlice(agent_id, self._kernel, profile)
        self._slices[agent_id] = mem_slice
        return mem_slice

    def get_slice(self, agent_id: str) -> MemorySlice | None:
        """Get an agent's memory slice. Returns None if not registered."""
        return self._slices.get(agent_id)

    def get_profile(self, agent_id: str) -> RetrievalProfile | None:
        """Get an agent's retrieval profile. Returns None if not registered."""
        return self._profiles.get(agent_id)

    def is_registered(self, agent_id: str) -> bool:
        return agent_id in self._profiles

    def all_profiles(self) -> list[RetrievalProfile]:
        return list(self._profiles.values())

    def status(self) -> dict[str, Any]:
        """Isolation manager health status."""
        return {
            "registered_agents": len(self._profiles),
            "agent_ids": list(self._profiles.keys()),
            "profiles": {aid: p.to_dict() for aid, p in self._profiles.items()},
        }
