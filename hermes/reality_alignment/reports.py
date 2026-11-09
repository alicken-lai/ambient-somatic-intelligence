"""Reports for the institutional reality alignment kernel."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermes.reality_alignment.alignment_engine import RealityAlignmentEngine


def build_reality_alignment_assets() -> dict[str, Any]:
    return RealityAlignmentEngine().align()


def generate_reality_report(output_path: str | Path = "reports/reality_alignment_report.md") -> dict[str, Any]:
    assets = build_reality_alignment_assets()
    lines = [
        "# Reality Alignment Report",
        "",
        f"Reality Score: {assets['reality_score']:.2f}",
        f"Echo Risk: {assets['echo']['echo_risk']} - {assets['echo']['reason']}",
        "",
        "Reality alignment remains advisory and may not override Guardian, governance, provider permissions, credential policies, or approval requirements.",
        "",
        "## Challenge Results",
        "",
    ]
    for item in assets["challenges"]:
        status = "PASS" if item["passed"] else "REVERIFY"
        lines.append(f"- {item['target_id']}: {status} ({item['reality_score']:.2f}) - {item['reason']}")
    lines.extend(["", "## Belief Evolution", ""])
    for belief in assets["beliefs"].values():
        lines.append(f"- {belief['belief_id']}: {belief['status']} / confidence {belief['confidence']}")
    return _write(output_path, lines, assets)


def generate_diversity_report(output_path: str | Path = "reports/diversity_report.md") -> dict[str, Any]:
    assets = build_reality_alignment_assets()
    diversity = assets["diversity"]
    lines = [
        "# Diversity Report",
        "",
        f"Diversity Score: {diversity['diversity_score']:.2f}",
        f"Internal Ratio: {diversity['internal_ratio']:.4f}",
        f"External Ratio: {diversity['external_ratio']:.4f}",
        f"Source Variety: {diversity['source_variety']}",
        f"Source Concentration: {diversity['source_concentration']:.4f}",
        "",
        "## Echo Chamber Indicators",
        "",
        f"- Echo risk: {assets['echo']['echo_risk']}",
        f"- Reason: {assets['echo']['reason']}",
        "",
        "## Recommendations",
        "",
    ]
    if diversity["external_ratio"] < 0.35:
        lines.append("- Add benchmark, test, or external validation observations before increasing confidence.")
    if diversity["source_concentration"] > 0.4:
        lines.append("- Reduce reliance on the most repeated internal source.")
    if len(lines) and lines[-1] == "## Recommendations":
        lines.append("- Current source diversity is acceptable for advisory reuse.")
    return _write(output_path, lines, {"diversity": diversity, "echo": assets["echo"]})


def generate_fitness_report(output_path: str | Path = "reports/institutional_fitness_report.md") -> dict[str, Any]:
    assets = build_reality_alignment_assets()
    fitness = sorted(assets["fitness"], key=lambda item: item["fitness_score"], reverse=True)
    lines = [
        "# Institutional Fitness Report",
        "",
        f"Reality Score: {assets['reality_score']:.2f}",
        "",
        "## Highest Fitness Beliefs",
        "",
    ]
    for item in fitness[:5]:
        lines.append(f"- {item['target_id']} ({item['target_type']}): {item['fitness_score']:.2f} / {item['trend']}")
    lines.extend(["", "## Lowest Fitness Beliefs", ""])
    for item in fitness[-5:]:
        lines.append(f"- {item['target_id']} ({item['target_type']}): {item['fitness_score']:.2f} / {item['trend']}")
    lines.extend(["", "## Most Effective Playbooks", ""])
    for item in [entry for entry in fitness if entry["target_type"] == "playbook"][:5]:
        lines.append(f"- {item['target_id']}: {item['fitness_score']:.2f}")
    lines.extend(["", "## Most Effective Skills", ""])
    for item in [entry for entry in fitness if entry["target_type"] == "skill"][:5]:
        lines.append(f"- {item['target_id']}: {item['fitness_score']:.2f}")
    return _write(output_path, lines, {"fitness": fitness, "reality_score": assets["reality_score"], "challenges": assets["challenges"]})


def _write(path: str | Path, lines: list[str], payload: dict[str, Any]) -> dict[str, Any]:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = output.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**payload, "report_path": str(output), "json_path": str(json_path)}
