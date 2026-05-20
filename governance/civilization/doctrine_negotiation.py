"""Doctrine negotiation — compare doctrines without merge or injection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DoctrineNegotiationVerdict:
    compatible: bool
    merge_forbidden: bool = True
    injection_blocked: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "compatible": self.compatible,
            "merge_forbidden": self.merge_forbidden,
            "injection_blocked": self.injection_blocked,
            "notes": list(self.notes),
        }


class DoctrineNegotiation:
    """Advisory comparison of foreign vs local doctrine fragments."""

    _INCOMPATIBLE_MARKERS = (
        "inject strategy without promotion",
        "alwaysapply: true",
        "replace canonical_rules",
        "hive mind doctrine",
    )

    def compare(self, local: str, foreign: str) -> DoctrineNegotiationVerdict:
        notes: list[str] = []
        compatible = True
        combined = f"{local}\n{foreign}".lower()
        for marker in self._INCOMPATIBLE_MARKERS:
            if marker in combined:
                compatible = False
                notes.append(f"incompatible:{marker[:40]}")
        if "merge doctrines" in combined or "unify doctrine" in combined:
            compatible = False
            notes.append("doctrine_merge_forbidden")
        return DoctrineNegotiationVerdict(
            compatible=compatible,
            notes=notes,
        )
