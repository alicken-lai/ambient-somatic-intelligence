"""Federation stability scoring — observational."""

from __future__ import annotations

from observability.v04.metric_normalizer import clamp01


class FederationStability:
    def score(
        self,
        sovereign_a: str,
        sovereign_b: str,
        *,
        dominance_free: bool = True,
    ) -> float:
        if sovereign_a == sovereign_b:
            return 0.0
        base = 0.85 if dominance_free else 0.2
        if sovereign_a.lower() in ("ambient", "hermes") or sovereign_b.lower() in ("ambient", "hermes"):
            base = min(base + 0.05, 1.0)
        return clamp01(base)
