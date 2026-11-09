"""Persistent evidence registry."""

from __future__ import annotations

from pathlib import Path
import json

from hermes.verification.evidence.evidence_models import Evidence


class EvidenceRegistry:
    def __init__(self, path: str | Path = "reports/evidence_registry.json"):
        self.path = Path(path)

    def load(self) -> dict[str, Evidence]:
        if not self.path.is_file():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {key: Evidence.from_dict(value) for key, value in raw.items()}

    def save(self, evidence: dict[str, Evidence]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({k: v.to_dict() for k, v in evidence.items()}, indent=2, ensure_ascii=False), encoding="utf-8")

    def upsert_many(self, items: list[Evidence]) -> dict[str, Evidence]:
        current = self.load()
        for item in items:
            current[item.evidence_id] = item
        self.save(current)
        return current
