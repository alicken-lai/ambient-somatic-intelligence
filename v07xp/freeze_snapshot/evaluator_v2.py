"""CLI entry for civilization freeze snapshot V2 (v0.7.x-P stabilization)."""

from __future__ import annotations

import json
from pathlib import Path

from observability.v07xp_freeze.civilization_lineage_integrity_score_v2 import (
    CivilizationFreezeSnapshotV2,
    evaluate_civilization_lineage_integrity_v2,
)

_SNAPSHOT = Path(__file__).resolve().parent / "civilization_freeze_snapshot_v2.json"
_MD_REPORT = Path(__file__).resolve().parent / "civilization_lineage_integrity_v2.md"


def write_snapshot(path: Path | None = None) -> dict:
    path = path or _SNAPSHOT
    report = evaluate_civilization_lineage_integrity_v2()
    snapshot = CivilizationFreezeSnapshotV2(report=report)
    payload = snapshot.to_dict()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_markdown(report, _MD_REPORT)
    return payload


def _write_markdown(report, md_path: Path) -> None:
    lines = [
        "# Civilization Lineage Integrity V2",
        "",
        f"- **lineage_integrity_score:** {report.lineage_integrity_score:.6f}",
        f"- **gate_pass:** {report.gate_pass}",
        f"- **gate_threshold:** {report.gate_threshold}",
        f"- **classification:** {report.classification}",
        f"- **weakest layer:** {min(report.layers, key=lambda x: x['primary_score'])['version']}",
        f"- **horizon_fix:** {report.horizon_fix}",
        "",
        "## Layers",
        "",
        "| version | primary_score | gate_pass |",
        "|---------|---------------|-----------|",
    ]
    for layer in report.layers:
        lines.append(
            f"| {layer['version']} | {layer['primary_score']:.6f} | {layer['gate_pass']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    data = write_snapshot()
    print(data["lineage_integrity_score"], data["gate_pass"])
