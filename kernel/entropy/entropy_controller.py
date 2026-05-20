"""Entropy controller — aggregates metrics into a system entropy score."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from kernel.entropy.coupling_pressure import CouplingPressure
from kernel.entropy.drift_detector import DriftDetector
from kernel.entropy.entropy_metric import EntropyMetric, MetricKind, MetricSnapshot
from kernel.entropy.mutation_tracker import MutationTracker
from kernel.entropy.orphan_pressure import OrphanPressure
from kernel.entropy.patch_entropy_adapter import PatchEntropyAdapter
from kernel.entropy.stale_state_detector import StaleStateDetector
from kernel.entropy.truth_entropy_adapter import TruthEntropyAdapter
from kernel.truth.truth_graph import TruthGraph


class EntropyClassification(str, Enum):
    """Entropy score bands — observable only, no auto-remediation."""

    STABLE = "stable"           # < 0.30
    ACCEPTABLE = "acceptable"   # < 0.50
    WARNING = "warning"         # < 0.70
    UNSTABLE = "unstable"       # >= 0.70


@dataclass
class EntropyReport:
    """Aggregated entropy assessment."""

    score: float
    classification: EntropyClassification
    snapshot: MetricSnapshot
    breakdown: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "classification": self.classification.value,
            "breakdown": {k: round(v, 4) for k, v in self.breakdown.items()},
            "snapshot": self.snapshot.to_dict(),
        }


class EntropyController:
    """
    Aggregates drift, coupling, mutation, patch, orphan, and stale metrics.

    Observable only — never silently mutates subsystem state.
    """

    THRESHOLD_STABLE = 0.30
    THRESHOLD_ACCEPTABLE = 0.50
    THRESHOLD_WARNING = 0.70

    def __init__(
        self,
        truth_graph: TruthGraph | None = None,
        drift_detector: DriftDetector | None = None,
        coupling_pressure: CouplingPressure | None = None,
        mutation_tracker: MutationTracker | None = None,
        truth_adapter: TruthEntropyAdapter | None = None,
        patch_adapter: PatchEntropyAdapter | None = None,
        orphan_pressure: OrphanPressure | None = None,
        stale_detector: StaleStateDetector | None = None,
        root: Path | None = None,
    ) -> None:
        self.drift_detector = drift_detector or DriftDetector(truth_graph)
        self.coupling_pressure = coupling_pressure or CouplingPressure()
        self.mutation_tracker = mutation_tracker or MutationTracker()
        self.truth_adapter = truth_adapter or TruthEntropyAdapter()
        self.patch_adapter = patch_adapter or PatchEntropyAdapter()
        self.orphan_pressure = orphan_pressure or OrphanPressure()
        self.stale_detector = stale_detector or StaleStateDetector(root)
        self._last_report: EntropyReport | None = None

    @staticmethod
    def classify(score: float) -> EntropyClassification:
        if score < EntropyController.THRESHOLD_STABLE:
            return EntropyClassification.STABLE
        if score < EntropyController.THRESHOLD_ACCEPTABLE:
            return EntropyClassification.ACCEPTABLE
        if score < EntropyController.THRESHOLD_WARNING:
            return EntropyClassification.WARNING
        return EntropyClassification.UNSTABLE

    def collect_metrics(
        self,
        truth_graph: TruthGraph | None = None,
        bus_connections: list[str] | None = None,
        bus_event_log: list[Any] | None = None,
        orphan_modules: list[str] | None = None,
        reachable_modules: set[str] | None = None,
    ) -> MetricSnapshot:
        """Gather all entropy metrics without side effects."""
        metrics: list[EntropyMetric] = []
        metrics.extend(self.drift_detector.observe(truth_graph))
        metrics.extend(self.truth_adapter.observe(truth_graph))
        metrics.extend(self.patch_adapter.observe())
        metrics.extend(self.coupling_pressure.observe(bus_connections))
        metrics.extend(self.mutation_tracker.observe())
        metrics.extend(
            self.orphan_pressure.observe(
                all_modules=orphan_modules,
                reachable=reachable_modules,
            )
        )
        metrics.extend(
            self.stale_detector.observe(truth_graph, bus_event_log)
        )
        return MetricSnapshot(
            metrics=tuple(metrics),
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

    def compute(
        self,
        truth_graph: TruthGraph | None = None,
        bus_connections: list[str] | None = None,
        bus_event_log: list[Any] | None = None,
        orphan_modules: list[str] | None = None,
        reachable_modules: set[str] | None = None,
    ) -> EntropyReport:
        """Compute weighted entropy score and classification."""
        snapshot = self.collect_metrics(
            truth_graph,
            bus_connections,
            bus_event_log,
            orphan_modules,
            reachable_modules,
        )

        breakdown: dict[str, float] = {kind.value: 0.0 for kind in MetricKind}
        weights: dict[str, float] = {kind.value: 0.0 for kind in MetricKind}

        for metric in snapshot.metrics:
            kind = metric.kind.value
            breakdown[kind] = breakdown.get(kind, 0.0) + metric.weighted_value()
            weights[kind] = weights.get(kind, 0.0) + metric.weight

        total_weight = sum(weights.values()) or 1.0
        score = sum(breakdown.values()) / total_weight
        score = max(0.0, min(1.0, score))

        normalized = {
            k: (breakdown[k] / weights[k] if weights[k] > 0 else 0.0)
            for k in breakdown
        }

        report = EntropyReport(
            score=score,
            classification=self.classify(score),
            snapshot=snapshot,
            breakdown=normalized,
        )
        self._last_report = report
        return report

    @property
    def last_report(self) -> EntropyReport | None:
        return self._last_report
