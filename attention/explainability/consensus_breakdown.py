"""
Consensus breakdown — explains bounded consensus negotiation.

Wraps the governance bounded-consensus evaluator to report whether consensus
pressure stays bounded, while making explicit that forced consensus is always
constitutionally blocked. Read-only/advisory.
"""

from __future__ import annotations

from typing import Any

from governance.reality.bounded_consensus import BoundedConsensus


class ConsensusBreakdown:
    """Transparent breakdown of bounded consensus negotiation."""

    def __init__(self) -> None:
        self.consensus = BoundedConsensus()

    def explain(self, text: str) -> dict[str, Any]:
        verdict = self.consensus.evaluate(text)

        summary = (
            f"Consensus {'bounded' if verdict.bounded else 'pressured'} "
            f"(pressure={verdict.consensus_pressure:.4f}, "
            f"signals={list(verdict.signals)}). Forced/absolute consensus is "
            "constitutionally blocked; uncertainty is negotiated, not coerced."
        )

        return {
            "advisory_only": True,
            "forced_consensus_blocked": True,
            "bounded": verdict.bounded,
            "consensus_pressure": round(verdict.consensus_pressure, 4),
            "signals": list(verdict.signals),
            "summary": summary,
        }
