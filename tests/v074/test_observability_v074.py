"""Area 8: Phase 7 observability metrics."""

from observability.v074.ethical_drift_containment_metrics import (
    collect_ethical_drift_containment_metrics,
)
from observability.v074.normative_boundary_metrics import collect_normative_boundary_metrics
from observability.v074.normative_integrity_metrics import collect_normative_integrity_metrics
from observability.v074.normative_provenance_metrics import collect_normative_provenance_metrics
from observability.v074.value_decay_metrics import collect_value_decay_metrics
from observability.v074.value_lineage_integrity_metrics import (
    collect_value_lineage_integrity_metrics,
)


def test_all_metrics_collect() -> None:
    assert collect_ethical_drift_containment_metrics().containment_rate == 1.0
    assert collect_normative_boundary_metrics().boundary_rate == 1.0
    assert collect_value_lineage_integrity_metrics().integrity_rate == 1.0
    assert collect_value_decay_metrics().decay_rate == 1.0
    assert collect_normative_provenance_metrics().provenance_rate == 1.0
    assert collect_normative_integrity_metrics().integrity_rate == 1.0
