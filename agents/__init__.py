"""
Persistent Specialized Agents — Phase 7 of Ambient OS Architecture Refactor.

Each agent is a stateful, domain-specialized cognitive unit:
  - Maintains local memory (domain experience, patterns, strategies)
  - Persists state across sessions (not ephemeral like sub-agents)
  - Has specialized retrieval (relevant to its domain)
  - Learns from execution history (improves over time)

  base.py          — BaseAgent framework with lifecycle and persistence
  registry.py      — AgentRegistry for discovery and coordination
  memory.py        — AgentMemory for per-agent local knowledge
  orchestrator.py  — AgentOrchestrator for multi-agent task dispatch
  specialists.py   — Domain-specific agent implementations
"""

from agents.base import BaseAgent, AgentCapability, AgentStatus
from agents.registry import AgentRegistry
from agents.memory import AgentMemory
from agents.orchestrator import AgentOrchestrator

__all__ = [
    "BaseAgent",
    "AgentCapability",
    "AgentStatus",
    "AgentRegistry",
    "AgentMemory",
    "AgentOrchestrator",
]
