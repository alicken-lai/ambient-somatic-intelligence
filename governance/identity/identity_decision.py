"""Identity decision — provenance-aware cognition authority outcome."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.identity.provenance_record import ProvenanceRecord


@dataclass
class IdentityDecision:
    trusted: bool
    authority_multiplier: float
    provenance: ProvenanceRecord
    reason: str = "ok"
    replay_separated: bool = True
    synthetic_bounded: bool = True
    coherence_ok: bool = True
    trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trusted": self.trusted,
            "authority_multiplier": round(self.authority_multiplier, 4),
            "reason": self.reason,
            "replay_separated": self.replay_separated,
            "synthetic_bounded": self.synthetic_bounded,
            "coherence_ok": self.coherence_ok,
            "provenance": self.provenance.to_dict(),
            "trace": list(self.trace),
        }
