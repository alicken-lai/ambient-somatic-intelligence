"""Area 7: v061 observability metrics."""

from observability.v061.constitutional_compliance_metrics import collect_constitutional_compliance_metrics
from observability.v061.guardian_supremacy_metrics import collect_guardian_supremacy_metrics


def test_compliance_metrics() -> None:
    m = collect_constitutional_compliance_metrics()
    assert 0.0 <= m.compliance_rate <= 1.0


def test_guardian_supremacy_metrics() -> None:
    m = collect_guardian_supremacy_metrics()
    assert m.supremacy_preserved_rate >= 0.99
