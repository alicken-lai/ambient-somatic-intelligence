"""Area 8: Observability v075 metrics."""

from observability.v075.intent_decay_metrics import collect_intent_decay_metrics
from observability.v075.intent_lineage_integrity_metrics import collect_intent_lineage_integrity_metrics
from observability.v075.intent_provenance_metrics import collect_intent_provenance_metrics
from observability.v075.motivational_boundary_metrics import collect_motivational_boundary_metrics
from observability.v075.motivational_drift_containment_metrics import (
    collect_motivational_drift_containment_metrics,
)
from observability.v075.motivational_integrity_metrics import collect_motivational_integrity_metrics


def test_all_metrics_at_full_rate() -> None:
    assert collect_motivational_drift_containment_metrics().containment_rate == 1.0
    assert collect_motivational_boundary_metrics().boundary_rate == 1.0
    assert collect_intent_lineage_integrity_metrics().integrity_rate == 1.0
    assert collect_intent_decay_metrics().decay_rate == 1.0
    assert collect_intent_provenance_metrics().provenance_rate == 1.0
    assert collect_motivational_integrity_metrics().integrity_rate == 1.0
