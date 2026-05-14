"""
Pattern Miner — Mine successful and failed execution patterns from historical data.

Reads execution history JSONL files from state/agents/<agent_id>/history.jsonl
and MemoryKernel layers to identify recurring patterns that can inform
optimization decisions.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SuccessPattern:
    """A recurring successful execution pattern extracted from history."""
    pattern_id: str
    description: str
    frequency: int
    avg_duration: float
    agents_involved: list[str]
    success_rate: float
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "description": self.description,
            "frequency": self.frequency,
            "avg_duration": round(self.avg_duration, 1),
            "agents_involved": self.agents_involved,
            "success_rate": round(self.success_rate, 3),
            "confidence": round(self.confidence, 3),
        }


@dataclass
class FailurePattern:
    """A recurring failure mode extracted from history."""
    pattern_id: str
    description: str
    frequency: int
    failure_type: str
    agents_affected: list[str]
    potential_causes: list[str]
    severity: str  # low, medium, high, critical

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "description": self.description,
            "frequency": self.frequency,
            "failure_type": self.failure_type,
            "agents_affected": self.agents_affected,
            "potential_causes": self.potential_causes,
            "severity": self.severity,
        }


@dataclass
class CostAnalysis:
    """Cost analysis of execution paths."""
    high_cost_paths: list[dict[str, Any]]
    avg_cost_per_task_type: dict[str, float]
    total_tokens_consumed: int
    total_duration_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "high_cost_paths": self.high_cost_paths,
            "avg_cost_per_task_type": {
                k: round(v, 1) for k, v in self.avg_cost_per_task_type.items()
            },
            "total_tokens_consumed": self.total_tokens_consumed,
            "total_duration_ms": round(self.total_duration_ms, 1),
        }


@dataclass
class MemoryPatterns:
    """Combined patterns mined from MemoryKernel layers."""
    success_patterns: list[SuccessPattern]
    failure_patterns: list[FailurePattern]
    cost_analysis: CostAnalysis

    def to_dict(self) -> dict[str, Any]:
        return {
            "success_patterns": [p.to_dict() for p in self.success_patterns],
            "failure_patterns": [p.to_dict() for p in self.failure_patterns],
            "cost_analysis": self.cost_analysis.to_dict(),
        }


class PatternMiner:
    """
    Mine execution history for recurring success/failure patterns.

    Reads JSONL history files from the agents state directory and identifies
    statistical patterns that can be used to optimize future task execution.

    Usage:
        miner = PatternMiner()
        successes = miner.mine_success_patterns(min_occurrences=3)
        failures = miner.mine_failure_patterns(min_occurrences=2)
    """

    def __init__(self, history_dir: Path | str | None = None):
        if history_dir is None:
            from pathlib import Path as P
            import os
            root = P(os.environ.get("AMBIENT_OS_ROOT", P.home() / "ambient-os"))
            self._history_dir = root / "state" / "agents"
        else:
            self._history_dir = Path(history_dir)

    def mine_success_patterns(self, min_occurrences: int = 3) -> list[SuccessPattern]:
        """
        Find recurring successful workflow patterns across all agents.

        Analyzes which task types succeed most, which strategies work best,
        and which agent capabilities correlate with success.
        """
        all_records = self._load_all_history()
        if not all_records:
            logger.info("No execution history found for pattern mining")
            return []

        strategy_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"successes": 0, "total": 0, "durations": [], "agents": set()}
        )
        task_type_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"successes": 0, "total": 0, "durations": [], "agents": set()}
        )

        for agent_id, records in all_records.items():
            for rec in records:
                task_type = rec.get("task_type", "unknown")
                strategy = rec.get("strategy", "")
                status = rec.get("status", "")
                duration = rec.get("duration_ms", 0)

                task_type_stats[task_type]["total"] += 1
                task_type_stats[task_type]["agents"].add(agent_id)
                if status == "completed":
                    task_type_stats[task_type]["successes"] += 1
                    task_type_stats[task_type]["durations"].append(duration)

                if strategy:
                    strategy_stats[strategy]["total"] += 1
                    strategy_stats[strategy]["agents"].add(agent_id)
                    if status == "completed":
                        strategy_stats[strategy]["successes"] += 1
                        strategy_stats[strategy]["durations"].append(duration)

        patterns: list[SuccessPattern] = []

        for strategy, stats in strategy_stats.items():
            if stats["total"] < min_occurrences:
                continue
            success_rate = stats["successes"] / stats["total"]
            if success_rate < 0.6:
                continue

            durations = stats["durations"]
            avg_duration = sum(durations) / len(durations) if durations else 0
            confidence = min(1.0, stats["total"] / 10.0) * success_rate

            patterns.append(SuccessPattern(
                pattern_id=f"sp-{uuid.uuid4().hex[:8]}",
                description=f"Strategy '{strategy}' succeeds consistently",
                frequency=stats["total"],
                avg_duration=avg_duration,
                agents_involved=sorted(stats["agents"]),
                success_rate=success_rate,
                confidence=confidence,
            ))

        for task_type, stats in task_type_stats.items():
            if stats["total"] < min_occurrences:
                continue
            success_rate = stats["successes"] / stats["total"]
            if success_rate < 0.7:
                continue

            durations = stats["durations"]
            avg_duration = sum(durations) / len(durations) if durations else 0
            confidence = min(1.0, stats["total"] / 10.0) * success_rate

            patterns.append(SuccessPattern(
                pattern_id=f"sp-{uuid.uuid4().hex[:8]}",
                description=f"Task type '{task_type}' has high success rate",
                frequency=stats["total"],
                avg_duration=avg_duration,
                agents_involved=sorted(stats["agents"]),
                success_rate=success_rate,
                confidence=confidence,
            ))

        patterns.sort(key=lambda p: (p.confidence, p.frequency), reverse=True)
        logger.info("Mined %d success patterns from %d agents", len(patterns), len(all_records))
        return patterns

    def mine_failure_patterns(self, min_occurrences: int = 2) -> list[FailurePattern]:
        """
        Find recurring failure modes across all agents.

        Analyzes common failure reasons, failure cascades, and agent-specific
        failure modes.
        """
        all_records = self._load_all_history()
        if not all_records:
            return []

        failure_by_type: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "agents": set(), "errors": [], "task_types": []}
        )
        failure_by_task: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "agents": set(), "errors": []}
        )

        for agent_id, records in all_records.items():
            for rec in records:
                if rec.get("status") != "error":
                    continue

                task_type = rec.get("task_type", "unknown")
                error_msg = rec.get("metadata", {}).get("error", "unknown_error")
                failure_type = self._classify_failure(error_msg, task_type)

                failure_by_type[failure_type]["count"] += 1
                failure_by_type[failure_type]["agents"].add(agent_id)
                failure_by_type[failure_type]["errors"].append(error_msg)
                failure_by_type[failure_type]["task_types"].append(task_type)

                failure_by_task[task_type]["count"] += 1
                failure_by_task[task_type]["agents"].add(agent_id)
                failure_by_task[task_type]["errors"].append(error_msg)

        patterns: list[FailurePattern] = []

        for failure_type, stats in failure_by_type.items():
            if stats["count"] < min_occurrences:
                continue

            causes = self._infer_causes(stats["errors"])
            severity = self._assess_severity(stats["count"], len(stats["agents"]))

            patterns.append(FailurePattern(
                pattern_id=f"fp-{uuid.uuid4().hex[:8]}",
                description=f"Recurring '{failure_type}' failures",
                frequency=stats["count"],
                failure_type=failure_type,
                agents_affected=sorted(stats["agents"]),
                potential_causes=causes,
                severity=severity,
            ))

        for task_type, stats in failure_by_task.items():
            if stats["count"] < min_occurrences:
                continue

            causes = self._infer_causes(stats["errors"])
            severity = self._assess_severity(stats["count"], len(stats["agents"]))

            patterns.append(FailurePattern(
                pattern_id=f"fp-{uuid.uuid4().hex[:8]}",
                description=f"Task type '{task_type}' frequently fails",
                frequency=stats["count"],
                failure_type="task_specific",
                agents_affected=sorted(stats["agents"]),
                potential_causes=causes,
                severity=severity,
            ))

        patterns.sort(key=lambda p: p.frequency, reverse=True)
        logger.info("Mined %d failure patterns", len(patterns))
        return patterns

    def mine_from_memory(self, memory_kernel: Any) -> MemoryPatterns:
        """
        Mine patterns from MemoryKernel layers (episodic and procedural).

        Identifies high-cost context paths (long duration, many retries)
        and extracts execution patterns from memory records.
        """
        success_patterns: list[SuccessPattern] = []
        failure_patterns: list[FailurePattern] = []

        episodic_records = self._read_memory_layer(memory_kernel, "episodic")
        procedural_records = self._read_memory_layer(memory_kernel, "procedural")
        all_memory_records = episodic_records + procedural_records

        task_mentions: dict[str, int] = Counter()
        duration_mentions: list[float] = []
        token_mentions: list[int] = []

        for record in all_memory_records:
            content = record.get("content", "")
            tags = record.get("tags", [])

            for tag in tags:
                task_mentions[tag] += 1

            duration = self._extract_duration_from_content(content)
            if duration is not None:
                duration_mentions.append(duration)

            tokens = self._extract_tokens_from_content(content)
            if tokens is not None:
                token_mentions.append(tokens)

        frequent_tasks = [
            (task, count) for task, count in task_mentions.most_common(20)
            if count >= 3
        ]
        for task, count in frequent_tasks:
            success_patterns.append(SuccessPattern(
                pattern_id=f"mp-{uuid.uuid4().hex[:8]}",
                description=f"Frequently referenced task pattern: '{task}'",
                frequency=count,
                avg_duration=sum(duration_mentions) / len(duration_mentions) if duration_mentions else 0,
                agents_involved=[],
                success_rate=0.8,
                confidence=min(1.0, count / 10.0),
            ))

        high_cost_paths: list[dict[str, Any]] = []
        for record in all_memory_records:
            content = record.get("content", "")
            duration = self._extract_duration_from_content(content)
            if duration is not None and duration > 5000:
                high_cost_paths.append({
                    "content_preview": content[:200],
                    "estimated_duration_ms": duration,
                    "tags": record.get("tags", []),
                })

        avg_cost: dict[str, float] = {}
        for task, count in task_mentions.most_common(20):
            avg_cost[task] = sum(duration_mentions) / max(len(duration_mentions), 1)

        cost_analysis = CostAnalysis(
            high_cost_paths=high_cost_paths[:10],
            avg_cost_per_task_type=avg_cost,
            total_tokens_consumed=sum(token_mentions),
            total_duration_ms=sum(duration_mentions),
        )

        return MemoryPatterns(
            success_patterns=success_patterns,
            failure_patterns=failure_patterns,
            cost_analysis=cost_analysis,
        )

    def _load_all_history(self) -> dict[str, list[dict[str, Any]]]:
        """Load execution history for all agents."""
        all_records: dict[str, list[dict[str, Any]]] = {}

        if not self._history_dir.exists():
            logger.debug("History directory does not exist: %s", self._history_dir)
            return all_records

        for agent_dir in self._history_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            history_file = agent_dir / "history.jsonl"
            if not history_file.exists():
                continue

            records: list[dict[str, Any]] = []
            try:
                with history_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            except OSError as e:
                logger.warning("Failed to read history for %s: %s", agent_dir.name, e)
                continue

            if records:
                all_records[agent_dir.name] = records

        return all_records

    def _read_memory_layer(self, memory_kernel: Any, layer: str) -> list[dict[str, Any]]:
        """Read records from a MemoryKernel layer file."""
        records: list[dict[str, Any]] = []
        try:
            layer_file = memory_kernel.memory_dir / layer / "records.jsonl"
            if not layer_file.exists():
                return records
            with layer_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except (AttributeError, OSError) as e:
            logger.warning("Failed to read memory layer '%s': %s", layer, e)
        return records

    def _classify_failure(self, error_msg: str, task_type: str) -> str:
        """Classify a failure into a category based on error message."""
        error_lower = error_msg.lower()
        if "timeout" in error_lower:
            return "timeout"
        if "permission" in error_lower or "denied" in error_lower:
            return "permission_denied"
        if "not found" in error_lower or "missing" in error_lower:
            return "resource_not_found"
        if "connection" in error_lower or "network" in error_lower:
            return "network_error"
        if "memory" in error_lower or "oom" in error_lower:
            return "resource_exhaustion"
        if "rate limit" in error_lower or "throttl" in error_lower:
            return "rate_limited"
        return "unclassified"

    def _infer_causes(self, errors: list[str]) -> list[str]:
        """Infer potential causes from a collection of error messages."""
        causes: list[str] = []
        error_lower = " ".join(errors).lower()

        if "timeout" in error_lower:
            causes.append("Task execution exceeding time limits")
        if "permission" in error_lower or "denied" in error_lower:
            causes.append("Insufficient agent permissions or policy blocking")
        if "not found" in error_lower:
            causes.append("Required resources or dependencies unavailable")
        if "connection" in error_lower:
            causes.append("Network connectivity issues")
        if "rate limit" in error_lower:
            causes.append("External API rate limits being hit")

        if not causes:
            causes.append("Undetermined — requires manual investigation")

        return causes

    def _assess_severity(self, frequency: int, agent_count: int) -> str:
        """Assess severity based on frequency and breadth of impact."""
        if frequency >= 10 or agent_count >= 3:
            return "critical"
        if frequency >= 5 or agent_count >= 2:
            return "high"
        if frequency >= 3:
            return "medium"
        return "low"

    def _extract_duration_from_content(self, content: str) -> float | None:
        """Try to extract a duration value from memory content."""
        import re
        match = re.search(r"duration[_:\s]*(\d+(?:\.\d+)?)\s*(?:ms)?", content.lower())
        if match:
            return float(match.group(1))
        return None

    def _extract_tokens_from_content(self, content: str) -> int | None:
        """Try to extract a token count from memory content."""
        import re
        match = re.search(r"tokens?[_:\s]*(\d+)", content.lower())
        if match:
            return int(match.group(1))
        return None
