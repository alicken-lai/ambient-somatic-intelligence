"""Area 8: Phase 7 observability metrics."""

from observability.v071.bounded_consensus_metrics import collect_bounded_consensus_metrics
from observability.v071.contamination_guard_metrics import collect_contamination_guard_metrics
from observability.v071.divergence_containment_metrics import collect_divergence_containment_metrics
from observability.v071.reality_integrity_metrics import collect_reality_integrity_metrics
from observability.v071.replay_alignment_metrics import collect_replay_alignment_metrics
from observability.v071.truth_boundary_metrics import collect_truth_boundary_metrics


def test_all_six_metrics_pass() -> None:
    assert collect_divergence_containment_metrics().containment_rate == 1.0
    assert collect_bounded_consensus_metrics().bounded_rate == 1.0
    assert collect_truth_boundary_metrics().boundary_rate == 1.0
    assert collect_replay_alignment_metrics().alignment_rate == 1.0
    assert collect_contamination_guard_metrics().containment_rate == 1.0
    assert collect_reality_integrity_metrics().integrity_rate == 1.0
