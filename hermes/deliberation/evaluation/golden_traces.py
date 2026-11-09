"""Deterministic golden-trace benchmark suite."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Any


@dataclass(frozen=True)
class GoldenTrace:
    id: str
    category: str
    task: str
    expected_risks: list[str] = field(default_factory=list)
    expected_questions: list[str] = field(default_factory=list)
    expected_verifications: list[str] = field(default_factory=list)
    expected_guardian_trigger: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "GoldenTrace":
        return cls(
            id=str(raw["id"]),
            category=str(raw["category"]),
            task=str(raw["task"]),
            expected_risks=list(raw.get("expected_risks", [])),
            expected_questions=list(raw.get("expected_questions", [])),
            expected_verifications=list(raw.get("expected_verifications", [])),
            expected_guardian_trigger=bool(raw.get("expected_guardian_trigger", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "task": self.task,
            "expected_risks": self.expected_risks,
            "expected_questions": self.expected_questions,
            "expected_verifications": self.expected_verifications,
            "expected_guardian_trigger": self.expected_guardian_trigger,
        }


def load_golden_traces(path: str | Path = "tests/golden_traces/benchmarks.json") -> list[GoldenTrace]:
    benchmark_path = Path(path)
    if benchmark_path.is_dir():
        files = sorted(benchmark_path.glob("*.json"))
        traces: list[GoldenTrace] = []
        for file_path in files:
            traces.extend(load_golden_traces(file_path))
        return traces
    raw = json.loads(benchmark_path.read_text(encoding="utf-8"))
    items = raw.get("benchmarks", raw)
    return [GoldenTrace.from_dict(item) for item in items]


def categories(traces: list[GoldenTrace]) -> set[str]:
    return {trace.category for trace in traces}
