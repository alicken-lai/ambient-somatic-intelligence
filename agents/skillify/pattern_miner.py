"""
Pattern Miner — Mine recurring workflow patterns from observations.

Builds on the conceptual approach of memory.evolution.pattern_miner but
operates on WorkflowEvent observations instead of raw execution history.
Identifies canonical step sequences and computes statistical profiles.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.skillify.workflow_observer import WorkflowEvent, WorkflowStep

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
HISTORY_DIR = AMBIENT_ROOT / "state" / "agents"


@dataclass
class WorkflowPattern:
    """A recurring workflow pattern extracted from observations."""
    pattern_id: str
    workflow_type: str
    canonical_steps: list[str]
    occurrence_count: int
    success_rate: float
    avg_duration_ms: float
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    variation_score: float
    governance_requirements: list[str]
    first_seen: datetime
    last_seen: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "workflow_type": self.workflow_type,
            "canonical_steps": self.canonical_steps,
            "occurrence_count": self.occurrence_count,
            "success_rate": round(self.success_rate, 3),
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "variation_score": round(self.variation_score, 3),
            "governance_requirements": self.governance_requirements,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> WorkflowPattern:
        def _parse_ts(raw: Any) -> datetime:
            if isinstance(raw, str):
                try:
                    return datetime.fromisoformat(raw)
                except ValueError:
                    pass
            return datetime.now(timezone.utc)

        return WorkflowPattern(
            pattern_id=data.get("pattern_id", ""),
            workflow_type=data.get("workflow_type", ""),
            canonical_steps=data.get("canonical_steps", []),
            occurrence_count=data.get("occurrence_count", 0),
            success_rate=data.get("success_rate", 0.0),
            avg_duration_ms=data.get("avg_duration_ms", 0.0),
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
            variation_score=data.get("variation_score", 0.0),
            governance_requirements=data.get("governance_requirements", []),
            first_seen=_parse_ts(data.get("first_seen")),
            last_seen=_parse_ts(data.get("last_seen")),
        )


class SkillifyPatternMiner:
    """
    Mine recurring workflow patterns from WorkflowEvent observations.

    Groups events by workflow_type, identifies canonical step sequences,
    and computes statistical profiles (success rate, duration, variation).

    Usage:
        miner = SkillifyPatternMiner()
        patterns = miner.mine(observations, min_support=3)
        patterns = miner.mine_from_history()
    """

    def mine(
        self,
        observations: list[WorkflowEvent],
        min_support: int = 3,
    ) -> list[WorkflowPattern]:
        """
        Mine patterns from a list of workflow observations.

        A pattern must appear at least `min_support` times to be included.
        """
        if not observations:
            return []

        by_type: dict[str, list[WorkflowEvent]] = defaultdict(list)
        for event in observations:
            by_type[event.workflow_type].append(event)

        patterns: list[WorkflowPattern] = []
        for wf_type, events in by_type.items():
            if len(events) < min_support:
                continue

            pattern = self._build_pattern(wf_type, events)
            patterns.append(pattern)

        patterns.sort(key=lambda p: (p.success_rate, p.occurrence_count), reverse=True)
        logger.info(
            "Mined %d patterns from %d observations (%d workflow types)",
            len(patterns), len(observations), len(by_type),
        )
        return patterns

    def mine_from_history(
        self,
        history_dir: str | None = None,
        min_support: int = 3,
    ) -> list[WorkflowPattern]:
        """
        Mine patterns from existing agent execution history JSONL files.

        Reads state/agents/<agent_id>/history.jsonl and converts records
        into WorkflowEvents for pattern extraction.
        """
        target_dir = Path(history_dir) if history_dir else HISTORY_DIR
        if not target_dir.exists():
            logger.debug("History directory does not exist: %s", target_dir)
            return []

        events: list[WorkflowEvent] = []
        for agent_dir in target_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            history_file = agent_dir / "history.jsonl"
            if not history_file.exists():
                continue

            try:
                with history_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                            event = self._record_to_event(rec, agent_dir.name)
                            events.append(event)
                        except (json.JSONDecodeError, KeyError):
                            continue
            except OSError as e:
                logger.warning("Failed to read history for %s: %s", agent_dir.name, e)

        logger.info("Loaded %d events from execution history", len(events))
        return self.mine(events, min_support=min_support)

    def _build_pattern(
        self,
        workflow_type: str,
        events: list[WorkflowEvent],
    ) -> WorkflowPattern:
        """Build a WorkflowPattern from a group of same-type events."""
        successes = sum(1 for e in events if e.success)
        durations = [e.duration_ms for e in events]
        timestamps = [e.timestamp for e in events]

        canonical_steps = self._extract_canonical_steps(events)
        input_schema = self._infer_schema(e.inputs for e in events)
        output_schema = self._infer_schema(e.outputs for e in events)
        variation = self._compute_variation(events)

        all_gov: set[str] = set()
        for e in events:
            all_gov.update(e.governance_checks)

        return WorkflowPattern(
            pattern_id=f"wp-{uuid.uuid4().hex[:8]}",
            workflow_type=workflow_type,
            canonical_steps=canonical_steps,
            occurrence_count=len(events),
            success_rate=successes / len(events) if events else 0.0,
            avg_duration_ms=sum(durations) / len(durations) if durations else 0.0,
            input_schema=input_schema,
            output_schema=output_schema,
            variation_score=variation,
            governance_requirements=sorted(all_gov),
            first_seen=min(timestamps),
            last_seen=max(timestamps),
        )

    def _extract_canonical_steps(self, events: list[WorkflowEvent]) -> list[str]:
        """Find the most common step sequence across events."""
        step_sequences: list[list[str]] = []
        for event in events:
            seq = [step.step_name for step in event.steps]
            step_sequences.append(seq)

        if not step_sequences:
            return []

        # Use the most frequent sequence length, then pick the most common step at each position
        from collections import Counter
        length_counts = Counter(len(s) for s in step_sequences)
        canonical_len = length_counts.most_common(1)[0][0]

        canonical: list[str] = []
        matching = [s for s in step_sequences if len(s) == canonical_len]
        if not matching:
            matching = step_sequences

        for i in range(canonical_len):
            steps_at_pos = [s[i] for s in matching if i < len(s)]
            if steps_at_pos:
                most_common = Counter(steps_at_pos).most_common(1)[0][0]
                canonical.append(most_common)

        return canonical

    def _infer_schema(self, dicts_iter: Any) -> dict[str, str]:
        """Infer a common key→type schema from multiple dicts."""
        field_types: dict[str, set[str]] = defaultdict(set)
        for d in dicts_iter:
            if not isinstance(d, dict):
                continue
            for key, val in d.items():
                field_types[key].add(type(val).__name__)

        schema: dict[str, str] = {}
        for key, types in sorted(field_types.items()):
            schema[key] = "|".join(sorted(types)) if len(types) > 1 else next(iter(types))
        return schema

    def _compute_variation(self, events: list[WorkflowEvent]) -> float:
        """
        Compute variation score (0.0 = identical, 1.0 = completely different).

        Based on step sequence diversity and duration variance.
        """
        if len(events) <= 1:
            return 0.0

        unique_sequences = set()
        for e in events:
            seq_key = tuple(s.step_name for s in e.steps)
            unique_sequences.add(seq_key)

        sequence_variation = (len(unique_sequences) - 1) / max(len(events) - 1, 1)

        durations = [e.duration_ms for e in events if e.duration_ms > 0]
        if len(durations) >= 2:
            mean_d = sum(durations) / len(durations)
            if mean_d > 0:
                variance = sum((d - mean_d) ** 2 for d in durations) / len(durations)
                cv = (variance ** 0.5) / mean_d
                duration_variation = min(cv, 1.0)
            else:
                duration_variation = 0.0
        else:
            duration_variation = 0.0

        return round(0.6 * sequence_variation + 0.4 * duration_variation, 3)

    def _record_to_event(self, record: dict[str, Any], agent_id: str) -> WorkflowEvent:
        """Convert an execution history record to a WorkflowEvent."""
        from datetime import datetime, timezone
        import uuid as _uuid

        ts_raw = record.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")) if ts_raw else datetime.now(timezone.utc)
        except ValueError:
            ts = datetime.now(timezone.utc)

        status = record.get("status", "unknown")
        task_type = record.get("task_type", "unknown")

        steps = [
            WorkflowStep(
                step_name=record.get("strategy", task_type),
                module="agents",
                function="execute",
                duration_ms=record.get("duration_ms", 0.0),
                success=status == "completed",
            )
        ]

        return WorkflowEvent(
            event_id=str(_uuid.uuid4()),
            timestamp=ts,
            workflow_type=task_type,
            steps=steps,
            inputs={"description": record.get("description", "")},
            outputs=record.get("metadata", {}),
            success=status == "completed",
            duration_ms=record.get("duration_ms", 0.0),
            agent_id=agent_id,
            governance_checks=[],
        )
