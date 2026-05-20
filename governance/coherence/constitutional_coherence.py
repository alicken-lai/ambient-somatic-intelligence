"""Constitutional coherence — governance verdicts align with constitution."""

from __future__ import annotations

from typing import Any

from observability.v04.metric_normalizer import clamp01


class ConstitutionalCoherence:
    def pressure(
        self,
        *,
        constitutional_compliant: bool,
        constitutional_verdict: dict[str, Any] | None = None,
    ) -> float:
        if not constitutional_compliant:
            return 1.0
        verdict = constitutional_verdict or {}
        violations = verdict.get("violations") or []
        if violations:
            return clamp01(0.5 + 0.1 * len(violations))
        return 0.0

    def coherent(
        self,
        *,
        constitutional_compliant: bool,
        constitutional_verdict: dict[str, Any] | None = None,
    ) -> bool:
        return self.pressure(
            constitutional_compliant=constitutional_compliant,
            constitutional_verdict=constitutional_verdict,
        ) < 0.35
