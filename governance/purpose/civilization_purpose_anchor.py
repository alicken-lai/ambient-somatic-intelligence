"""Civilization purpose anchor — compare peer purpose without forced convergence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CivilizationPurposeAnchorVerdict:
    anchored: bool
    peer_id: str = "foreign"
    divergence_ok: bool = True
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchored": self.anchored,
            "peer_id": self.peer_id,
            "divergence_ok": self.divergence_ok,
            "signals": list(self.signals),
            "advisory_only": True,
        }


class CivilizationPurposeAnchor:
    def compare(
        self,
        local_summary: str,
        *,
        peer_summary: str = "",
        peer_id: str = "foreign",
    ) -> CivilizationPurposeAnchorVerdict:
        signals: list[str] = []
        lower = local_summary.lower()
        if "forced purpose convergence" in lower or "universal teleology sync" in lower:
            signals.append("forced_convergence")
        anchored = len(signals) == 0
        divergence_ok = peer_summary != local_summary or not peer_summary
        return CivilizationPurposeAnchorVerdict(
            anchored=anchored,
            peer_id=peer_id,
            divergence_ok=divergence_ok,
            signals=signals,
        )
