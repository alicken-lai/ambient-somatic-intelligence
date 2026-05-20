"""Fixture matches clean-graph doctrine."""

from kernel.entropy.truth_entropy_adapter import TruthEntropyAdapter


def test_edgeless_truth_graph_not_orphan(truth_graph) -> None:
    orphans = TruthEntropyAdapter._orphan_truth_nodes(truth_graph)
    assert orphans == []
    metrics = TruthEntropyAdapter().observe(truth_graph)
    orphan_metric = next(m for m in metrics if m.name == "truth_orphan_nodes")
    assert orphan_metric.value == 0.0
