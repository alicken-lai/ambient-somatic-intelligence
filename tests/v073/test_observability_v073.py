"""Area 8: Phase 7 observability metrics."""

from observability.v073.drift_containment_metrics import collect_drift_containment_metrics
from observability.v073.meaning_integrity_metrics import collect_meaning_integrity_metrics
from observability.v073.ontology_boundary_metrics import collect_ontology_boundary_metrics


def test_drift_containment_metrics() -> None:
    m = collect_drift_containment_metrics()
    assert m.containment_rate == 1.0


def test_ontology_boundary_metrics() -> None:
    m = collect_ontology_boundary_metrics()
    assert m.boundary_rate == 1.0


def test_meaning_integrity_metrics() -> None:
    m = collect_meaning_integrity_metrics()
    assert m.integrity_rate == 1.0
