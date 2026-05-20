"""Cognition federation — advisory membership stability (not hive-mind)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.civilization.dominance_detector import DominanceDetector
from governance.civilization.federation_stability import FederationStability


@dataclass
class FederationVerdict:
    stable: bool
    member_count: int = 2
    hive_mind_blocked: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "stable": self.stable,
            "member_count": self.member_count,
            "hive_mind_blocked": self.hive_mind_blocked,
        }


class CognitionFederation:
    """Advisory federation evaluator — never merges members."""

    def __init__(self) -> None:
        self._dominance = DominanceDetector()
        self._stability = FederationStability()

    def evaluate_membership(
        self,
        sovereign_a: str,
        sovereign_b: str,
        text: str,
    ) -> FederationVerdict:
        dom = self._dominance.scan(text)
        stab = self._stability.score(sovereign_a, sovereign_b, dominance_free=not dom.dominance_detected)
        return FederationVerdict(
            stable=stab >= 0.5 and not dom.dominance_detected,
            member_count=2,
            hive_mind_blocked=True,
        )
