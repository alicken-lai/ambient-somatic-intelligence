"""Trust evolution engine."""

from __future__ import annotations

from hermes.calibration.source_trust import evolve_source_trust


def evolve_trust(
    current_score: float,
    *,
    verification_success: int = 0,
    verification_failure: int = 0,
    contradictions: int = 0,
    guardian_positive: int = 0,
    guardian_negative: int = 0,
    freshness: float = 1.0,
) -> dict[str, object]:
    adjusted = evolve_source_trust(
        current_score,
        verification_success=verification_success + guardian_positive,
        verification_failure=verification_failure + guardian_negative,
        contradictions=contradictions,
        freshness=freshness,
    )
    delta = round(adjusted - current_score, 4)
    event = "promotion" if delta > 0 else "reduction" if delta < 0 else "unchanged"
    return {"trust_score": adjusted, "delta": delta, "event": event}
