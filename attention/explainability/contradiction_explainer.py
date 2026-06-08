"""
Contradiction explainer — narrates contradiction pressure across records.

Wraps the governance contradiction detector to report how conflicting
confidence/domain clusters raise advisory contradiction pressure. Never asserts
deterministic truth about which record is "right".
"""

from __future__ import annotations

from typing import Any

from governance.coherence.contradiction_detector import ContradictionDetector


class ContradictionExplainer:
    """Transparent breakdown of contradiction pressure over a record batch."""

    def __init__(self) -> None:
        self.detector = ContradictionDetector()

    def explain_records(self, records: list[Any]) -> dict[str, Any]:
        pressure = self.detector.pressure(records)
        has_contradiction = self.detector.has_contradiction(records)

        summary = (
            f"Contradiction pressure={pressure:.4f} across {len(records)} record(s) "
            f"(has_contradiction={has_contradiction}). Advisory, not deterministic truth."
        )

        return {
            "advisory_only": True,
            "record_count": len(records),
            "pressure": round(pressure, 4),
            "has_contradiction": has_contradiction,
            "summary": summary,
        }
