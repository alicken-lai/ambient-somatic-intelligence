"""Treaty decay — advisory freshness of inter-sovereign agreements."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from governance.civilization.treaty_record import TreatyRecord
from observability.v04.metric_normalizer import clamp01


@dataclass
class TreatyDecayVerdict:
    fresh: bool
    decay_factor: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "fresh": self.fresh,
            "decay_factor": round(self.decay_factor, 4),
        }


class TreatyDecay:
    def evaluate(self, treaty: TreatyRecord, *, max_age_hours: float = 720.0) -> TreatyDecayVerdict:
        try:
            created = datetime.fromisoformat(treaty.created_at.replace("Z", "+00:00"))
        except ValueError:
            return TreatyDecayVerdict(fresh=True, decay_factor=1.0)
        age_h = (datetime.now(timezone.utc) - created).total_seconds() / 3600.0
        factor = clamp01(1.0 - age_h / max(max_age_hours, 1.0))
        return TreatyDecayVerdict(fresh=factor >= 0.25, decay_factor=factor)
