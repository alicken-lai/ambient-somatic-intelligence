"""
Civilization semantic breakdown — explains bounded retention of meaning records.

Wraps the governance interpretive-retention policy to report whether civilization
meaning stays within bounded horizons (no immortal ontology). Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.meaning.interpretive_retention import InterpretiveRetention


class CivilizationSemanticBreakdown:
    """Transparent breakdown of bounded interpretive-meaning retention."""

    def __init__(self) -> None:
        self.retention = InterpretiveRetention()

    def explain(self, *, retention_hours: float = 168.0) -> dict[str, Any]:
        verdict = self.retention.evaluate(retention_hours)
        retention = verdict.to_dict()

        summary = (
            f"Civilization meaning retention is "
            f"{'within bounds' if verdict.retention_ok else 'out of bounds'} "
            f"({retention_hours:.2f}h, max={verdict.max_hours:.0f}h). "
            "Bounded horizons only; no immortal ontology."
        )

        return {
            "advisory_only": True,
            "retention": retention,
            "summary": summary,
        }
