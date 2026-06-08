"""
Governed attention activation — kernel submission behind cognitive governance.

This is the runtime bridge that routes attention activations through the
:class:`CognitiveGovernor` (advisory arbitration: sovereignty, constitution,
identity, coherence, metacognition, homeostasis) before they reach the kernel.

It is *advisory and bounded*: governance can reject or attenuate a target's
salience but never amplifies it, never executes side effects, and never forms a
recursive governance loop.  Deliberately not exported from ``attention.runtime``
so the base attention import path stays decoupled from the governance tree.
"""

from __future__ import annotations

from typing import Any, Optional

from attention.consolidation.attention_memory_store import AttentionMemoryStore
from attention.core.attention_target import AttentionTarget
from attention.kernel.attention_kernel import AttentionKernel
from governance.cognition.cognitive_governor import CognitiveGovernor, GovernanceDecision
from governance.cognition.salience_arbitrator import SalienceClaim


class GovernedAttentionActivation:
    """Submits targets into the kernel only after cognitive governance."""

    def __init__(
        self,
        kernel: Optional[AttentionKernel] = None,
        store: Optional[AttentionMemoryStore] = None,
        governor: Optional[CognitiveGovernor] = None,
    ) -> None:
        self.kernel = kernel if kernel is not None else AttentionKernel()
        self.store = store
        self.governor = governor or CognitiveGovernor()

    def govern_target(
        self,
        target: AttentionTarget,
        *,
        raw_confidence: float = 0.7,
        uncertainty: float = 0.35,
        replay_hint: float = 0.0,
        route_name: str = "attention_submit",
    ) -> GovernanceDecision:
        """Advisory governance verdict for *target* (no kernel submission)."""
        return self.governor.govern_target(
            target,
            raw_confidence=raw_confidence,
            uncertainty=uncertainty,
            replay_hint=replay_hint,
            route_name=route_name,
        )

    def submit_governed_target(
        self,
        target: AttentionTarget,
        *,
        raw_confidence: float = 0.7,
        uncertainty: float = 0.35,
        replay_hint: float = 0.0,
        route_name: str = "attention_submit",
    ) -> dict[str, Any]:
        """Govern *target*, and submit to the kernel only if governance accepts."""
        decision = self.govern_target(
            target,
            raw_confidence=raw_confidence,
            uncertainty=uncertainty,
            replay_hint=replay_hint,
            route_name=route_name,
        )
        result: dict[str, Any] = {
            "target_id": target.target_id,
            "accepted": decision.accepted,
            "governed": decision.accepted,
            "governed_salience": round(decision.governed_salience, 4),
            "reason": decision.reason,
            "governance": decision.to_dict(),
        }
        if decision.accepted:
            result["kernel"] = self.kernel.submit(target)
        return result

    def arbitrate_claims(
        self,
        claims: list[SalienceClaim],
        *,
        uncertainty: float = 0.3,
    ) -> dict[str, Any]:
        """Govern a set of salience claims and return the arbitration outcome."""
        decision = self.governor.govern_salience(claims, uncertainty=uncertainty)
        return {
            "accepted": decision.accepted,
            "governed_salience": round(decision.governed_salience, 4),
            "arbitration": decision.arbitration.to_dict(),
            "governance": decision.to_dict(),
        }
