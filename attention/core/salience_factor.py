"""
Salience factors — the canonical 10-dimension salience model.

The unified attention layer scores every :class:`AttentionTarget` across ten
domain-agnostic dimensions.  This module is the single source of truth for
*which* dimensions exist and *how* they are weighted by default.

Downstream layers (kernel, forecasting, calibration, explainability) read
``ALL_DIMENSIONS`` and ``DEFAULT_DIMENSION_WEIGHTS`` so that the dimensionality
of salience stays consistent across the whole architecture.

The default weights are normalised to sum to 1.0 so that a target whose every
dimension is saturated (1.0) yields a total salience of 1.0.
"""

from __future__ import annotations

# Ordered list of the ten salience dimensions.  Order is stable so that any
# breakdown / explanation that enumerates dimensions is deterministic.
ALL_DIMENSIONS: list[str] = [
    "urgency",
    "novelty",
    "anomaly",
    "recurrence",
    "historical_similarity",
    "governance_relevance",
    "somatic_stress",
    "memory_relevance",
    "operator_priority",
    "temporal_freshness",
]

# Default contribution of each dimension to the weighted total.
# Invariant: ``sum(DEFAULT_DIMENSION_WEIGHTS.values()) == 1.0``.
DEFAULT_DIMENSION_WEIGHTS: dict[str, float] = {
    "urgency": 0.15,
    "novelty": 0.12,
    "anomaly": 0.12,
    "recurrence": 0.08,
    "historical_similarity": 0.08,
    "governance_relevance": 0.10,
    "somatic_stress": 0.10,
    "memory_relevance": 0.08,
    "operator_priority": 0.08,
    "temporal_freshness": 0.09,
}
