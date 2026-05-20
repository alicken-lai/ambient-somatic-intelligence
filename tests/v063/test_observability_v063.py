"""Area 8: observability v063 metrics."""

from observability.v063.constitutional_coherence_metrics import (
    collect_constitutional_coherence_metrics,
)
from observability.v063.contradiction_metrics import collect_contradiction_metrics
from observability.v063.drift_metrics import collect_drift_metrics
from observability.v063.fragmentation_pressure_metrics import (
    collect_fragmentation_pressure_metrics,
)
from observability.v063.replay_coherence_metrics import collect_replay_coherence_metrics


def test_all_metrics_collect() -> None:
    assert collect_contradiction_metrics().resistance_rate >= 0.5
    assert collect_drift_metrics().bounded_rate >= 0.5
    assert collect_replay_coherence_metrics().coherence_rate >= 0.5
    assert collect_constitutional_coherence_metrics().alignment_rate >= 0.5
    assert collect_fragmentation_pressure_metrics().containment_rate >= 0.5
