"""Area 8: Observability v076 metrics."""

from observability.v076.autonomous_purpose_containment_metrics import (
    collect_autonomous_purpose_containment_metrics,
)
from observability.v076.optimization_decay_metrics import collect_optimization_decay_metrics
from observability.v076.purpose_boundary_metrics import collect_purpose_boundary_metrics
from observability.v076.purpose_integrity_metrics import collect_purpose_integrity_metrics
from observability.v076.purpose_lineage_integrity_metrics import (
    collect_purpose_lineage_integrity_metrics,
)
from observability.v076.purpose_provenance_metrics import collect_purpose_provenance_metrics


def test_all_six_metrics_present() -> None:
    assert collect_autonomous_purpose_containment_metrics().containment_rate == 1.0
    assert collect_purpose_boundary_metrics().boundary_rate == 1.0
    assert collect_purpose_lineage_integrity_metrics().integrity_rate == 1.0
    assert collect_optimization_decay_metrics().decay_rate == 1.0
    assert collect_purpose_provenance_metrics().provenance_rate == 1.0
    assert collect_purpose_integrity_metrics().integrity_rate == 1.0
