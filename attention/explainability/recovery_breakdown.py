"""
Recovery breakdown — explains advisory coherence-recovery steps.

Wraps the governance coherence-recovery assessor to report the coherence gap and
recommended recovery steps when coherence pressure is elevated. Advisory only.
"""

from __future__ import annotations

from typing import Any

from governance.homeostasis.coherence_recovery import CoherenceRecovery


class RecoveryBreakdown:
    """Transparent breakdown of advisory coherence recovery."""

    def __init__(self) -> None:
        self.coherence_recovery = CoherenceRecovery()

    def breakdown(
        self,
        *,
        coherence_score: float,
        coherence_ok: bool,
        coherence_verdict: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        recovery = self.coherence_recovery.assess(
            coherence_score=coherence_score,
            coherence_ok=coherence_ok,
            coherence_verdict=coherence_verdict,
        )
        needed = bool(recovery.get("recommendations"))

        summary = (
            f"Coherence recovery {'needed' if needed else 'not needed'} "
            f"(gap={recovery.get('coherence_gap', 0.0)})."
        )

        return {
            "advisory_only": True,
            "recovery_needed": needed,
            "coherence_recovery": recovery,
            "summary": summary,
        }
