"""Area 8: Phase 7 observability metrics."""

from observability.v072.continuity_integrity_metrics import collect_continuity_integrity_metrics
from observability.v072.epoch_boundary_metrics import collect_epoch_boundary_metrics
from observability.v072.fragmentation_containment_metrics import (
    collect_fragmentation_containment_metrics,
)
from observability.v072.lineage_integrity_metrics import collect_lineage_integrity_metrics
from observability.v072.memory_decay_metrics import collect_memory_decay_metrics
from observability.v072.temporal_provenance_metrics import collect_temporal_provenance_metrics


def test_six_metric_collectors() -> None:
    assert collect_fragmentation_containment_metrics().containment_rate == 1.0
    assert collect_epoch_boundary_metrics().boundary_rate == 1.0
    assert collect_lineage_integrity_metrics().integrity_rate == 1.0
    assert collect_memory_decay_metrics().decay_rate == 1.0
    assert collect_temporal_provenance_metrics().provenance_rate == 1.0
    assert collect_continuity_integrity_metrics().integrity_rate == 1.0
