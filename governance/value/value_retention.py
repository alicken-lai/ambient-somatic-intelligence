"""Value retention — cap normative snapshot lifetime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_MAX_HOURS = 8760 * 2


@dataclass
class ValueRetentionVerdict:
    retained: bool
    capped_hours: float

    def to_dict(self) -> dict[str, Any]:
        return {"retained": self.retained, "capped_hours": round(self.capped_hours, 2)}


class ValueRetention:
    def cap(self, retention_hours: float) -> ValueRetentionVerdict:
        capped = min(max(1.0, retention_hours), _MAX_HOURS)
        return ValueRetentionVerdict(retained=True, capped_hours=capped)
