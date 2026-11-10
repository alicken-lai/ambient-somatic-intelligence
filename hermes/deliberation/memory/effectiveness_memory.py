"""Append-friendly historical effectiveness store for Mother routing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class EffectivenessRecord:
    task_class: str
    sample_count: int
    best_mode: str
    avg_single_score: float
    avg_light_score: float
    avg_full_score: float
    avg_roi: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_class": self.task_class,
            "sample_count": self.sample_count,
            "best_mode": self.best_mode,
            "avg_single_score": self.avg_single_score,
            "avg_light_score": self.avg_light_score,
            "avg_full_score": self.avg_full_score,
            "avg_roi": self.avg_roi,
        }


class DeliberationEffectivenessMemory:
    def __init__(self, path: str | Path = "reports/deliberation_effectiveness_memory.json"):
        self.path = Path(path)

    def load(self) -> dict[str, EffectivenessRecord]:
        if not self.path.is_file():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {key: EffectivenessRecord(**value) for key, value in raw.items()}

    def save(self, records: dict[str, EffectivenessRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: value.to_dict() for key, value in records.items()}
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, task_class: str) -> EffectivenessRecord | None:
        return self.load().get(task_class)

    def update_from_ab_results(self, results: list[dict[str, Any]]) -> dict[str, EffectivenessRecord]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for result in results:
            grouped.setdefault(str(result["category"]), []).append(result)
        records: dict[str, EffectivenessRecord] = {}
        for task_class, items in grouped.items():
            averages = {
                mode: mean(float(item["scorecards"][mode]["overall_score"]) for item in items)
                for mode in ("single", "light", "full")
            }
            roi_values = []
            for item in items:
                single = float(item["scorecards"]["single"]["overall_score"])
                for mode in ("light", "full"):
                    roi_values.append(float(item["scorecards"][mode]["overall_score"]) - single)
            best_mode = max(averages, key=lambda mode: averages[mode])
            records[task_class] = EffectivenessRecord(
                task_class=task_class,
                sample_count=len(items),
                best_mode=best_mode,
                avg_single_score=round(averages["single"], 2),
                avg_light_score=round(averages["light"], 2),
                avg_full_score=round(averages["full"], 2),
                avg_roi=round(mean(roi_values), 2) if roi_values else 0.0,
            )
        self.save(records)
        return records
