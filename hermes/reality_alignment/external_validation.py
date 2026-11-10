"""Advisory external validation registry.

This module defines validation sources and outcomes only. It does not perform
network calls or automatic external actions.
"""

from __future__ import annotations

import json
from pathlib import Path

from hermes.reality_alignment.reality_models import ValidationOutcome, ValidationSource


class ExternalValidationRegistry:
    def __init__(self, path: str | Path = "reports/external_validation_registry.json"):
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.is_file():
            return {"sources": {}, "outcomes": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def register_source(self, source: ValidationSource) -> dict:
        payload = self.load()
        payload["sources"][source.source_id] = source.to_dict()
        self._save(payload)
        return payload

    def record_outcome(self, outcome: ValidationOutcome) -> dict:
        payload = self.load()
        payload["outcomes"].append(outcome.to_dict())
        self._save(payload)
        return payload

    def _save(self, payload: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
