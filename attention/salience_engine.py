"""
Salience Engine — Unified cross-domain salience scoring.

Computes a single 0.0–1.0 salience score for any AttentionSignal by combining
nine weighted factors:

  novelty            — how new / unexpected (integrates with AnomalyAmplifier)
  anomaly_level      — deviation from baseline
  recurrence         — habituate to repeated patterns
  historical_similarity — similarity to past important events
  governance_urgency — governance-related priority
  somatic_stress     — current system stress level
  memory_relevance   — relevance to recent memory context
  operator_priority  — manually set priority overrides
  temporal_decay     — diminish over time unless reinforced

Weights are configurable; defaults are provided.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from attention.attention_state import AttentionSignal, AttentionSnapshot

logger = logging.getLogger(__name__)


DEFAULT_WEIGHTS: dict[str, float] = {
    "novelty": 0.15,
    "anomaly_level": 0.15,
    "recurrence": 0.10,
    "historical_similarity": 0.08,
    "governance_urgency": 0.12,
    "somatic_stress": 0.12,
    "memory_relevance": 0.08,
    "operator_priority": 0.10,
    "temporal_decay": 0.10,
}


@dataclass
class SalienceScore:
    """Result of salience computation for a single signal."""
    signal_id: str
    total: float
    factors: dict[str, float]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "total": round(self.total, 4),
            "factors": {k: round(v, 4) for k, v in self.factors.items()},
            "explanation": self.explanation,
        }


class SalienceEngine:
    """
    Computes unified salience scores across all signal domains.

    Usage::

        engine = SalienceEngine()
        score = engine.compute_salience(signal, state)
        print(score.total, score.explanation)
    """

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        operator_overrides: dict[str, float] | None = None,
    ) -> None:
        self._weights = dict(weights or DEFAULT_WEIGHTS)
        self._operator_overrides: dict[str, float] = dict(operator_overrides or {})
        self._occurrence_counts: dict[str, int] = {}
        self._important_history: list[dict[str, Any]] = []
        self._somatic_stress: float = 0.0
        self._memory_relevance_fn: Any = None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_weights(self, weights: dict[str, float]) -> None:
        """Replace the factor weights (must sum to ≈1.0)."""
        self._weights = dict(weights)

    def set_operator_override(self, signal_type: str, priority: float) -> None:
        """Set a manual operator priority for a signal type."""
        self._operator_overrides[signal_type] = max(0.0, min(1.0, priority))
        logger.info("Operator override set: %s = %.2f", signal_type, priority)

    def clear_operator_override(self, signal_type: str) -> None:
        """Remove an operator priority override."""
        self._operator_overrides.pop(signal_type, None)

    def update_somatic_stress(self, stress: float) -> None:
        """Feed the current aggregate somatic stress (0.0–1.0)."""
        self._somatic_stress = max(0.0, min(1.0, stress))

    def set_memory_relevance_fn(self, fn: Any) -> None:
        """Inject a callable(signal) → float for memory relevance."""
        self._memory_relevance_fn = fn

    def record_important_event(self, signal: AttentionSignal) -> None:
        """Record a signal that was acted on (for historical similarity)."""
        self._important_history.append({
            "domain": signal.source_domain,
            "type": signal.signal_type,
            "value": signal.raw_value,
            "ts": signal.timestamp.isoformat(),
        })
        if len(self._important_history) > 500:
            self._important_history = self._important_history[-500:]

    # ------------------------------------------------------------------
    # Core scoring
    # ------------------------------------------------------------------

    def compute_salience(
        self,
        signal: AttentionSignal,
        context: AttentionSnapshot,
    ) -> SalienceScore:
        """
        Compute a unified salience score for *signal* given the current
        attention *context*.
        """
        sig_key = f"{signal.source_domain}:{signal.signal_type}"
        self._occurrence_counts[sig_key] = self._occurrence_counts.get(sig_key, 0) + 1
        count = self._occurrence_counts[sig_key]

        factors: dict[str, float] = {
            "novelty": self._score_novelty(sig_key, count),
            "anomaly_level": self._score_anomaly(signal),
            "recurrence": self._score_recurrence(count),
            "historical_similarity": self._score_historical(signal),
            "governance_urgency": self._score_governance(signal),
            "somatic_stress": self._score_somatic(),
            "memory_relevance": self._score_memory(signal),
            "operator_priority": self._score_operator(signal),
            "temporal_decay": self._score_temporal_decay(signal),
        }

        total = sum(
            self._weights.get(k, 0.0) * v for k, v in factors.items()
        )
        total = max(0.0, min(1.0, total))

        explanation = self._build_explanation(factors, total)

        score = SalienceScore(
            signal_id=signal.signal_id,
            total=total,
            factors=factors,
            explanation=explanation,
        )

        logger.debug(
            "Salience for %s [%s]: %.4f — %s",
            signal.signal_id[:8], sig_key, total, explanation,
        )
        return score

    # ------------------------------------------------------------------
    # Individual factor scorers (all return 0.0–1.0)
    # ------------------------------------------------------------------

    def _score_novelty(self, sig_key: str, count: int) -> float:
        """First occurrence → 1.0, decays with repeated occurrences."""
        if count <= 1:
            return 1.0
        return max(0.0, 1.0 / math.log2(count + 1))

    def _score_anomaly(self, signal: AttentionSignal) -> float:
        """Use raw_value as a proxy; high values are more anomalous."""
        return signal.raw_value

    def _score_recurrence(self, count: int) -> float:
        """Inverse habituation — frequent signals score *lower*."""
        if count <= 1:
            return 1.0
        return max(0.05, 1.0 - math.log10(count) * 0.4)

    def _score_historical(self, signal: AttentionSignal) -> float:
        """Similarity to past important events (simple type matching)."""
        if not self._important_history:
            return 0.0
        matches = sum(
            1 for h in self._important_history[-50:]
            if h["domain"] == signal.source_domain
            and h["type"] == signal.signal_type
        )
        return min(matches / 5.0, 1.0)

    def _score_governance(self, signal: AttentionSignal) -> float:
        """Governance-related signals score higher."""
        if signal.source_domain == "governance":
            return min(0.6 + signal.raw_value * 0.4, 1.0)
        gov_flag = signal.metadata.get("governance_relevant", False)
        return 0.5 if gov_flag else 0.1

    def _score_somatic(self) -> float:
        """Pass-through of the aggregate somatic stress level."""
        return self._somatic_stress

    def _score_memory(self, signal: AttentionSignal) -> float:
        """Delegate to injected memory-relevance function if available."""
        if self._memory_relevance_fn:
            try:
                return max(0.0, min(1.0, float(self._memory_relevance_fn(signal))))
            except Exception:
                return 0.0
        return signal.metadata.get("memory_relevance", 0.0)

    def _score_operator(self, signal: AttentionSignal) -> float:
        """Manual operator priority override."""
        override = self._operator_overrides.get(signal.signal_type)
        if override is not None:
            return override
        return signal.metadata.get("operator_priority", 0.0)

    def _score_temporal_decay(self, signal: AttentionSignal) -> float:
        """Exponential decay based on signal age (half-life 60 s)."""
        age = signal.age_seconds
        half_life = 60.0
        return max(0.0, math.exp(-0.693 * age / half_life))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_explanation(factors: dict[str, float], total: float) -> str:
        top = sorted(factors.items(), key=lambda kv: kv[1], reverse=True)[:3]
        parts = [f"{k}={v:.2f}" for k, v in top if v > 0.05]
        if not parts:
            return f"Low salience ({total:.2f})"
        return f"Salience {total:.2f} driven by {', '.join(parts)}"
