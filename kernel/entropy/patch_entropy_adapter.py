"""Patch registry entropy adapter — active patches, churn, overlap, age."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from kernel.entropy.entropy_metric import EntropyMetric, MetricKind

if TYPE_CHECKING:
    from kernel.wiring.patch_registry import PatchRegistry


class PatchEntropyAdapter:
    """
    Read-only PatchRegistry observability.

    Metrics: active patch count, churn, target overlap, mean age, restore ratio.
    """

    def __init__(self, max_age_seconds: float = 3600.0) -> None:
        self._max_age = max_age_seconds

    def observe(self, registry: PatchRegistry | None = None) -> list[EntropyMetric]:
        if registry is None:
            from kernel.wiring.patch_registry import get_patch_registry

            registry = get_patch_registry()

        snapshot = registry.entropy_snapshot()
        active_count = snapshot["active_count"]
        total = max(snapshot["total_count"], 1)
        churn = min(1.0, snapshot["register_churn"] / 20.0)
        overlap = min(1.0, snapshot["target_overlap"] / max(active_count, 1))
        age_pressure = min(1.0, snapshot["mean_age_seconds"] / self._max_age)
        restore_fail = 1.0 - snapshot["unwire_success_ratio"]

        leakage = min(1.0, snapshot["inactive_but_registered"] / total)

        return [
            EntropyMetric(
                name="patch_active_pressure",
                kind=MetricKind.PATCH,
                value=min(1.0, active_count / 15.0),
                weight=1.2,
                source="kernel.entropy.patch_entropy_adapter",
                detail=f"{active_count} active patches",
                metadata=snapshot,
            ),
            EntropyMetric(
                name="patch_churn",
                kind=MetricKind.PATCH,
                value=churn,
                weight=1.0,
                source="kernel.entropy.patch_entropy_adapter",
                detail=f"churn={snapshot['register_churn']}",
            ),
            EntropyMetric(
                name="patch_overlap",
                kind=MetricKind.PATCH,
                value=overlap,
                weight=1.3,
                source="kernel.entropy.patch_entropy_adapter",
                detail=f"overlap={snapshot['target_overlap']}",
            ),
            EntropyMetric(
                name="patch_age_pressure",
                kind=MetricKind.PATCH,
                value=age_pressure,
                weight=0.8,
                source="kernel.entropy.patch_entropy_adapter",
                detail=f"mean_age={snapshot['mean_age_seconds']:.0f}s",
            ),
            EntropyMetric(
                name="patch_leakage",
                kind=MetricKind.PATCH,
                value=leakage,
                weight=1.5,
                source="kernel.entropy.patch_entropy_adapter",
                detail=f"inactive_registered={snapshot['inactive_but_registered']}",
            ),
            EntropyMetric(
                name="patch_unwire_failure",
                kind=MetricKind.PATCH,
                value=restore_fail,
                weight=1.2,
                source="kernel.entropy.patch_entropy_adapter",
                detail=f"unwire_success={snapshot['unwire_success_ratio']:.2f}",
            ),
        ]
