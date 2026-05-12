#!/usr/bin/env python3
"""Build the public README for Ambient Somatic Intelligence Alpha."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SNAPSHOT_MD = ROOT / "docs" / "public_architecture_snapshot.md"
README_MD = ROOT / "README.md"
LICENSE_FILE = ROOT / "LICENSE"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def parse_section(path: Path, heading: str) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    collected: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line[3:].strip() == heading
            continue
        if in_section and line.strip():
            collected.append(line.strip())
    return " ".join(collected).strip()


def parse_bullets(path: Path, heading: str) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    items: list[str] = []
    for line in lines:
        if line.startswith("## "):
            in_section = line[3:].strip() == heading
            continue
        if in_section and line.startswith("- "):
            items.append(line[2:].strip())
    return items


def milestone_log() -> list[str]:
    return [
        "Night 0: bootstrap and substrate initialization.",
        "Night 1: baseline identity and approval scaffolding.",
        "Night 2: telemetry capture and incident recall beginnings.",
        "Night 3: visual observation and OCR-adjacent checks.",
        "Night 4: dashboard and local state synthesis.",
        "Night 5: integrity and health scoring foundations.",
        "Night 6: memory pressure diagnosis and reflex review.",
        "Night 7: circadian baseline work.",
        "Night 8: system state synthesis.",
        "Night 9: dashboard synthesis.",
        "Night 10: digest generation.",
        "Night 11: anomaly explanation patterns.",
        "Night 12: memory integrity and incident review.",
        "Night 13: foundational self-model stabilization.",
        "Night 14: memory integrity audit.",
        "Night 15: single source of truth.",
        "Night 16: self-model query interface.",
        "Night 17: self-reflection loop.",
        "Night 18: circadian memory.",
        "Night 19: anomaly explanation engine.",
        "Night 20: operator briefing.",
        "Night 21: decision boundary protocol.",
        "Night 22: approval packet protocol.",
        "Night 23: pre-accident simulation.",
        "Night 24: Guardian dreaming.",
        "Night 25: recalibration queue.",
        "Night 26: MemPalace integration.",
        "Night 27: MemPalace recall interface.",
        "Night 28: operational identity.",
        "Night 29: public architecture snapshot.",
    ]


def architecture_diagram() -> list[str]:
    return [
        "```mermaid",
        "flowchart TD",
        "    T[Telemetry and incidents] --> B[Baselines and circadian context]",
        "    B --> S[System state and self-model]",
        "    S --> E[Explanations, reflections, briefings, simulations]",
        "    E --> G[Guardian boundary and review queues]",
        "    G --> M[MemPalace and identity]",
        "    M --> O[Operator review]",
        "    O -->|approval| X[Execution reserved]",
        "```",
    ]


def build_readme() -> dict[str, Any]:
    snapshot = load_text(PUBLIC_SNAPSHOT_MD)
    if not snapshot:
        raise RuntimeError("docs/public_architecture_snapshot.md is missing; run public-architecture-build first")
    mission = parse_section(PUBLIC_SNAPSHOT_MD, "Mission")
    safety = parse_bullets(PUBLIC_SNAPSHOT_MD, "Safety Boundaries")
    limitations = parse_bullets(PUBLIC_SNAPSHOT_MD, "What It Does Not Do")
    roadmap = parse_bullets(PUBLIC_SNAPSHOT_MD, "Future Roadmap")
    capabilities = parse_bullets(PUBLIC_SNAPSHOT_MD, "Current Capabilities")
    milestones = milestone_log()
    readme_lines = [
        "# Ambient Somatic Intelligence Alpha",
        "",
        "## Project Thesis",
        "",
        mission or "Ambient Somatic Intelligence Alpha observes the system, explains drift, preserves memory, and prepares evidence for human review without taking unsanctioned corrective action.",
        "",
        "## Architecture Diagram",
        "",
        *architecture_diagram(),
        "",
        "## Current Features",
        "",
    ]
    for item in capabilities:
        readme_lines.append(f"- {item}")
    readme_lines.extend(
        [
            "",
            "## Safety Model",
            "",
        ]
    )
    for item in safety:
        readme_lines.append(f"- {item}")
    readme_lines.extend(
        [
            "",
            "## Night 0-29 Build Log",
            "",
        ]
    )
    for item in milestones:
        readme_lines.append(f"- {item}")
    readme_lines.extend(
        [
            "",
            "## Quickstart",
            "",
            "1. Read the public architecture snapshot to understand the operating model.",
            "2. Use the Guardian-gated CLI to inspect current state, explanations, simulations, and memory artifacts.",
            "3. Review the boundary protocol before treating any recommendation as an execution path.",
            "4. Prefer the public summaries and append-only artifacts over ad hoc inspection.",
            "",
            "## Limitations",
            "",
        ]
    )
    for item in limitations:
        readme_lines.append(f"- {item}")
    readme_lines.extend(
        [
            "",
            "## Roadmap",
            "",
        ]
    )
    for item in roadmap:
        readme_lines.append(f"- {item}")
    readme_lines.extend(
        [
            "",
            "## Source Basis",
            "",
            "This README is derived from the public architecture snapshot and the current public identity artifacts.",
        ]
    )
    return {
        "generated_at": utc_now(),
        "readme": "\n".join(readme_lines) + "\n",
        "summary": {
            "document": "README.md",
            "milestones_count": len(milestones),
            "recommendations_only": True,
        },
    }


def ensure_license_placeholder() -> None:
    if LICENSE_FILE.exists():
        return
    LICENSE_FILE.write_text(
        "License placeholder\n\n"
        "This repository does not yet have a final license selection.\n"
        "Replace this placeholder with the project license before public distribution.\n",
        encoding="utf-8",
    )


def write_readme(payload: dict[str, Any]) -> None:
    README_MD.write_text(payload["readme"], encoding="utf-8")


def run_build() -> dict[str, Any]:
    ensure_license_placeholder()
    payload = build_readme()
    write_readme(payload)
    record_checksum(README_MD, "github_readme_write", {"source": "public_architecture_snapshot"})
    record_checksum(LICENSE_FILE, "license_placeholder_write", {"source": "night30"})
    append_memory(stable_json(payload["summary"]), ["github", "readme", "night30"], "github_readme")
    log_action("github-readme:build", "completed", "ALLOW", payload["summary"])
    return {
        "readme": str(README_MD.relative_to(ROOT)),
        "license": str(LICENSE_FILE.relative_to(ROOT)),
        "recommendations_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the public README for Ambient Somatic Intelligence Alpha.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_build()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
