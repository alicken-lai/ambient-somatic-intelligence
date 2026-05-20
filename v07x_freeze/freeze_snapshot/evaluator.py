"""CLI entry for civilization freeze snapshot generation."""

from __future__ import annotations

import json
from pathlib import Path

from observability.v07x_freeze.civilization_lineage_integrity_score import (
    evaluate_civilization_lineage_integrity,
)

_SNAPSHOT = Path(__file__).resolve().parent / "civilization_freeze_snapshot.json"


def write_snapshot(path: Path | None = None) -> dict:
    path = path or _SNAPSHOT
    report = evaluate_civilization_lineage_integrity()
    payload = report.to_dict()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    data = write_snapshot()
    print(data["lineage_integrity_score"], data["gate_pass"])
