"""Aggregate civilization observability for governor attachment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.civilization.cognition_sandbox_boundary import CognitionSandboxBoundary
from governance.civilization.cognitive_diplomacy import CognitiveDiplomacy
from governance.civilization.constitutional_interop import ConstitutionalInterop
from governance.civilization.dominance_detector import DominanceDetector
from governance.civilization.interop_boundary import InteropBoundary
from governance.civilization.non_interference import NonInterferenceGuard
from governance.civilization.provenance_exchange import ProvenanceExchange
from governance.civilization.sovereign_runtime import SovereignRuntime


@dataclass
class CivilizationObservability:
    """Read-only civilization snapshot — never mutates governance acceptance."""

    advisory_only: bool = True
    interop_safe: bool = True
    non_interference_ok: bool = True
    dominance_free: bool = True
    constitutional_aligned: bool = True
    sandbox_contained: bool = True
    provenance_exchange_valid: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "advisory_only": self.advisory_only,
            "interop_safe": self.interop_safe,
            "non_interference_ok": self.non_interference_ok,
            "dominance_free": self.dominance_free,
            "constitutional_aligned": self.constitutional_aligned,
            "sandbox_contained": self.sandbox_contained,
            "provenance_exchange_valid": self.provenance_exchange_valid,
            "issues": list(self.issues),
            "disclaimer": "civilization_observational_only",
        }


def observe_civilization(
    text: str,
    *,
    sovereign_id: str = "foreign",
    peer_id: str = "ambient",
    scope: str = "advisory",
    provenance_payload: dict[str, Any] | None = None,
) -> CivilizationObservability:
    diplomacy = CognitiveDiplomacy()
    decision = diplomacy.evaluate(
        text,
        sovereign_id=sovereign_id,
        peer_id=peer_id,
        scope=scope,
    )
    sb = CognitionSandboxBoundary().evaluate(text, scope=scope)
    pe = ProvenanceExchange().validate(provenance_payload, sovereign_id=sovereign_id)

    issues = list(decision.reasons)
    if not sb.contained:
        issues.extend(sb.violations)
    if not pe.exchange_valid:
        issues.extend(pe.issues)

    return CivilizationObservability(
        advisory_only=True,
        interop_safe=decision.interop_allowed,
        non_interference_ok=decision.non_interference_ok,
        dominance_free=not decision.dominance_detected,
        constitutional_aligned=decision.guardian_supremacy_preserved,
        sandbox_contained=sb.contained,
        provenance_exchange_valid=pe.exchange_valid,
        issues=issues,
    )
