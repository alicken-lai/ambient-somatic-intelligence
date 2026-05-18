"""Drift detector — observes divergence from registered truth baselines."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from kernel.entropy.entropy_metric import EntropyMetric, MetricKind
from kernel.truth.truth_graph import TruthGraph


@dataclass
class DriftObservation:
    node_id: str
    drift_score: float
    reason: str


class DriftDetector:
    """
    Observable drift against the truth graph.

    Does not mutate nodes — only reports drift metrics.
    """

    def __init__(self, truth_graph: TruthGraph | None = None) -> None:
        self._graph = truth_graph
        self._observations: list[DriftObservation] = []

    @property
    def observations(self) -> list[DriftObservation]:
        return list(self._observations)

    def observe(self, truth_graph: TruthGraph | None = None) -> list[EntropyMetric]:
        """Scan truth graph for stale sources and checksum failures."""
        graph = truth_graph or self._graph
        if graph is None:
            return []

        self._observations.clear()
        metrics: list[EntropyMetric] = []

        stale = graph.stale_sources()
        if graph.nodes:
            stale_ratio = len(stale) / len(graph.nodes)
        else:
            stale_ratio = 0.0

        metrics.append(
            EntropyMetric(
                name="truth_stale_ratio",
                kind=MetricKind.DRIFT,
                value=min(1.0, stale_ratio),
                weight=1.2,
                source="kernel.entropy.drift_detector",
                detail=f"{len(stale)} stale of {len(graph.nodes)} nodes",
                metadata={"stale_ids": stale[:20]},
            )
        )

        checksum_reports = graph.validate_checksums()
        invalid = [r for r in checksum_reports if not r.valid]
        invalid_ratio = len(invalid) / max(len(checksum_reports), 1)
        metrics.append(
            EntropyMetric(
                name="truth_checksum_drift",
                kind=MetricKind.DRIFT,
                value=min(1.0, invalid_ratio),
                weight=1.5,
                source="kernel.entropy.drift_detector",
                detail=f"{len(invalid)} checksum mismatches",
            )
        )

        conflicts = graph.detect_conflicts()
        conflict_score = min(1.0, len(conflicts) * 0.25)
        metrics.append(
            EntropyMetric(
                name="truth_conflict_pressure",
                kind=MetricKind.DRIFT,
                value=conflict_score,
                weight=1.0,
                source="kernel.entropy.drift_detector",
                detail=f"{len(conflicts)} graph conflicts",
            )
        )

        for obs in stale:
            self._observations.append(
                DriftObservation(node_id=obs, drift_score=0.5, reason="stale_timestamp")
            )
        for report in invalid:
            self._observations.append(
                DriftObservation(
                    node_id=report.node_id,
                    drift_score=1.0,
                    reason="checksum_mismatch",
                )
            )

        return metrics

    def record_external_drift(
        self,
        subsystem: str,
        score: float,
        reason: str,
    ) -> EntropyMetric:
        """Record drift observed from an external subsystem hook."""
        metric = EntropyMetric(
            name=f"external_drift_{subsystem}",
            kind=MetricKind.DRIFT,
            value=max(0.0, min(1.0, score)),
            source=f"subsystem.{subsystem}",
            detail=reason,
            metadata={"observed_at": datetime.now(timezone.utc).isoformat()},
        )
        return metric
