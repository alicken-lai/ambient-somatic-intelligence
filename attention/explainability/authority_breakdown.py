"""
Authority breakdown — explains bounded somatic & replay influence on salience.

Mirrors the governance somatic/replay authority bounds (somatic boost <= 0.25,
replay influence <= 0.15) so the attention layer can transparently show that
neither path can seize autonomous control or exceed its hard ceiling.

Kept self-contained (no governance import) to preserve attention-layer layering.
"""

from __future__ import annotations

from typing import Any

SOMATIC_MAX_BOOST = 0.25
REPLAY_MAX_INFLUENCE = 0.15


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


class AuthorityBreakdown:
    """Decomposes how somatic and replay authority shape a base salience."""

    def __init__(
        self,
        *,
        somatic_max_boost: float = SOMATIC_MAX_BOOST,
        replay_max_influence: float = REPLAY_MAX_INFLUENCE,
    ) -> None:
        self.somatic_max_boost = somatic_max_boost
        self.replay_max_influence = replay_max_influence

    def breakdown(
        self,
        *,
        base_salience: float,
        domain: str,
        somatic_strength: float = 0.5,
        replay_hint: float = 0.0,
        replay_confidence: float = 0.5,
    ) -> dict[str, Any]:
        base = _clamp01(base_salience)

        is_somatic = domain == "somatic"
        boost = (
            min(self.somatic_max_boost, _clamp01(somatic_strength) * self.somatic_max_boost)
            if is_somatic
            else 0.0
        )
        somatic_governed = _clamp01(base + boost)
        somatic = {
            "base_salience": round(base, 4),
            "somatic_boost": round(boost, 4),
            "governed_salience": round(somatic_governed, 4),
            "bounded": boost <= self.somatic_max_boost,
        }

        hint = _clamp01(replay_hint)
        conf = _clamp01(replay_confidence)
        replay_w = min(self.replay_max_influence, hint * conf * self.replay_max_influence)
        blended = _clamp01(somatic_governed * (1.0 - replay_w) + hint * replay_w)
        replay = {
            "replay_weight": round(replay_w, 4),
            "live_weight": round(blended, 4),
            "bounded": replay_w <= self.replay_max_influence,
            "read_only": True,
        }

        return {
            "domain": domain,
            "no_autonomous_execution": True,
            "somatic": somatic,
            "replay": replay,
            "composite_live_weight": round(blended, 4),
        }
