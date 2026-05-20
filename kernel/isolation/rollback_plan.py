"""Rollback plan — declared recovery strategy per execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RollbackType(str, Enum):
    NONE = "none"
    SNAPSHOT = "snapshot"
    COMPENSATING_WRITE = "compensating_write"
    MANUAL_REVIEW = "manual_review"
    IRREVERSIBLE_WITH_APPROVAL = "irreversible_with_approval"


HIGH_RISK_FORBIDDEN = frozenset({RollbackType.NONE})


@dataclass(frozen=True)
class RollbackPlan:
    rollback_type: RollbackType
    description: str = ""
    artifacts: tuple[str, ...] = ()
    guardian_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rollback_type": self.rollback_type.value,
            "description": self.description,
            "artifacts": list(self.artifacts),
            "guardian_reference": self.guardian_reference,
            "metadata": self.metadata,
        }

    def satisfies_high_risk(self) -> bool:
        return self.rollback_type not in HIGH_RISK_FORBIDDEN
