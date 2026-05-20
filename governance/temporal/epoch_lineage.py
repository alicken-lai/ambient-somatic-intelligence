"""Epoch lineage — bounded parent links without false inheritance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EpochLineageNode:
    epoch_id: str
    parent_epoch_id: str | None = None
    depth: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "epoch_id": self.epoch_id,
            "parent_epoch_id": self.parent_epoch_id,
            "depth": self.depth,
        }


@dataclass
class EpochLineageVerdict:
    lineage_valid: bool
    max_depth: int = 0
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_valid": self.lineage_valid,
            "max_depth": self.max_depth,
            "issues": list(self.issues),
        }


class EpochLineage:
    _MAX_DEPTH = 8

    def validate_chain(self, nodes: list[EpochLineageNode]) -> EpochLineageVerdict:
        issues: list[str] = []
        depth = max((n.depth for n in nodes), default=0)
        if depth > self._MAX_DEPTH:
            issues.append("lineage_depth_exceeded")
        ids = {n.epoch_id for n in nodes}
        if len(ids) != len(nodes):
            issues.append("duplicate_epoch_in_lineage")
        for n in nodes:
            if n.parent_epoch_id and n.parent_epoch_id not in ids and n.depth > 0:
                issues.append(f"orphan_parent:{n.epoch_id}")
        return EpochLineageVerdict(
            lineage_valid=len(issues) == 0,
            max_depth=depth,
            issues=issues,
        )
