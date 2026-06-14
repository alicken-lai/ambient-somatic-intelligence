"""Self-tuning routing from historical effectiveness."""

from __future__ import annotations

from typing import Any

from hermes.deliberation.memory import EffectivenessRecord
from hermes.deliberation.router.routing_policies import RoutingPolicyConfig


class AdaptiveRoutingLearner:
    def __init__(self, policy: RoutingPolicyConfig | None = None):
        self.policy = policy or RoutingPolicyConfig()

    def learn_defaults(self, records: dict[str, EffectivenessRecord]) -> dict[str, dict[str, Any]]:
        recommendations: dict[str, dict[str, Any]] = {}
        for task_class, record in records.items():
            if record.sample_count < self.policy.minimum_sample_threshold:
                continue
            scores = {
                "single": record.avg_single_score,
                "light": record.avg_light_score,
                "full": record.avg_full_score,
            }
            best = max(scores, key=lambda mode: scores[mode])
            baseline = scores["single"]
            margin = scores[best] - baseline
            if margin < self.policy.quality_margin:
                continue
            confidence = min(0.95, 0.55 + margin / 40.0 + min(0.2, record.sample_count / 100.0))
            if confidence < self.policy.confidence_threshold:
                continue
            recommendations[task_class] = {
                "default_mode": best,
                "confidence": round(confidence, 3),
                "rollback_protection": {
                    "rollback_if_margin_below": self.policy.rollback_margin,
                    "immutable_governance": True,
                },
                "reason": f"{best} beats single by {margin:.2f} points across {record.sample_count} samples.",
            }
        return recommendations
