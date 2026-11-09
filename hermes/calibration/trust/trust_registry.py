"""Persistent trust registry."""

from __future__ import annotations

from pathlib import Path
import json

from hermes.calibration.trust.trust_models import TrustRecord


class TrustRegistry:
    def __init__(self, path: str | Path = "reports/trust_registry.json"):
        self.path = Path(path)

    def load(self) -> dict[str, TrustRecord]:
        if not self.path.is_file():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {key: TrustRecord.from_dict(value) for key, value in raw.items()}

    def save(self, records: dict[str, TrustRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({key: value.to_dict() for key, value in records.items()}, indent=2, ensure_ascii=False), encoding="utf-8")

    def upsert_many(self, records: list[TrustRecord]) -> dict[str, TrustRecord]:
        current = self.load()
        for record in records:
            current[record.trust_id] = record
        self.save(current)
        return current
