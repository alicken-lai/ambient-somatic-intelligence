"""
Skill Candidate Generator — Generate candidate skill definitions from clusters.

Transforms a WorkflowClusterGroup into a SkillCandidate with proposed
inputs, outputs, routing conditions, governance level, and evidence
derived from the underlying workflow patterns.

Storage: agents/skillify/candidates.jsonl
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.skillify.workflow_cluster import WorkflowClusterGroup
from agents.skillify.pattern_miner import WorkflowPattern

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
CANDIDATES_PATH = AMBIENT_ROOT / "agents" / "skillify" / "candidates.jsonl"


@dataclass
class SkillCandidate:
    """A proposed skill definition generated from workflow patterns."""
    candidate_id: str
    proposed_name: str
    proposed_version: str
    description: str
    proposed_inputs: list[dict[str, Any]]
    proposed_outputs: list[dict[str, Any]]
    confidence_range: tuple[float, float]
    routing_conditions: list[str]
    memory_updates: list[str]
    governance_level: str
    observability_hooks: list[str]
    source_patterns: list[str]
    evidence: dict[str, Any]
    status: str
    created_at: datetime
    reviewed_at: datetime | None = None
    reviewer_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "proposed_name": self.proposed_name,
            "proposed_version": self.proposed_version,
            "description": self.description,
            "proposed_inputs": self.proposed_inputs,
            "proposed_outputs": self.proposed_outputs,
            "confidence_range": list(self.confidence_range),
            "routing_conditions": self.routing_conditions,
            "memory_updates": self.memory_updates,
            "governance_level": self.governance_level,
            "observability_hooks": self.observability_hooks,
            "source_patterns": self.source_patterns,
            "evidence": self.evidence,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewer_notes": self.reviewer_notes,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> SkillCandidate:
        cr = data.get("confidence_range", [0.5, 0.8])
        if isinstance(cr, list) and len(cr) == 2:
            confidence_range = (float(cr[0]), float(cr[1]))
        else:
            confidence_range = (0.5, 0.8)

        created_raw = data.get("created_at", "")
        try:
            created_at = datetime.fromisoformat(created_raw) if created_raw else datetime.now(timezone.utc)
        except ValueError:
            created_at = datetime.now(timezone.utc)

        reviewed_raw = data.get("reviewed_at")
        reviewed_at = None
        if reviewed_raw:
            try:
                reviewed_at = datetime.fromisoformat(reviewed_raw)
            except ValueError:
                pass

        return SkillCandidate(
            candidate_id=data.get("candidate_id", ""),
            proposed_name=data.get("proposed_name", ""),
            proposed_version=data.get("proposed_version", "0.1.0"),
            description=data.get("description", ""),
            proposed_inputs=data.get("proposed_inputs", []),
            proposed_outputs=data.get("proposed_outputs", []),
            confidence_range=confidence_range,
            routing_conditions=data.get("routing_conditions", []),
            memory_updates=data.get("memory_updates", []),
            governance_level=data.get("governance_level", "REVIEW_REQUIRED"),
            observability_hooks=data.get("observability_hooks", []),
            source_patterns=data.get("source_patterns", []),
            evidence=data.get("evidence", {}),
            status=data.get("status", "draft"),
            created_at=created_at,
            reviewed_at=reviewed_at,
            reviewer_notes=data.get("reviewer_notes", []),
        )


class SkillCandidateGenerator:
    """
    Generate candidate skill definitions from workflow cluster groups.

    Transforms the representative pattern and cluster statistics into a
    SkillCandidate ready for validation and governance review.

    Usage:
        gen = SkillCandidateGenerator()
        candidate = gen.generate(cluster_group)
    """

    def __init__(self, candidates_path: Path | str | None = None):
        self._candidates_path = Path(candidates_path) if candidates_path else CANDIDATES_PATH

    def generate(self, cluster: WorkflowClusterGroup) -> SkillCandidate:
        """Generate a SkillCandidate from a WorkflowClusterGroup."""
        rep = cluster.representative

        proposed_name = self._derive_name(rep)
        description = self._derive_description(cluster)
        proposed_inputs = self._derive_inputs(cluster)
        proposed_outputs = self._derive_outputs(cluster)
        confidence_range = self._derive_confidence(cluster)
        routing_conditions = self._derive_routing(cluster)
        memory_updates = self._derive_memory_updates(cluster)
        governance_level = self._derive_governance_level(cluster)
        observability_hooks = self._derive_observability_hooks(cluster)

        total_occurrences = sum(p.occurrence_count for p in cluster.patterns)
        avg_success = sum(p.success_rate for p in cluster.patterns) / max(len(cluster.patterns), 1)
        avg_duration = sum(p.avg_duration_ms for p in cluster.patterns) / max(len(cluster.patterns), 1)

        candidate = SkillCandidate(
            candidate_id=str(uuid.uuid4()),
            proposed_name=proposed_name,
            proposed_version="0.1.0",
            description=description,
            proposed_inputs=proposed_inputs,
            proposed_outputs=proposed_outputs,
            confidence_range=confidence_range,
            routing_conditions=routing_conditions,
            memory_updates=memory_updates,
            governance_level=governance_level,
            observability_hooks=observability_hooks,
            source_patterns=[p.pattern_id for p in cluster.patterns],
            evidence={
                "occurrence_count": total_occurrences,
                "success_rate": round(avg_success, 3),
                "avg_duration_ms": round(avg_duration, 1),
                "pattern_count": len(cluster.patterns),
                "skill_potential": cluster.skill_potential,
            },
            status="draft",
            created_at=datetime.now(timezone.utc),
        )

        self._persist(candidate)
        logger.info(
            "Generated skill candidate '%s' (id=%s) from %d patterns",
            proposed_name, candidate.candidate_id, len(cluster.patterns),
        )
        return candidate

    def _derive_name(self, pattern: WorkflowPattern) -> str:
        """Derive a concise skill name from the representative pattern."""
        wf = pattern.workflow_type
        clean = re.sub(r"[^a-z0-9_]", "_", wf.lower().strip())
        return f"auto_{clean}"

    def _derive_description(self, cluster: WorkflowClusterGroup) -> str:
        """Auto-generate a description from cluster data."""
        rep = cluster.representative
        steps_desc = " → ".join(rep.canonical_steps) if rep.canonical_steps else "N/A"
        return (
            f"Auto-generated skill from '{rep.workflow_type}' pattern. "
            f"Canonical flow: {steps_desc}. "
            f"Based on {rep.occurrence_count} observations with "
            f"{rep.success_rate:.0%} success rate."
        )

    def _derive_inputs(self, cluster: WorkflowClusterGroup) -> list[dict[str, Any]]:
        """Derive proposed inputs from pattern input schemas."""
        all_fields: dict[str, set[str]] = {}
        field_frequency: dict[str, int] = {}

        for pattern in cluster.patterns:
            for key, type_str in pattern.input_schema.items():
                if key not in all_fields:
                    all_fields[key] = set()
                    field_frequency[key] = 0
                all_fields[key].add(type_str)
                field_frequency[key] += 1

        total = len(cluster.patterns)
        inputs: list[dict[str, Any]] = []
        for key in sorted(all_fields):
            types = all_fields[key]
            freq = field_frequency[key]
            inputs.append({
                "name": key,
                "type": next(iter(types)) if len(types) == 1 else "Any",
                "required": freq == total,
            })
        return inputs

    def _derive_outputs(self, cluster: WorkflowClusterGroup) -> list[dict[str, Any]]:
        """Derive proposed outputs from pattern output schemas."""
        all_fields: dict[str, set[str]] = {}
        for pattern in cluster.patterns:
            for key, type_str in pattern.output_schema.items():
                if key not in all_fields:
                    all_fields[key] = set()
                all_fields[key].add(type_str)

        outputs: list[dict[str, Any]] = []
        for key in sorted(all_fields):
            types = all_fields[key]
            outputs.append({
                "name": key,
                "type": next(iter(types)) if len(types) == 1 else "Any",
            })
        return outputs

    def _derive_confidence(self, cluster: WorkflowClusterGroup) -> tuple[float, float]:
        """Derive confidence range from cluster success rates."""
        rates = [p.success_rate for p in cluster.patterns]
        if not rates:
            return (0.5, 0.8)
        low = round(min(rates) * 0.9, 2)
        high = round(max(rates), 2)
        return (max(0.0, low), min(1.0, high))

    def _derive_routing(self, cluster: WorkflowClusterGroup) -> list[str]:
        """Derive routing conditions from pattern workflow types."""
        types = {p.workflow_type for p in cluster.patterns}
        return [f"workflow_type == '{t}'" for t in sorted(types)]

    def _derive_memory_updates(self, cluster: WorkflowClusterGroup) -> list[str]:
        """Derive memory update hooks from pattern characteristics."""
        updates: list[str] = ["record_execution_result"]
        rep = cluster.representative
        if rep.success_rate < 0.9:
            updates.append("track_failure_patterns")
        if rep.avg_duration_ms > 2000:
            updates.append("log_performance_metrics")
        return updates

    def _derive_governance_level(self, cluster: WorkflowClusterGroup) -> str:
        """Derive governance level based on governance requirements presence."""
        all_gov: set[str] = set()
        for p in cluster.patterns:
            all_gov.update(p.governance_requirements)

        if not all_gov:
            return "ALLOW"
        if any("block" in g.lower() for g in all_gov):
            return "BLOCK"
        return "REVIEW_REQUIRED"

    def _derive_observability_hooks(self, cluster: WorkflowClusterGroup) -> list[str]:
        """Derive observability hooks for the candidate skill."""
        hooks = [
            "emit_start_event",
            "emit_completion_event",
            "record_duration_ms",
        ]
        rep = cluster.representative
        if rep.success_rate < 0.95:
            hooks.append("emit_failure_event")
        if rep.avg_duration_ms > 5000:
            hooks.append("emit_slow_execution_warning")
        return hooks

    def _persist(self, candidate: SkillCandidate) -> None:
        """Append candidate to the JSONL store."""
        self._candidates_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._candidates_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(candidate.to_dict(), ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Failed to persist skill candidate: %s", e)
