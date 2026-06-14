"""Persistent advisory strategy memory."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any


class StrategyMemory:
    def __init__(self, path: str | Path = "reports/deliberation_strategy_memory.jsonl"):
        self.path = Path(path)

    def append(self, record: dict[str, Any]) -> None:
        safe = {
            "selected_strategy": record.get("selected_strategy"),
            "outcome": record.get("outcome"),
            "roi": record.get("roi", 0),
            "quality_score": record.get("quality_score", 0),
            "verification_score": record.get("verification_score", 0),
            "guardian_result": record.get("guardian_result", "NOT_REQUIRED"),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(safe, ensure_ascii=False) + "\n")

    def load(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
