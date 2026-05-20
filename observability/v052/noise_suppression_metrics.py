"""Noise suppression and benign pattern metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.consolidation.benign_pattern_memory import BenignPatternMemory
from attention.consolidation.background_stability import BackgroundStability
from attention.consolidation.attention_trace import AttentionTrace


@dataclass
class NoiseSuppressionMetrics:
    benign_pattern_count: int = 0
    background_stability: float = 1.0
    suppression_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "benign_pattern_count": self.benign_pattern_count,
            "background_stability": round(self.background_stability, 4),
            "suppression_rate": round(self.suppression_rate, 4),
        }


def collect_noise_suppression_metrics(
    benign: BenignPatternMemory,
    trace: AttentionTrace,
) -> NoiseSuppressionMetrics:
    stability = BackgroundStability().score(trace, benign)
    rate = min(1.0, benign.count / max(1, benign.max_patterns))
    return NoiseSuppressionMetrics(
        benign_pattern_count=benign.count,
        background_stability=stability,
        suppression_rate=rate,
    )
