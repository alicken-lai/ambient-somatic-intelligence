"""Configurable ROI calculator for deliberation modes."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from hermes.deliberation.roi.roi_models import ROIRecord, ROIWeights


RESOURCE_COST = {"single": 1.0, "light": 2.0, "full": 3.0, "guardian_required": 3.5}


class ROICalculator:
    def __init__(self, weights: ROIWeights | None = None, history_path: str | Path = "reports/deliberation_roi_history.jsonl"):
        self.weights = weights or ROIWeights()
        self.history_path = Path(history_path)

    def calculate(
        self,
        *,
        task_type: str,
        mode: str,
        baseline_quality: float,
        mode_quality: float,
        baseline_verification: float = 0.0,
        mode_verification: float = 0.0,
        latency_cost: float = 1.0,
        resource_cost: float | None = None,
    ) -> ROIRecord:
        resource = RESOURCE_COST.get(mode, 2.0) if resource_cost is None else resource_cost
        return calculate_roi_from_scores(
            task_type=task_type,
            mode=mode,
            quality_gain=mode_quality - baseline_quality,
            verification_gain=mode_verification - baseline_verification,
            latency_cost=latency_cost,
            resource_cost=resource,
            weights=self.weights,
        )

    def append(self, record: ROIRecord) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def load_history(self) -> list[ROIRecord]:
        if not self.history_path.is_file():
            return []
        return [
            ROIRecord(**json.loads(line))
            for line in self.history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


def calculate_roi_from_scores(
    *,
    task_type: str,
    mode: str,
    quality_gain: float,
    latency_cost: float,
    resource_cost: float,
    verification_gain: float = 0.0,
    weights: ROIWeights | None = None,
) -> ROIRecord:
    weights = weights or ROIWeights()
    denominator = max(
        weights.denominator_floor,
        (latency_cost * weights.latency_weight) + (resource_cost * weights.resource_weight),
    )
    adjusted_gain = quality_gain + (verification_gain * weights.verification_weight)
    roi = adjusted_gain / denominator
    return ROIRecord(
        task_type=task_type,
        mode=mode,
        quality_gain=round(quality_gain, 4),
        latency_cost=round(latency_cost, 4),
        resource_cost=round(resource_cost, 4),
        verification_gain=round(verification_gain, 4),
        overall_roi=round(roi, 4),
    )
