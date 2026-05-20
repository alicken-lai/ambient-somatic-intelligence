"""Area 8: observability v077 metrics."""

from observability.v077.agency_boundary_metrics import collect_agency_boundary_metrics
from observability.v077.autonomous_agency_containment_metrics import (
    collect_autonomous_agency_containment_metrics,
)
from observability.v077.cognition_decay_metrics import collect_cognition_decay_metrics


def test_agency_boundary_metrics() -> None:
    m = collect_agency_boundary_metrics()
    assert m.boundary_rate == 1.0


def test_autonomous_agency_containment_metrics() -> None:
    m = collect_autonomous_agency_containment_metrics()
    assert m.containment_rate == 1.0


def test_cognition_decay_metrics() -> None:
    m = collect_cognition_decay_metrics()
    assert m.decay_rate == 1.0
