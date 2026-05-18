"""Orphan module pressure — classify lifecycle without deleting modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from kernel.entropy.entropy_metric import EntropyMetric, MetricKind


class ModuleLifecycle(str, Enum):
    """Module reachability classification (observable only)."""

    ACTIVE = "active"
    EXPERIMENTAL = "experimental"
    ORPHAN = "orphan"
    DEPRECATED = "deprecated"


@dataclass
class ClassifiedModule:
    module_path: str
    lifecycle: ModuleLifecycle
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_path": self.module_path,
            "lifecycle": self.lifecycle.value,
            "reason": self.reason,
        }


@dataclass
class OrphanPressureReport:
    classified: list[ClassifiedModule] = field(default_factory=list)
    orphan_rate: float = 0.0
    pressure_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        counts = {lc.value: 0 for lc in ModuleLifecycle}
        for item in self.classified:
            counts[item.lifecycle.value] = counts.get(item.lifecycle.value, 0) + 1
        return {
            "orphan_rate": round(self.orphan_rate, 4),
            "pressure_score": round(self.pressure_score, 4),
            "counts": counts,
            "sample": [c.to_dict() for c in self.classified[:30]],
        }


# Baseline from v0.4 architecture truth scan (README / graph_truth_layer).
_V04_ORPHAN_BASELINE: dict[str, ModuleLifecycle] = {
    "runtime/entropy_controller": ModuleLifecycle.ACTIVE,
    "observability/drift_detection": ModuleLifecycle.ACTIVE,
    "architecture/graph_truth_layer": ModuleLifecycle.EXPERIMENTAL,
}


class OrphanPressure:
    """
    Computes orphan pressure from classified module paths.

    Does not delete or quarantine modules — classification only.
    """

    EXPERIMENTAL_PREFIXES = (
        "architecture/",
        "experiments/",
        "sandbox/",
    )
    DEPRECATED_MARKERS = ("_legacy", "_deprecated", "/legacy/")

    def __init__(self) -> None:
        self._classified: list[ClassifiedModule] = []

    @property
    def classified(self) -> list[ClassifiedModule]:
        return list(self._classified)

    def classify_modules(
        self,
        all_modules: list[str],
        reachable: set[str] | None = None,
    ) -> OrphanPressureReport:
        """Classify modules; reachable set from static graph when available."""
        reachable = reachable or set()
        self._classified = []

        for module_path in sorted(all_modules):
            lifecycle, reason = self._classify_one(module_path, reachable)
            self._classified.append(
                ClassifiedModule(module_path=module_path, lifecycle=lifecycle, reason=reason)
            )

        total = max(len(all_modules), 1)
        orphans = [c for c in self._classified if c.lifecycle == ModuleLifecycle.ORPHAN]
        orphan_rate = len(orphans) / total
        pressure = min(1.0, orphan_rate * 1.5)

        report = OrphanPressureReport(
            classified=self._classified,
            orphan_rate=orphan_rate,
            pressure_score=pressure,
        )
        return report

    def _classify_one(
        self,
        module_path: str,
        reachable: set[str],
    ) -> tuple[ModuleLifecycle, str]:
        normalized = module_path.replace("\\", "/")
        for prefix, lifecycle in _V04_ORPHAN_BASELINE.items():
            if normalized.startswith(prefix):
                return lifecycle, "v04_baseline"

        if any(marker in normalized for marker in self.DEPRECATED_MARKERS):
            return ModuleLifecycle.DEPRECATED, "deprecated_marker"

        if any(normalized.startswith(p) for p in self.EXPERIMENTAL_PREFIXES):
            return ModuleLifecycle.EXPERIMENTAL, "experimental_prefix"

        module_key = normalized.replace("/", ".").removesuffix(".py")
        if module_key in reachable or normalized in reachable:
            return ModuleLifecycle.ACTIVE, "reachable_from_kernel"

        return ModuleLifecycle.ORPHAN, "unreachable_from_entry_points"

    def observe(
        self,
        all_modules: list[str] | None = None,
        reachable: set[str] | None = None,
    ) -> list[EntropyMetric]:
        if all_modules is None:
            all_modules = []
        report = self.classify_modules(all_modules, reachable)
        return [
            EntropyMetric(
                name="orphan_pressure",
                kind=MetricKind.ORPHAN,
                value=report.pressure_score,
                weight=1.0,
                source="kernel.entropy.orphan_pressure",
                detail=f"orphan_rate={report.orphan_rate:.2%}",
                metadata=report.to_dict(),
            ),
            EntropyMetric(
                name="orphan_rate",
                kind=MetricKind.ORPHAN,
                value=min(1.0, report.orphan_rate),
                weight=0.8,
                source="kernel.entropy.orphan_pressure",
                detail=f"{sum(1 for c in report.classified if c.lifecycle == ModuleLifecycle.ORPHAN)} orphans",
            ),
        ]
