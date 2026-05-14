"""
Cognition Tracer — Traces the system's own cognitive processes.

Captures higher-level cognitive operations beyond raw task execution:
  - Routing decisions (which agent handles what)
  - Retrieval decisions (what memories to recall)
  - Scheduling decisions (task ordering and priority)
  - Governance decisions (approval/denial reasoning)
  - Attention decisions (focus allocation)
  - Evolution decisions (self-improvement proposals)

Each trace captures inputs, outputs, rationale, and duration, enabling
the system to observe its own decision-making patterns over time.

Persists to: observability/cognition_traces/traces_YYYY-MM-DD.jsonl
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
COGNITION_TRACES_DIR = AMBIENT_ROOT / "observability" / "cognition_traces"


class DecisionType(str, Enum):
    """Types of cognitive decisions the system can make."""
    ROUTING = "routing"
    RETRIEVAL = "retrieval"
    SCHEDULING = "scheduling"
    GOVERNANCE = "governance"
    ATTENTION = "attention"
    EVOLUTION = "evolution"


@dataclass
class CognitionTrace:
    """A single cognitive decision trace."""
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    decision_type: DecisionType = DecisionType.ROUTING
    timestamp: float = field(default_factory=time.time)
    inputs: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    duration_ms: float = 0.0
    agent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "trace_id": self.trace_id,
            "decision_type": self.decision_type.value,
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "inputs": self.inputs,
            "output": self.output,
            "rationale": self.rationale,
            "duration_ms": round(self.duration_ms, 2),
            "agent_id": self.agent_id,
            "metadata": self.metadata,
        }


@dataclass
class ReasoningStep:
    """A single step in a multi-step reasoning chain."""
    step_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    description: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "step_id": self.step_id,
            "description": self.description,
            "inputs": self.inputs,
            "output": self.output,
            "duration_ms": round(self.duration_ms, 2),
        }


@dataclass
class ReasoningChain:
    """A multi-step reasoning process."""
    chain_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    steps: list[ReasoningStep] = field(default_factory=list)
    total_duration: float = 0.0
    outcome: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "chain_id": self.chain_id,
            "steps": [s.to_dict() for s in self.steps],
            "total_duration_ms": round(self.total_duration, 2),
            "outcome": self.outcome,
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "metadata": self.metadata,
        }


class CognitionTracer:
    """
    Traces the system's own cognitive processes.

    Captures higher-level decisions — routing, retrieval, scheduling,
    governance, attention, evolution — with full context including
    inputs, outputs, rationale, and timing.

    Usage:
        tracer = CognitionTracer()

        tracer.trace_decision(
            decision_type=DecisionType.ROUTING,
            inputs={"task": "implement login", "available_agents": ["frontend", "backend"]},
            output={"chosen_agent": "frontend"},
            rationale="Task is UI-focused, frontend agent has relevant experience",
            duration=0.045,
        )

        traces = tracer.query_traces(decision_type=DecisionType.ROUTING)
    """

    def __init__(self, persist: bool = True, max_traces: int = 1000):
        self._traces: list[CognitionTrace] = []
        self._chains: list[ReasoningChain] = []
        self._max_traces = max_traces
        self._persist = persist

        if persist:
            COGNITION_TRACES_DIR.mkdir(parents=True, exist_ok=True)

    def trace_decision(
        self,
        decision_type: DecisionType | str,
        inputs: dict[str, Any],
        output: dict[str, Any],
        rationale: str = "",
        duration: float = 0.0,
        agent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CognitionTrace:
        """
        Log a cognitive decision.

        Args:
            decision_type: Category of decision (ROUTING, RETRIEVAL, etc.)
            inputs: What information was available for the decision
            output: What was decided
            rationale: Why this decision was made
            duration: How long the decision took (seconds)
            agent_id: Which agent made the decision (if applicable)
            metadata: Additional context
        """
        if isinstance(decision_type, str):
            decision_type = DecisionType(decision_type)

        trace = CognitionTrace(
            decision_type=decision_type,
            inputs=inputs,
            output=output,
            rationale=rationale,
            duration_ms=duration * 1000,
            agent_id=agent_id,
            metadata=metadata or {},
        )

        self._traces.append(trace)
        if len(self._traces) > self._max_traces:
            self._traces = self._traces[-self._max_traces:]

        if self._persist:
            self._persist_trace(trace)

        logger.debug(
            "Cognition trace: %s [%s] %.1fms",
            decision_type.value, trace.trace_id, trace.duration_ms
        )
        return trace

    def trace_reasoning_chain(
        self,
        chain_id: str | None = None,
        steps: list[dict[str, Any]] | None = None,
        outcome: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ReasoningChain:
        """
        Log a multi-step reasoning process.

        Args:
            chain_id: Optional explicit chain ID
            steps: List of step dicts with description, inputs, output, duration_ms
            outcome: Final outcome of the reasoning chain
            metadata: Additional context
        """
        reasoning_steps = []
        total_duration = 0.0

        for step_data in (steps or []):
            step = ReasoningStep(
                description=step_data.get("description", ""),
                inputs=step_data.get("inputs", {}),
                output=step_data.get("output", {}),
                duration_ms=step_data.get("duration_ms", 0.0),
            )
            reasoning_steps.append(step)
            total_duration += step.duration_ms

        chain = ReasoningChain(
            chain_id=chain_id or uuid.uuid4().hex[:16],
            steps=reasoning_steps,
            total_duration=total_duration,
            outcome=outcome,
            metadata=metadata or {},
        )

        self._chains.append(chain)
        if len(self._chains) > self._max_traces:
            self._chains = self._chains[-self._max_traces:]

        if self._persist:
            self._persist_chain(chain)

        logger.debug(
            "Reasoning chain: %s [%d steps] %.1fms → %s",
            chain.chain_id, len(chain.steps), chain.total_duration, chain.outcome
        )
        return chain

    def get_cognition_trace(self, trace_id: str) -> CognitionTrace | None:
        """Retrieve a specific cognition trace by ID."""
        for trace in self._traces:
            if trace.trace_id == trace_id:
                return trace
        return None

    def query_traces(
        self,
        decision_type: DecisionType | str | None = None,
        time_range: tuple[float, float] | None = None,
        agent_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Query cognition traces with optional filters.

        Args:
            decision_type: Filter by decision type
            time_range: Tuple of (start_time, end_time) as Unix timestamps
            agent_id: Filter by agent
            limit: Maximum results to return
        """
        if isinstance(decision_type, str):
            decision_type = DecisionType(decision_type)

        filtered = self._traces

        if decision_type is not None:
            filtered = [t for t in filtered if t.decision_type == decision_type]

        if time_range is not None:
            start, end = time_range
            filtered = [t for t in filtered if start <= t.timestamp <= end]

        if agent_id is not None:
            filtered = [t for t in filtered if t.agent_id == agent_id]

        filtered = sorted(filtered, key=lambda t: t.timestamp, reverse=True)
        return [t.to_dict() for t in filtered[:limit]]

    def stats(self) -> dict[str, Any]:
        """Get aggregate statistics on cognition traces."""
        if not self._traces:
            return {
                "total_traces": 0,
                "total_chains": len(self._chains),
                "by_type": {},
                "avg_duration_ms": 0.0,
            }

        by_type: dict[str, int] = {}
        total_duration = 0.0

        for trace in self._traces:
            by_type[trace.decision_type.value] = by_type.get(trace.decision_type.value, 0) + 1
            total_duration += trace.duration_ms

        return {
            "total_traces": len(self._traces),
            "total_chains": len(self._chains),
            "by_type": by_type,
            "avg_duration_ms": round(total_duration / len(self._traces), 2),
        }

    def _persist_trace(self, trace: CognitionTrace) -> None:
        """Append trace to daily JSONL file."""
        try:
            date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            filepath = COGNITION_TRACES_DIR / f"traces_{date_str}.jsonl"
            with filepath.open("a", encoding="utf-8") as f:
                f.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            logger.warning("Failed to persist cognition trace %s", trace.trace_id)

    def _persist_chain(self, chain: ReasoningChain) -> None:
        """Append reasoning chain to daily JSONL file."""
        try:
            date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            filepath = COGNITION_TRACES_DIR / f"traces_{date_str}.jsonl"
            record = {"type": "reasoning_chain", **chain.to_dict()}
            with filepath.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            logger.warning("Failed to persist reasoning chain %s", chain.chain_id)
