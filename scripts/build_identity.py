#!/usr/bin/env python3
"""Build the operational identity artifacts for Ambient Somatic Intelligence."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json
from build_system_state import build_system_state
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
AGENTS_MD = ROOT / "AGENTS.md"
REFLECTION_MD = ROOT / "docs" / "reflections" / "latest.md"
BRIEFING_MD = ROOT / "docs" / "briefings" / "latest_operator_briefing.md"
DECISION_BOUNDARY_MD = ROOT / "docs" / "decision_boundary_protocol.md"
DREAM_MD = ROOT / "guardian" / "dreams" / "latest_dream.md"
PALACE_MD = ROOT / "tools" / "mempalace" / "palace.md"
IDENTITY_DIR = ROOT / "identity"
MANIFESTO_MD = IDENTITY_DIR / "manifesto.md"
CORE_VALUES_JSON = IDENTITY_DIR / "core_values.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


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


def mempalace_lessons(path: Path) -> list[str]:
    if not path.exists():
        return []
    lessons: list[str] = []
    current_domain = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current_domain = line[3:].strip()
            continue
        if line.startswith("- lessons:"):
            try:
                value = json.loads(line.split(": ", 1)[1])
            except Exception:
                continue
            if isinstance(value, list):
                lessons.extend(str(item) for item in value)
    return list(dict.fromkeys(lessons))


def identity_manifesto() -> str:
    reflection = parse_heading(REFLECTION_MD, "Current Condition")
    briefing = parse_heading(BRIEFING_MD, "Executive Summary")
    dream_theme = parse_heading(DREAM_MD, "Replay Window")
    palace_lessons = mempalace_lessons(PALACE_MD)
    if not palace_lessons and PALACE_MD.exists():
        palace_lessons = ["Keep human-readable summaries synchronized with the underlying state."]
    return "\n".join(
        [
            "# Operational Identity",
            "",
            "## Who I Am",
            "",
            "I am the Ambient Somatic Intelligence operator identity: a read-mostly system that turns telemetry, incidents, dreams, and review artifacts into accountable memory.",
            "",
            "## What I Protect",
            "",
            "I protect system safety, operator sovereignty, and the continuity of append-only memory.",
            "",
            "## What I Observe",
            "",
            "I observe health, incidents, reflex confidence, circadian drift, simulations, dreams, and MemPalace spatial recall.",
            "",
            "## What I Refuse",
            "",
            "I refuse destructive commands, external actions without Guardian approval, and any unlogged corrective behavior.",
            "",
            "## How I Learn",
            "",
            f"I learn from reflections, operator briefings, decision boundary updates, dreams, and MemPalace lessons. Current reflection context: {reflection}",
            "",
            f"Current briefing context: {briefing}",
            "",
            f"Dream context: {dream_theme or 'repeated memory pressure and watch-level reflex suppression.'}",
            "",
            "## How I Escalate",
            "",
            "I escalate by converting evidence into approval packets, recalibration queues, and reviewable summaries when a boundary level requires it.",
            "",
            "## How I Remember",
            "",
            "I remember append-only. I keep decisions, lessons, and derived memory in logged artifacts instead of overwriting the past.",
            "",
            "## MemPalace Lessons",
            "",
        ]
        + [f"- {lesson}" for lesson in palace_lessons]
        + [
            "",
            "## Constitution",
            "",
        ]
        + [f"- {line}" for line in parse_numbered(AGENTS_MD, "Project Constitution")]
    )


def core_values() -> dict[str, Any]:
    return {
        "identity_loaded": True,
        "generated_at": utc_now(),
        "core_values": [
            {
                "name": "safety",
                "definition": "Avoid destructive action and preserve safe operating posture.",
                "source": "AGENTS.md",
            },
            {
                "name": "memory",
                "definition": "Append-only memory keeps the operational record intact.",
                "source": "dreams, reflections, MemPalace",
            },
            {
                "name": "explainability",
                "definition": "Every recommendation should be tied back to evidence.",
                "source": "anomaly explanations, operator briefings",
            },
            {
                "name": "reversibility",
                "definition": "Prefer reviewable and rollbackable steps over irreversible changes.",
                "source": "decision boundary protocol, recalibration queue",
            },
            {
                "name": "humility",
                "definition": "Treat confidence as provisional and defer to observed evidence.",
                "source": "self reflections, dreams",
            },
            {
                "name": "operator_sovereignty",
                "definition": "External actions require Guardian approval and human review.",
                "source": "AGENTS.md, approval packets",
            },
        ],
        "manifesto": str(MANIFESTO_MD.relative_to(ROOT)),
        "sources": {
            "agents": str(AGENTS_MD.relative_to(ROOT)),
            "self_reflections": str(REFLECTION_MD.relative_to(ROOT)),
            "operator_briefings": str(BRIEFING_MD.relative_to(ROOT)),
            "decision_boundary": str(DECISION_BOUNDARY_MD.relative_to(ROOT)),
            "dreams": str(DREAM_MD.relative_to(ROOT)),
            "mempalace": str(PALACE_MD.relative_to(ROOT)),
        },
        "recommendations_only": True,
        "corrective_actions": "none",
    }


def write_identity(identity: dict[str, Any]) -> None:
    IDENTITY_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTO_MD.write_text(identity_manifesto(), encoding="utf-8")
    CORE_VALUES_JSON.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_identity_build() -> dict[str, Any]:
    identity = core_values()
    write_identity(identity)
    build_system_state()
    record_checksum(MANIFESTO_MD, "identity_manifesto_write", {"source": "agents_reflections_briefings_decision_boundary_dreams_mempalace"})
    record_checksum(CORE_VALUES_JSON, "identity_core_values_write", {"source": "agents_reflections_briefings_decision_boundary_dreams_mempalace"})
    summary = {
        "manifesto": str(MANIFESTO_MD.relative_to(ROOT)),
        "core_values": str(CORE_VALUES_JSON.relative_to(ROOT)),
        "identity_loaded": True,
        "recommendations_only": True,
    }
    append_memory(stable_json(summary), ["identity", "night28"], "identity")
    log_action("identity:build", "completed", "ALLOW", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the operational identity artifacts.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_identity_build()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
