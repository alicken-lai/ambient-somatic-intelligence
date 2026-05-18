"""Truth graph entropy adapter — duplicate, stale, checksum, version, orphan nodes."""

from __future__ import annotations

from kernel.entropy.entropy_metric import EntropyMetric, MetricKind
from kernel.truth.truth_graph import TruthGraph


class TruthEntropyAdapter:
    """
    Observes TruthGraph integrity signals without mutating the graph.

    Feeds EntropyController with duplicate nodes, stale timestamps, checksum
    divergence, version mismatch, and orphan truth nodes (no edges).
    """

    def observe(self, graph: TruthGraph | None) -> list[EntropyMetric]:
        if graph is None or not graph.nodes:
            return [
                EntropyMetric(
                    name="truth_empty_graph",
                    kind=MetricKind.DRIFT,
                    value=0.0,
                    source="kernel.entropy.truth_entropy_adapter",
                    detail="no truth graph supplied",
                )
            ]

        metrics: list[EntropyMetric] = []
        conflicts = graph.detect_conflicts()
        duplicates = [c for c in conflicts if c.conflict_type == "duplicate_version"]
        checksum_bad = [c for c in conflicts if c.conflict_type == "checksum_invalid"]
        version_cycles = [c for c in conflicts if c.conflict_type == "circular_dependency"]

        stale_ids = graph.stale_sources()
        orphan_ids = self._orphan_truth_nodes(graph)

        node_count = max(len(graph.nodes), 1)
        dup_score = min(1.0, len(duplicates) / node_count)
        stale_score = min(1.0, len(stale_ids) / node_count)
        checksum_score = min(1.0, len(checksum_bad) / node_count)
        version_score = min(1.0, len(version_cycles) * 0.5)
        orphan_score = min(1.0, len(orphan_ids) / node_count)

        metrics.extend(
            [
                EntropyMetric(
                    name="truth_duplicate_nodes",
                    kind=MetricKind.DRIFT,
                    value=dup_score,
                    weight=1.5,
                    source="kernel.entropy.truth_entropy_adapter",
                    detail=f"{len(duplicates)} duplicate version entries",
                    metadata={"node_ids": [c.node_id for c in duplicates[:20]]},
                ),
                EntropyMetric(
                    name="truth_stale_timestamps",
                    kind=MetricKind.DRIFT,
                    value=stale_score,
                    weight=1.2,
                    source="kernel.entropy.truth_entropy_adapter",
                    detail=f"{len(stale_ids)} stale nodes",
                    metadata={"stale_ids": stale_ids[:20]},
                ),
                EntropyMetric(
                    name="truth_checksum_divergence",
                    kind=MetricKind.DRIFT,
                    value=checksum_score,
                    weight=1.5,
                    source="kernel.entropy.truth_entropy_adapter",
                    detail=f"{len(checksum_bad)} checksum mismatches",
                ),
                EntropyMetric(
                    name="truth_version_mismatch",
                    kind=MetricKind.DRIFT,
                    value=version_score,
                    weight=1.0,
                    source="kernel.entropy.truth_entropy_adapter",
                    detail=f"{len(version_cycles)} version/cycle conflicts",
                ),
                EntropyMetric(
                    name="truth_orphan_nodes",
                    kind=MetricKind.DRIFT,
                    value=orphan_score,
                    weight=0.8,
                    source="kernel.entropy.truth_entropy_adapter",
                    detail=f"{len(orphan_ids)} nodes without edges",
                    metadata={"orphan_ids": orphan_ids[:20]},
                ),
            ]
        )
        return metrics

    @staticmethod
    def _orphan_truth_nodes(graph: TruthGraph) -> list[str]:
        connected: set[str] = set()
        for edge in graph.edges:
            connected.add(edge.source_id)
            connected.add(edge.target_id)
        return [nid for nid in graph.nodes if nid not in connected]
