"""Validation rules for truth graph operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from kernel.truth.truth_edge import TruthEdge
from kernel.truth.truth_node import Mutability, TruthNode

if TYPE_CHECKING:
    from kernel.truth.truth_graph import TruthGraph


@dataclass
class ValidationIssue:
    code: str
    message: str
    node_id: str | None = None


@dataclass
class ValidationResult:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, code: str, message: str, node_id: str | None = None) -> None:
        self.issues.append(ValidationIssue(code=code, message=message, node_id=node_id))
        self.valid = False


class TruthValidator:
    """Enforces truth-layer invariants before registration."""

    STALE_THRESHOLD_SECONDS = 86_400  # 24h default staleness window

    def validate_node(self, node: TruthNode) -> ValidationResult:
        result = ValidationResult(valid=True)
        if not node.source.strip():
            result.add("missing_source", "source is required", node.id)
        if not node.owner.strip():
            result.add("missing_owner", "owner is required", node.id)
        if not node.verify_checksum():
            result.add("checksum_mismatch", "payload checksum does not match", node.id)
        return result

    def validate_edge(self, edge: TruthEdge, graph: TruthGraph) -> ValidationResult:
        result = ValidationResult(valid=True)
        if edge.source_id not in graph.nodes:
            result.add("unknown_source", f"unknown source node: {edge.source_id}", edge.source_id)
        if edge.target_id not in graph.nodes:
            result.add("unknown_target", f"unknown target node: {edge.target_id}", edge.target_id)
        return result

    def validate_registration(
        self,
        node: TruthNode,
        graph: TruthGraph,
    ) -> ValidationResult:
        """Full pre-registration validation."""
        result = self.validate_node(node)
        if node.id in graph.nodes:
            existing = graph.nodes[node.id]
            if existing.mutability == Mutability.IMMUTABLE:
                result.add(
                    "immutable_conflict",
                    f"cannot replace immutable node {node.id}",
                    node.id,
                )
            elif existing.version == node.version and existing.checksum == node.checksum:
                result.add("duplicate", f"duplicate registration for {node.id}", node.id)
        return result

    @staticmethod
    def parse_timestamp(ts: str) -> datetime | None:
        try:
            normalized = ts.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except (ValueError, TypeError):
            return None

    def is_stale(self, node: TruthNode, now: datetime | None = None) -> bool:
        parsed = self.parse_timestamp(node.timestamp)
        if parsed is None:
            return True
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        age = (current - parsed).total_seconds()
        return age > self.STALE_THRESHOLD_SECONDS
