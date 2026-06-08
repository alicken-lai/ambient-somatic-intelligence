"""
Civilization memory breakdown — explains bounded retention of epoch memory.

Wraps the governance continuity-retention policy to report whether civilization
memory stays within bounded horizons (no immortal cognition). Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.temporal.continuity_retention import ContinuityRetention


class CivilizationMemoryBreakdown:
    """Transparent breakdown of bounded civilization-memory retention."""

    def __init__(self) -> None:
        self.retention = ContinuityRetention()

    def explain(self, *, retention_hours: float = 168.0) -> dict[str, Any]:
        verdict = self.retention.evaluate(retention_hours=retention_hours)
        retention = verdict.to_dict()

        summary = (
            f"Civilization memory retention is "
            f"{'within bounds' if verdict.retention_ok else 'out of bounds'} "
            f"({verdict.retention_hours:.2f}h). Bounded horizons only; "
            "no immortal cognition."
        )

        return {
            "advisory_only": True,
            "retention": retention,
            "summary": summary,
        }
