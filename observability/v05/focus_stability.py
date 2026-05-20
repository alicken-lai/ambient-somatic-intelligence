"""Focus stability — churn and retention of focused targets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FocusStability:
    """Higher score = more stable focus (less churn)."""

    retention_rate: float
    churn_rate: float
    stability_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "retention_rate": round(self.retention_rate, 4),
            "churn_rate": round(self.churn_rate, 4),
            "stability_score": round(self.stability_score, 4),
        }


def compute_focus_stability(
    previous_ids: set[str],
    current_ids: set[str],
) -> FocusStability:
    if not previous_ids and not current_ids:
        return FocusStability(1.0, 0.0, 1.0)
    if not previous_ids:
        return FocusStability(0.0, 1.0, 0.5)
    retained = len(previous_ids & current_ids)
    retention = retained / len(previous_ids)
    churn = 1.0 - retention if previous_ids else 0.0
    stability = max(0.0, min(1.0, retention * 0.7 + (1.0 - churn) * 0.3))
    return FocusStability(retention_rate=retention, churn_rate=churn, stability_score=stability)
