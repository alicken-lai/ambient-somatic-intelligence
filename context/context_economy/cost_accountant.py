"""
Context Cost Accountant — Granular context cost tracking.

Records every token-consuming operation across agents and tasks so we can
answer questions like:
  - How many tokens did agent X spend on retrieval today?
  - What is the cost breakdown for task T?
  - Which operations consume the most tokens system-wide?

Persists cost records to observability/context_costs/ in JSONL format,
following the same pattern as InjectionLogger.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
COST_LOG_DIR = AMBIENT_ROOT / "observability" / "context_costs"


class CostOperation(str, Enum):
    """Types of token-consuming context operations."""
    RETRIEVAL = "retrieval"
    INJECTION = "injection"
    COMPRESSION = "compression"
    ASSEMBLY = "assembly"


@dataclass
class CostRecord:
    """A single context cost event."""
    agent_id: str
    task_id: str
    operation: CostOperation
    tokens: int
    source: str
    utility_score: float = 0.0
    timestamp: float = field(default_factory=time.time)
    record_id: str = ""

    def __post_init__(self):
        if not self.record_id:
            self.record_id = f"cost_{int(self.timestamp * 1000)}"

    @property
    def cost_efficiency(self) -> float:
        """Utility per token — higher is better."""
        if self.tokens <= 0:
            return 0.0
        return self.utility_score / self.tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "operation": self.operation.value,
            "tokens": self.tokens,
            "source": self.source,
            "utility_score": round(self.utility_score, 4),
            "cost_efficiency": round(self.cost_efficiency, 6),
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


@dataclass
class CostSummary:
    """Aggregated cost summary over a set of records."""
    total_tokens: int
    by_agent: dict[str, int]
    by_operation: dict[str, int]
    by_source: dict[str, int]
    efficiency_score: float
    record_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_tokens": self.total_tokens,
            "record_count": self.record_count,
            "by_agent": self.by_agent,
            "by_operation": self.by_operation,
            "by_source": self.by_source,
            "efficiency_score": round(self.efficiency_score, 4),
        }


class ContextCostAccountant:
    """
    Tracks context costs at a granular level across agents, tasks, and operations.

    Usage:
        accountant = ContextCostAccountant()
        accountant.record_cost("agent-1", "task-42", CostOperation.RETRIEVAL, 500, "memory_kernel")
        summary = accountant.get_system_costs()
    """

    def __init__(self, persist: bool = True, max_records: int = 2000):
        self._records: list[CostRecord] = []
        self._max_records = max_records
        self._persist = persist

        if persist:
            COST_LOG_DIR.mkdir(parents=True, exist_ok=True)

    def record_cost(
        self,
        agent_id: str,
        task_id: str,
        operation: CostOperation,
        tokens: int,
        source: str,
        utility_score: float = 0.0,
    ) -> CostRecord:
        """Log a context cost event."""
        record = CostRecord(
            agent_id=agent_id,
            task_id=task_id,
            operation=operation,
            tokens=tokens,
            source=source,
            utility_score=utility_score,
        )

        self._records.append(record)
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]

        if self._persist:
            self._persist_record(record)

        logger.debug(
            "Cost recorded: agent=%s task=%s op=%s tokens=%d",
            agent_id, task_id, operation.value, tokens,
        )
        return record

    def get_agent_costs(
        self,
        agent_id: str,
        time_range: tuple[float, float] | None = None,
    ) -> CostSummary:
        """Get total costs and breakdown for a specific agent."""
        filtered = [r for r in self._records if r.agent_id == agent_id]
        if time_range:
            start, end = time_range
            filtered = [r for r in filtered if start <= r.timestamp <= end]
        return self._summarize(filtered)

    def get_task_costs(self, task_id: str) -> CostSummary:
        """Get costs for a specific task."""
        filtered = [r for r in self._records if r.task_id == task_id]
        return self._summarize(filtered)

    def get_system_costs(
        self,
        time_range: tuple[float, float] | None = None,
    ) -> CostSummary:
        """Get system-wide cost summary."""
        filtered = list(self._records)
        if time_range:
            start, end = time_range
            filtered = [r for r in filtered if start <= r.timestamp <= end]
        return self._summarize(filtered)

    def recent_records(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get the most recent cost records."""
        return [r.to_dict() for r in self._records[-limit:]]

    def _summarize(self, records: list[CostRecord]) -> CostSummary:
        """Build an aggregate summary from a list of records."""
        if not records:
            return CostSummary(
                total_tokens=0,
                by_agent={},
                by_operation={},
                by_source={},
                efficiency_score=0.0,
                record_count=0,
            )

        by_agent: dict[str, int] = defaultdict(int)
        by_operation: dict[str, int] = defaultdict(int)
        by_source: dict[str, int] = defaultdict(int)
        total_tokens = 0
        total_utility = 0.0

        for r in records:
            by_agent[r.agent_id] += r.tokens
            by_operation[r.operation.value] += r.tokens
            by_source[r.source] += r.tokens
            total_tokens += r.tokens
            total_utility += r.utility_score

        efficiency = total_utility / total_tokens if total_tokens > 0 else 0.0

        return CostSummary(
            total_tokens=total_tokens,
            by_agent=dict(by_agent),
            by_operation=dict(by_operation),
            by_source=dict(by_source),
            efficiency_score=efficiency,
            record_count=len(records),
        )

    def _persist_record(self, record: CostRecord) -> None:
        """Append record to disk as JSONL."""
        try:
            date_str = datetime.fromtimestamp(
                record.timestamp, tz=timezone.utc
            ).strftime("%Y-%m-%d")
            filepath = COST_LOG_DIR / f"costs_{date_str}.jsonl"
            with filepath.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            logger.warning("Failed to persist cost record to %s", COST_LOG_DIR)
