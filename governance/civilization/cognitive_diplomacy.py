"""Cognitive diplomacy — advisory inter-sovereign evaluation (no autonomous execution)."""

from __future__ import annotations

from governance.civilization.cognition_federation import CognitionFederation
from governance.civilization.constitutional_interop import ConstitutionalInterop
from governance.civilization.diplomacy_decision import DiplomacyDecision
from governance.civilization.dominance_detector import DominanceDetector
from governance.civilization.interop_boundary import InteropBoundary
from governance.civilization.non_interference import NonInterferenceGuard
from governance.civilization.sovereign_runtime import SovereignRuntime
from governance.civilization.sovereignty_alignment import SovereigntyAlignment
from governance.civilization.treaty_record import TreatyRecord


class CognitiveDiplomacy:
    """
    Evaluates foreign sovereign interaction proposals.

    Always advisory — never executes treaties or overrides Guardian/constitution.
    """

    def __init__(self) -> None:
        self._runtime = SovereignRuntime()
        self._interop = InteropBoundary()
        self._non_interference = NonInterferenceGuard()
        self._dominance = DominanceDetector()
        self._constitutional = ConstitutionalInterop()
        self._alignment = SovereigntyAlignment()
        self._federation = CognitionFederation()

    def evaluate(
        self,
        text: str,
        *,
        sovereign_id: str = "foreign",
        peer_id: str = "ambient",
        scope: str = "advisory",
        channel: str = "advisory",
    ) -> DiplomacyDecision:
        reasons: list[str] = []
        rt = self._runtime.evaluate(text, declared_scope=scope, entity_id=sovereign_id)
        ib = self._interop.evaluate(text, channel=channel)
        ni = self._non_interference.check(text, actor=sovereign_id, target=peer_id)
        dom = self._dominance.scan(text)
        ci = self._constitutional.check(text)
        align = self._alignment.evaluate(sovereign_id, peer_id, text)
        fed = self._federation.evaluate_membership(sovereign_id, peer_id, text)

        if not rt.runtime_safe:
            reasons.extend(rt.violations)
        if not ib.interop_safe:
            reasons.extend(ib.signals)
        if not ni.respected:
            reasons.extend(ni.violations)
        if dom.dominance_detected:
            reasons.extend(dom.signals)
        if not ci.aligned:
            reasons.extend(ci.violations)
        if not align.aligned:
            reasons.append("sovereignty_misalignment")
        if not fed.stable:
            reasons.append("federation_unstable")

        interop_allowed = (
            rt.runtime_safe
            and ib.interop_safe
            and ni.respected
            and not dom.dominance_detected
            and ci.aligned
            and align.aligned
            and fed.stable
        )
        treaty_recommended = interop_allowed and len(text) > 20

        return DiplomacyDecision(
            advisory_only=True,
            interop_allowed=interop_allowed,
            treaty_recommended=treaty_recommended,
            non_interference_ok=ni.respected,
            dominance_detected=dom.dominance_detected,
            federation_safe=fed.stable,
            guardian_supremacy_preserved=ci.guardian_supremacy,
            reasons=reasons,
        )

    def propose_treaty(
        self,
        sovereign_a: str,
        sovereign_b: str,
        *,
        text: str = "",
    ) -> TreatyRecord | None:
        decision = self.evaluate(text or "advisory interop", sovereign_id=sovereign_a, peer_id=sovereign_b)
        if not decision.interop_allowed:
            return None
        return TreatyRecord.create(sovereign_a, sovereign_b)
