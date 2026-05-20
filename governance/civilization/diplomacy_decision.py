"""Advisory diplomacy decision — observational only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiplomacyDecision:
    """Outcome of cognitive diplomacy evaluation — never overrides governor acceptance."""

    advisory_only: bool = True
    interop_allowed: bool = True
    treaty_recommended: bool = False
    non_interference_ok: bool = True
    dominance_detected: bool = False
    federation_safe: bool = True
    guardian_supremacy_preserved: bool = True
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "advisory_only": self.advisory_only,
            "interop_allowed": self.interop_allowed,
            "treaty_recommended": self.treaty_recommended,
            "non_interference_ok": self.non_interference_ok,
            "dominance_detected": self.dominance_detected,
            "federation_safe": self.federation_safe,
            "guardian_supremacy_preserved": self.guardian_supremacy_preserved,
            "reasons": list(self.reasons),
            "disclaimer": "civilization_observational_only",
        }
