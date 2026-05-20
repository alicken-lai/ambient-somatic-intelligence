"""Frozen constitutional rule — immutable after constitution load."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConstitutionalRule:
    """Single constitutional constraint; frozen at load time."""

    rule_id: str
    name: str
    description: str
    severity: str = "block"  # block | warn
    immutable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "immutable": self.immutable,
        }
