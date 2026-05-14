"""
Execution History — Persistent per-agent task execution records.

Each agent maintains an append-only execution history stored at:
    state/agents/<agent-id>/history.jsonl

Records capture: task description, result status, duration, tokens used,
strategy applied, and timestamp. The history is queryable by time range,
task type, and success/failure, and provides aggregated stats and pattern
detection for strategy learning.
"""

from __future__ import annotations

import json
import os
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AGENTS_STATE_DIR = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os")) / "state" / "agents"


@dataclass
class ExecutionRecord:
    """A single task execution record."""
    task_type: str
    description: str
    status: str  # completed, error, skipped
    duration_ms: float
    tokens_used: int
    strategy: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "description": self.description,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 1),
            "tokens_used": self.tokens_used,
            "strategy": self.strategy,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ExecutionRecord":
        return ExecutionRecord(
            task_type=data.get("task_type", "unknown"),
            description=data.get("description", ""),
            status=data.get("status", "unknown"),
            duration_ms=data.get("duration_ms", 0),
            tokens_used=data.get("tokens_used", 0),
            strategy=data.get("strategy", ""),
            timestamp=data.get("timestamp", ""),
            metadata=data.get("metadata", {}),
        )


class ExecutionHistory:
    """
    Persistent execution history for a single agent.

    Provides:
        record()   — Append a new execution record
        recent()   — Get N most recent records
        stats()    — Aggregated performance statistics
        patterns() — Detect recurring execution patterns
        query()    — Filter by time range, type, or status
    """

    def __init__(self, agent_id: str, max_records: int = 1000):
        self.agent_id = agent_id
        self.max_records = max_records
        self._records: list[ExecutionRecord] = []
        self._state_dir = AGENTS_STATE_DIR / agent_id
        self._history_path = self._state_dir / "history.jsonl"
        self._load()

    def record(
        self,
        task_type: str,
        description: str,
        status: str,
        duration_ms: float,
        tokens_used: int = 0,
        strategy: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionRecord:
        """Record a task execution."""
        entry = ExecutionRecord(
            task_type=task_type,
            description=description,
            status=status,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            strategy=strategy,
            metadata=metadata or {},
        )
        self._records.append(entry)

        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records:]

        self._append_to_disk(entry)
        return entry

    def recent(self, n: int = 10) -> list[ExecutionRecord]:
        """Get the N most recent execution records."""
        return list(reversed(self._records[-n:]))

    def query(
        self,
        task_type: str | None = None,
        status: str | None = None,
        since_hours: float | None = None,
        limit: int = 50,
    ) -> list[ExecutionRecord]:
        """Query execution records with filters."""
        results = self._records

        if task_type:
            results = [r for r in results if r.task_type == task_type]

        if status:
            results = [r for r in results if r.status == status]

        if since_hours is not None:
            cutoff = time.time() - (since_hours * 3600)
            filtered = []
            for r in results:
                try:
                    ts = datetime.fromisoformat(r.timestamp.replace("Z", "+00:00"))
                    if ts.timestamp() >= cutoff:
                        filtered.append(r)
                except (ValueError, TypeError):
                    pass
            results = filtered

        return list(reversed(results[-limit:]))

    def stats(self) -> dict[str, Any]:
        """Aggregated execution statistics."""
        if not self._records:
            return {
                "agent_id": self.agent_id,
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
                "total_tokens": 0,
            }

        completed = [r for r in self._records if r.status == "completed"]
        failed = [r for r in self._records if r.status == "error"]
        durations = [r.duration_ms for r in self._records if r.duration_ms > 0]

        type_counts: dict[str, int] = {}
        for r in self._records:
            type_counts[r.task_type] = type_counts.get(r.task_type, 0) + 1

        return {
            "agent_id": self.agent_id,
            "total_executions": len(self._records),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": round(len(completed) / len(self._records), 3) if self._records else 0,
            "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else 0,
            "total_tokens": sum(r.tokens_used for r in self._records),
            "task_types": type_counts,
            "recent_trend": self._recent_trend(),
        }

    def patterns(self) -> dict[str, Any]:
        """Detect recurring execution patterns for strategy learning."""
        if len(self._records) < 3:
            return {"agent_id": self.agent_id, "patterns": [], "sample_size": len(self._records)}

        strategy_success: dict[str, list[bool]] = {}
        type_durations: dict[str, list[float]] = {}

        for r in self._records:
            if r.strategy:
                if r.strategy not in strategy_success:
                    strategy_success[r.strategy] = []
                strategy_success[r.strategy].append(r.status == "completed")

            if r.task_type not in type_durations:
                type_durations[r.task_type] = []
            type_durations[r.task_type].append(r.duration_ms)

        best_strategies: list[dict[str, Any]] = []
        for strategy, outcomes in strategy_success.items():
            if len(outcomes) >= 2:
                rate = sum(outcomes) / len(outcomes)
                best_strategies.append({
                    "strategy": strategy,
                    "success_rate": round(rate, 3),
                    "uses": len(outcomes),
                })
        best_strategies.sort(key=lambda s: s["success_rate"], reverse=True)

        slow_tasks: list[dict[str, Any]] = []
        for task_type, durations in type_durations.items():
            avg = sum(durations) / len(durations)
            if avg > 1000 and len(durations) >= 2:
                slow_tasks.append({
                    "task_type": task_type,
                    "avg_duration_ms": round(avg, 1),
                    "count": len(durations),
                })

        failure_clusters = Counter(
            r.task_type for r in self._records if r.status == "error"
        ).most_common(5)

        return {
            "agent_id": self.agent_id,
            "sample_size": len(self._records),
            "best_strategies": best_strategies[:5],
            "slow_tasks": slow_tasks,
            "failure_clusters": [{"task_type": t, "count": c} for t, c in failure_clusters],
        }

    def _recent_trend(self, window: int = 10) -> str:
        """Compute a simple trend indicator from recent records."""
        recent = self._records[-window:]
        if len(recent) < 3:
            return "insufficient_data"
        successes = sum(1 for r in recent if r.status == "completed")
        rate = successes / len(recent)
        if rate >= 0.9:
            return "excellent"
        if rate >= 0.7:
            return "good"
        if rate >= 0.5:
            return "fair"
        return "needs_attention"

    def _append_to_disk(self, record: ExecutionRecord) -> None:
        """Append a single record to the JSONL file."""
        self._state_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._history_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            pass

    def _load(self) -> None:
        """Load execution history from disk."""
        if not self._history_path.exists():
            return
        try:
            with open(self._history_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        self._records.append(ExecutionRecord.from_dict(data))
            if len(self._records) > self.max_records:
                self._records = self._records[-self.max_records:]
        except (json.JSONDecodeError, OSError):
            pass
