"""Forecast boundary — anticipatory cognition must respect uncertainty bands."""

from __future__ import annotations

from governance.constitution.constitutional_rule import ConstitutionalRule
from governance.constitution.constitutional_violation import ConstitutionalViolation
from observability.v04.metric_normalizer import clamp01

FORECAST_BOUNDARY_RULE = ConstitutionalRule(
    rule_id="forecast_boundary",
    name="Forecast Boundary",
    description="Forecasts remain bounded; high uncertainty cannot be collapsed to certainty.",
    severity="block",
)

MIN_FORECAST_UNCERTAINTY = 0.05


def check_forecast_boundary(
    *,
    uncertainty: float,
    collapse_uncertainty: bool = False,
    forecast_certainty: bool = False,
) -> ConstitutionalViolation | None:
    u = clamp01(uncertainty)
    if collapse_uncertainty or forecast_certainty:
        return ConstitutionalViolation(
            rule_id=FORECAST_BOUNDARY_RULE.rule_id,
            message="forecast_uncertainty_collapse_forbidden",
            severity="block",
        )
    if u < MIN_FORECAST_UNCERTAINTY and forecast_certainty:
        return ConstitutionalViolation(
            rule_id=FORECAST_BOUNDARY_RULE.rule_id,
            message="forecast_uncertainty_below_constitutional_floor",
            severity="block",
        )
    return None
