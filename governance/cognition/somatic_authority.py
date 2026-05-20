"""Somatic domain authority — bounded boost, never overrides governance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observability.v04.metric_normalizer import clamp01

SOMATIC_MAX_BOOST = 0.25


@dataclass
class SomaticAuthorityResult:
    base_salience: float
    somatic_boost: float
    governed_salience: float
    bounded: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_salience": round(self.base_salience, 4),
            "somatic_boost": round(self.somatic_boost, 4),
            "governed_salience": round(self.governed_salience, 4),
            "bounded": self.bounded,
        }


class SomaticAuthority:
    """Grant somatic signals a capped authority increment."""

    def __init__(self, max_boost: float = SOMATIC_MAX_BOOST) -> None:
        self.max_boost = max_boost

    def apply(
        self,
        base_salience: float,
        *,
        somatic_strength: float = 0.5,
        is_somatic: bool = False,
    ) -> SomaticAuthorityResult:
        base = clamp01(base_salience)
        if not is_somatic:
            return SomaticAuthorityResult(
                base_salience=base,
                somatic_boost=0.0,
                governed_salience=base,
                bounded=True,
            )
        boost = min(self.max_boost, clamp01(somatic_strength) * self.max_boost)
        governed = clamp01(base + boost)
        return SomaticAuthorityResult(
            base_salience=base,
            somatic_boost=boost,
            governed_salience=governed,
            bounded=boost <= self.max_boost,
        )
