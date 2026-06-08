"""
Kernel salience engine — scores a target across the 10 salience dimensions.

``KernelSalienceEngine`` turns a single :class:`AttentionTarget` (which only
carries a scalar ``raw_value`` plus optional metadata hints) into a full
:class:`SalienceVector` over the canonical :data:`ALL_DIMENSIONS`.

The mapping is deterministic and derived from the target's ``raw_value``,
``source_domain`` and ``metadata`` hints — there is no hidden state and no
randomness, so the same target always yields the same vector.
"""

from __future__ import annotations

from attention.core.attention_target import AttentionTarget
from attention.core.salience import SalienceVector
from attention.core.salience_factor import ALL_DIMENSIONS


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class KernelSalienceEngine:
    """Deterministically scores an :class:`AttentionTarget` into a vector."""

    def score_dimensions(self, target: AttentionTarget) -> dict[str, float]:
        """Return a per-dimension score dict over all 10 dimensions."""
        base = _clamp_unit(target.raw_value)
        meta = target.metadata or {}
        domain = target.source_domain

        is_gov = domain == "governance" or bool(meta.get("governance_relevant"))
        is_somatic = domain == "somatic"
        is_memory = domain == "memory"

        dims: dict[str, float] = {
            "urgency": _clamp_unit(meta.get("urgency", base)),
            "novelty": base,
            "anomaly": base,
            "recurrence": base * 0.5,
            "historical_similarity": _clamp_unit(meta.get("historical_similarity", base * 0.5)),
            "governance_relevance": _clamp_unit(
                meta.get("governance_risk", 0.8 if is_gov else base * 0.4)
            ),
            "somatic_stress": _clamp_unit(meta.get("somatic_stress", base if is_somatic else base * 0.5)),
            "memory_relevance": _clamp_unit(
                meta.get("memory_relevance", base if is_memory else base * 0.4)
            ),
            "operator_priority": _clamp_unit(meta.get("operator_priority", 0.0)),
            "temporal_freshness": _clamp_unit(meta.get("temporal_freshness", base)),
        }
        # Guarantee exactly the canonical dimension set, in canonical order.
        return {d: dims.get(d, base) for d in ALL_DIMENSIONS}

    def compute(self, target: AttentionTarget) -> SalienceVector:
        """Score *target* and return its :class:`SalienceVector`."""
        return SalienceVector(
            target_id=target.target_id,
            dimensions=self.score_dimensions(target),
        )
