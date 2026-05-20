"""Area 7: Observability v065b metrics."""

from observability.v065b.doctrine_filter_metrics import collect_doctrine_filter_metrics
from observability.v065b.provenance_integrity_metrics import collect_provenance_integrity_metrics


def test_doctrine_filter_metrics() -> None:
    m = collect_doctrine_filter_metrics()
    assert m.containment_rate >= 0.5


def test_provenance_integrity_metrics() -> None:
    m = collect_provenance_integrity_metrics()
    assert m.mount_valid is True
