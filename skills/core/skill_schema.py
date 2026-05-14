"""
Skill Schema — Formal type contracts for all skills in the Ambient OS skill layer.

Every skill declares its inputs, outputs, governance requirements, memory side effects,
and observability hooks via typed dataclass schemas. This replaces implicit script
contracts with explicit, validated, and routable skill definitions.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SkillInput:
    """Declares a single input parameter for a skill."""
    name: str
    type_hint: str
    required: bool
    description: str


@dataclass(frozen=True)
class SkillOutput:
    """Declares a single output field produced by a skill."""
    name: str
    type_hint: str
    description: str


@dataclass
class SkillMetadata:
    """Additional metadata attached to a skill registration."""
    author: str = "ambient-os"
    tags: list[str] = field(default_factory=list)
    category: str = "general"
    deprecated: bool = False
    migration_source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "author": self.author,
            "tags": self.tags,
            "category": self.category,
            "deprecated": self.deprecated,
            "migration_source": self.migration_source,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> SkillMetadata:
        return SkillMetadata(
            author=data.get("author", "ambient-os"),
            tags=data.get("tags", []),
            category=data.get("category", "general"),
            deprecated=data.get("deprecated", False),
            migration_source=data.get("migration_source"),
        )


@dataclass
class SkillContext:
    """Runtime context passed to a skill during execution."""
    task_description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    memory_context: dict[str, Any] = field(default_factory=dict)
    attention_state: dict[str, Any] = field(default_factory=dict)
    governance_clearance: str = "ALLOW"
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    invoked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class SkillResult:
    """Result returned by a skill execution."""
    success: bool
    outputs: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    memory_updates: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    trace_id: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "success": self.success,
            "outputs": self.outputs,
            "confidence": round(self.confidence, 4),
            "memory_updates": self.memory_updates,
            "execution_time_ms": round(self.execution_time_ms, 1),
            "trace_id": self.trace_id,
        }
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class SkillSchema:
    """
    Formal definition of a skill in the Ambient OS skill layer.

    Every skill must declare its interface, governance requirements, memory
    side effects, and observability hooks. The schema is validated before
    registration and enforced at execution time.
    """
    name: str
    version: str
    description: str
    inputs: list[SkillInput]
    outputs: list[SkillOutput]
    execute: Callable[[SkillContext], SkillResult]
    confidence_range: tuple[float, float] = (0.0, 1.0)
    routing_conditions: list[str] = field(default_factory=list)
    memory_updates: list[str] = field(default_factory=list)
    governance_level: str = "ALLOW"
    observability_hooks: list[str] = field(default_factory=list)
    metadata: SkillMetadata = field(default_factory=SkillMetadata)
    skill_id: str = field(default_factory=lambda: f"skill-{uuid.uuid4().hex[:12]}")
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    enabled: bool = True

    def run(self, context: SkillContext) -> SkillResult:
        """Execute the skill with timing and tracing."""
        start = time.monotonic()
        try:
            result = self.execute(context)
            result.execution_time_ms = (time.monotonic() - start) * 1000
            result.trace_id = context.trace_id
            logger.debug(
                "Skill '%s' completed in %.1fms (trace=%s)",
                self.name, result.execution_time_ms, result.trace_id,
            )
            return result
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error(
                "Skill '%s' failed after %.1fms: %s", self.name, elapsed, exc,
            )
            return SkillResult(
                success=False,
                error=str(exc),
                execution_time_ms=elapsed,
                trace_id=context.trace_id,
            )

    def matches_task(self, task_description: str) -> float:
        """Score how well this skill matches a task description (0.0–1.0)."""
        if not self.enabled:
            return 0.0
        desc_lower = task_description.lower()
        matched = sum(
            1 for kw in self.routing_conditions if kw.lower() in desc_lower
        )
        if not self.routing_conditions:
            return 0.0
        raw = matched / len(self.routing_conditions)
        lo, hi = self.confidence_range
        return lo + raw * (hi - lo)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "inputs": [
                {"name": i.name, "type_hint": i.type_hint,
                 "required": i.required, "description": i.description}
                for i in self.inputs
            ],
            "outputs": [
                {"name": o.name, "type_hint": o.type_hint,
                 "description": o.description}
                for o in self.outputs
            ],
            "confidence_range": list(self.confidence_range),
            "routing_conditions": self.routing_conditions,
            "memory_updates": self.memory_updates,
            "governance_level": self.governance_level,
            "observability_hooks": self.observability_hooks,
            "metadata": self.metadata.to_dict(),
            "created_at": self.created_at,
            "enabled": self.enabled,
        }
