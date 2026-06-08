"""
Precursor reinforcement report — explains bounded precursor-driven reinforcement.

Reports how strongly a confirmed :class:`PrecursorSignal` reinforces salience,
reusing :class:`PrecursorWeighting` and :class:`SalienceReinforcement` so the
reinforced value is always bounded (never reaching certainty).
"""

from __future__ import annotations

from typing import Any

from attention.consolidation.precursor_weighting import PrecursorWeighting
from attention.consolidation.salience_reinforcement import (
    REINFORCEMENT_CEILING,
    SalienceReinforcement,
)
from attention.core.precursor_signal import PrecursorSignal


class PrecursorReinforcementReport:
    """Explains how a precursor reinforces salience, within bounds."""

    def __init__(
        self,
        weighting: PrecursorWeighting | None = None,
        reinforcement: SalienceReinforcement | None = None,
    ) -> None:
        self.weighting = weighting or PrecursorWeighting()
        self.reinforcement = reinforcement or SalienceReinforcement()

    def for_precursor(
        self,
        precursor: PrecursorSignal,
        current_salience: float = 0.0,
        hit_count: int = 1,
    ) -> dict[str, Any]:
        weight = self.weighting.weight(precursor)
        reinforced = self.reinforcement.reinforce(
            current=current_salience,
            evidence=weight,
            hit_count=hit_count,
        )
        return {
            "pattern_id": precursor.pattern_id,
            "precursor_strength": round(precursor.strength, 4),
            "precursor_weight": round(weight, 4),
            "current_salience": round(float(current_salience), 4),
            "reinforced_salience": reinforced,
            "ceiling": REINFORCEMENT_CEILING,
            "rationale": (
                f"Precursor {precursor.pattern_id} (weight {weight:.2f}) reinforces "
                f"salience to {reinforced:.2f}, capped at {REINFORCEMENT_CEILING:.2f}."
            ),
            "opaque": False,
        }
