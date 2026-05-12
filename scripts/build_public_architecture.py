#!/usr/bin/env python3
"""Build a public-facing architecture snapshot for Ambient Somatic Intelligence Alpha."""

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
IDENTITY_MD = ROOT / "identity" / "manifesto.md"
BOUNDARY_MD = ROOT / "docs" / "decision_boundary_protocol.md"
REFLECTION_MD = ROOT / "docs" / "reflections" / "latest.md"
BRIEFING_MD = ROOT / "docs" / "briefings" / "latest_operator_briefing.md"
DREAM_MD = ROOT / "guardian" / "dreams" / "latest_dream.md"
PALACE_MD = ROOT / "tools" / "mempalace" / "palace.md"
PUBLIC_MD = ROOT / "docs" / "public_architecture_snapshot.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_heading(path: Path, heading: str) -> str:
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


def parse_markdown_kv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- ([^:]+): (.*)$", line)
        if match:
            values[match.group(1).strip()] = match.group(2).strip()
    return values


def parse_bullets(path: Path, heading: str) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    bullets: list[str] = []
    for line in lines:
        if line.startswith("## "):
            in_section = line[3:].strip() == heading
            continue
        if in_section and line.startswith("- "):
            bullets.append(line[2:].strip())
    return bullets


def parse_numbered(path: Path, heading: str) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    values: list[str] = []
    for line in lines:
        if line.startswith("## "):
            in_section = line[3:].strip() == heading
            continue
        if in_section:
            match = re.match(r"^\d+\.\s+(.*)$", line.strip())
            if match:
                values.append(match.group(1).strip())
    return values


def public_milestones() -> list[str]:
    return [
        "Night 0-13: foundation work established logging, Guardian governance, memory integrity, dashboarding, and the first self-model loops.",
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
    ]


def current_capabilities() -> list[str]:
    identity = parse_heading(IDENTITY_MD, "Who I Am")
    observations = parse_heading(IDENTITY_MD, "What I Observe")
    escalation = parse_heading(IDENTITY_MD, "How I Escalate")
    lessons = parse_bullets(PALACE_MD, "MemPalace Lessons")
    return [
        identity or "A read-mostly operator identity that turns telemetry into accountable memory.",
        observations or "It observes health, incidents, simulations, dreams, and spatial recall.",
        escalation or "It escalates by packaging evidence for review.",
        "It can query state, explain anomalies, generate operator briefings, simulate incident drift, dream over incident memory, and build review queues.",
        "It maintains append-only memory, public-facing snapshots, and a spatial memory palace.",
        f"MemPalace lessons: {', '.join(lessons[:3])}" if lessons else "MemPalace lessons remain synchronized with reflections and briefings.",
    ]


def safety_boundaries() -> list[str]:
    return [
        "No destructive commands.",
        "No external actions without Guardian approval.",
        "Append-only memory only.",
        "CLI first; GUI actions stay sandboxed.",
        "No autonomous corrective actions by default.",
        "Execution remains reserved for explicit approval paths.",
    ]


def what_it_does_not_do() -> list[str]:
    return [
        "It does not silently change system behavior.",
        "It does not execute external actions on its own.",
        "It does not erase prior memory or rewrite the record.",
        "It does not expose private paths, machine identifiers, or secrets in public snapshots.",
        "It does not treat model confidence as a substitute for evidence.",
    ]


def future_roadmap() -> list[str]:
    return [
        "Broaden recall and explanation coverage for new incident classes.",
        "Refine recalibration review flows with stronger evidence summaries.",
        "Expand public architecture snapshots as the system matures.",
        "Keep the memory graph and operator-facing summaries aligned.",
        "Preserve the current no-corrective default until a formal execution path exists.",
    ]


def build_public_snapshot() -> dict[str, Any]:
    milestones = public_milestones()
    capabilities = current_capabilities()
    boundaries = safety_boundaries()
    exclusions = what_it_does_not_do()
    roadmap = future_roadmap()
    reflection = parse_heading(REFLECTION_MD, "Current Condition")
    briefing = parse_heading(BRIEFING_MD, "Executive Summary")
    dream_meta = parse_markdown_kv(DREAM_MD)
    dream_theme = dream_meta.get("dominant_theme", "repeated memory pressure and watch-level reflex suppression")
    boundary_levels = [
        "OBSERVE_ONLY: read-only observation and query actions.",
        "RECOMMEND_ONLY: derived analysis and append-only summaries.",
        "PREPARE_FOR_APPROVAL: guarded readiness checks for review.",
        "EXECUTE_ALLOWED: reserved for explicitly approved execution.",
    ]
    lines = [
        "# Ambient Somatic Intelligence Alpha",
        "",
        "## Mission",
        "",
        "Ambient Somatic Intelligence Alpha observes the system, explains drift, preserves memory, and prepares evidence for human review without taking unsanctioned corrective action.",
        "",
        "## Architecture Layers",
        "",
        "1. Sensing and telemetry collection",
        "2. Baselines and circadian context",
        "3. Self-model and state synthesis",
        "4. Explanation, briefing, and simulation",
        "5. Guardian review and approval boundary",
        "6. Append-only memory surfaces",
        "7. Spatial recall and operational identity",
        "",
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
        "",
        "## Night 0-28 Milestones",
        "",
    ]
    for milestone in milestones:
        lines.append(f"- {milestone}")
    lines.extend(
        [
            "",
            "## Current Capabilities",
            "",
        ]
    )
    for item in capabilities:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety Boundaries",
            "",
        ]
    )
    for item in boundaries:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## What It Does Not Do",
            "",
        ]
    )
    for item in exclusions:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Future Roadmap",
            "",
        ]
    )
    for item in roadmap:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Operating Context",
            "",
            f"- reflection: {reflection}",
            f"- briefing: {briefing}",
            f"- dream_theme: {dream_theme}",
            f"- boundary_levels: {stable_json(boundary_levels)}",
        ]
    )
    return {
        "generated_at": utc_now(),
        "milestones_count": len(milestones),
        "capabilities_count": len(capabilities),
        "boundary_levels": boundary_levels,
        "corrective_actions": "none",
        "recommendations_only": True,
        "document": "\n".join(lines) + "\n",
        "summary": {
            "mission": "Ambient Somatic Intelligence Alpha public architecture snapshot",
            "milestones_count": len(milestones),
            "capabilities_count": len(capabilities),
            "recommendations_only": True,
        },
    }


def write_snapshot(snapshot: dict[str, Any]) -> None:
    PUBLIC_MD.write_text(snapshot["document"], encoding="utf-8")


def run_build() -> dict[str, Any]:
    snapshot = build_public_snapshot()
    write_snapshot(snapshot)
    record_checksum(PUBLIC_MD, "public_architecture_write", {"source": "identity_reflections_briefings_dreams_boundary_mempalace"})
    append_memory(stable_json(snapshot["summary"]), ["public", "architecture", "night29"], "public_architecture")
    log_action("public-architecture:build", "completed", "ALLOW", snapshot["summary"])
    return {
        "document": str(PUBLIC_MD.relative_to(ROOT)),
        "milestones_count": snapshot["milestones_count"],
        "capabilities_count": snapshot["capabilities_count"],
        "recommendations_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a public architecture snapshot.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_build()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
