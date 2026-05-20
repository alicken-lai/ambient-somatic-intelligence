"""Civilization value anchor — local normative reference without universal morality."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CivilizationValueAnchor:
    runtime_id: str = "ambient"
    anchor_label: str = "bounded_local_normative"
    advisory_only: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "anchor_label": self.anchor_label,
            "advisory_only": self.advisory_only,
            "metadata": dict(self.metadata),
        }
