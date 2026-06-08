"""
Guardian attention bridge — routes Guardian verdicts into the kernel.

When Guardian classifies an action, this bridge converts the verdict into a
governance :class:`AttentionTarget` whose salience reflects the escalation
level, and submits it to the attention kernel.
"""

from __future__ import annotations

from typing import Any

from attention.core.attention_target import AttentionTarget
from attention.governance.escalation_salience import escalation_boost
from attention.kernel.attention_kernel import AttentionKernel


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class GuardianAttentionBridge:
    """Submits Guardian verdicts to the attention kernel as governance targets."""

    def __init__(self, kernel: AttentionKernel) -> None:
        self.kernel = kernel

    def from_guardian_result(
        self,
        action: str,
        risk: str,
        matched: list[str] | None = None,
    ) -> dict[str, Any]:
        boost = escalation_boost(risk)
        raw_value = _clamp_unit(max(0.1, boost))
        target = AttentionTarget(
            source_domain="governance",
            signal_type=f"guardian_{str(risk).lower()}",
            raw_value=raw_value,
            metadata={
                "governance_relevance": boost,
                "guardian_risk": risk,
                "guardian_action": action,
                "matched": list(matched or []),
                "urgency": boost,
            },
        )
        result = self.kernel.submit(target)
        return {
            "accepted": bool(result.get("accepted")),
            "target_id": result.get("target_id"),
            "risk": risk,
            "boost": boost,
        }
