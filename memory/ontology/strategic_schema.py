"""L4 Strategic Memory schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .layer_definition import MemoryLayer


@dataclass
class StrategicEntry:
    entry_id: str
    timestamp: datetime
    source_skills: list[str]
    heuristic: str
    applicability_scope: str
    confidence: float
    validation_count: int = 0
    cross_project_validations: list[str] = field(default_factory=list)
    governance_approval_id: str = ""
    verifier_id: str = ""
    last_applied: datetime | None = None
    contradiction_count: int = 0
    layer: MemoryLayer = MemoryLayer.L4_STRATEGIC

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "source_skills": list(self.source_skills),
            "heuristic": self.heuristic,
            "applicability_scope": self.applicability_scope,
            "confidence": self.confidence,
            "validation_count": self.validation_count,
            "cross_project_validations": list(self.cross_project_validations),
            "governance_approval_id": self.governance_approval_id,
            "verifier_id": self.verifier_id,
            "last_applied": (
                self.last_applied.isoformat() if self.last_applied else None
            ),
            "contradiction_count": self.contradiction_count,
            "layer": self.layer.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategicEntry:
        return cls(
            entry_id=data["entry_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source_skills=data["source_skills"],
            heuristic=data["heuristic"],
            applicability_scope=data["applicability_scope"],
            confidence=data["confidence"],
            validation_count=data.get("validation_count", 0),
            cross_project_validations=data.get("cross_project_validations", []),
            governance_approval_id=data.get("governance_approval_id", ""),
            verifier_id=data.get("verifier_id", ""),
            last_applied=(
                datetime.fromisoformat(data["last_applied"])
                if data.get("last_applied")
                else None
            ),
            contradiction_count=data.get("contradiction_count", 0),
            layer=MemoryLayer(data.get("layer", MemoryLayer.L4_STRATEGIC)),
        )

    def is_valid(self) -> bool:
        return bool(self.governance_approval_id)

    def apply_contradiction(self) -> None:
        self.contradiction_count += 1
