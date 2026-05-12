#!/usr/bin/env python3
"""Generate a concise operator briefing from Ambient OS self-model artifacts."""

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
STATE_JSON = ROOT / "state" / "system_state.json"
REFLECTION_MD = ROOT / "docs" / "reflections" / "latest.md"
EXPLANATION_MD = ROOT / "guardian" / "explanations" / "latest_anomaly.md"
DIGEST_MD = ROOT / "dashboard" / "daily_digest.md"
BRIEFING_DIR = ROOT / "docs" / "briefings"
LATEST_BRIEFING = BRIEFING_DIR / "latest_operator_briefing.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_markdown_kv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- ([^:]+): (.*)$", line)
        if match:
            values[match.group(1).strip()] = match.group(2).strip()
    return values


def load_bullets(path: Path, heading: str) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    bullets: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith("## "):
            in_section = line[3:].strip() == heading
            continue
        if in_section and line.startswith("- "):
            bullets.append(line[2:].strip())
    return bullets


def section_text(path: Path, heading: str) -> str:
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
        if in_section:
            if line.strip():
                collected.append(line.strip())
    return " ".join(collected).strip()


def latest_explanation(state: dict[str, Any]) -> dict[str, Any]:
    explanation = parse_markdown_kv(EXPLANATION_MD)
    warnings = load_bullets(EXPLANATION_MD, "Metric Warnings")
    reflex = load_bullets(EXPLANATION_MD, "Reflex Signal")
    return {
        "summary": explanation,
        "warnings": warnings,
        "reflex": reflex,
    }


def daily_digest_summary() -> dict[str, str]:
    return parse_markdown_kv(DIGEST_MD)


def build_briefing() -> dict[str, Any]:
    state = load_json(STATE_JSON)
    if not state:
        raise RuntimeError("state/system_state.json is missing; run system-state-build first")
    reflection_meta = parse_markdown_kv(REFLECTION_MD)
    reflection_current = section_text(REFLECTION_MD, "Current Condition")
    reflection_changes = section_text(REFLECTION_MD, "What Changed")
    reflection_observation = section_text(REFLECTION_MD, "Recommended Next Observation")
    reflection_recent = load_bullets(REFLECTION_MD, "Recent Incidents")
    explanation = latest_explanation(state)
    digest = daily_digest_summary()
    blocked_actions = [
        "No destructive shell commands.",
        "No external actions without Guardian approval.",
        "No corrective changes; this briefing is read-only.",
    ]
    active_risks = []
    if state.get("circadian_deviation", {}).get("overall_severity") in {"warning", "critical"}:
        active_risks.append(f"circadian deviation is {state['circadian_deviation']['overall_severity']}")
    if state.get("baseline_deviation", {}).get("overall_severity") in {"warning", "critical"}:
        active_risks.append(f"flat baseline deviation is {state['baseline_deviation']['overall_severity']}")
    if state.get("current_risk_class"):
        active_risks.append(f"reflex class is {state['current_risk_class']}")
    if state.get("repeated_anomalies"):
        active_risks.append(
            f"dominant incident memory is {state.get('repeated_anomalies', {}).get('high_memory_usage', 0)} repeated high_memory_usage events"
        )
    return {
        "generated_at": utc_now(),
        "state_generated_at": state.get("generated_at"),
        "executive_summary": (
            f"Health remains {state.get('health_score')} with stable trend. "
            f"Memory pressure is the dominant learned risk, and circadian context now downgrades reflex confidence to {state.get('latest_reflex_confidence')}."
        ),
        "current_health": {
            "health_score": state.get("health_score"),
            "health_risk": state.get("health_risk"),
            "trend": state.get("trend"),
            "incident_count": state.get("incident_count"),
            "dmn_append_count": state.get("dmn_append_count"),
            "baseline_deviation": state.get("baseline_deviation", {}).get("overall_severity"),
            "circadian_deviation": state.get("circadian_deviation", {}).get("overall_severity"),
        },
        "active_risks": active_risks or ["No active warning-level risk detected."],
        "confidence_assessment": {
            "base_reflex_confidence": state.get("base_reflex_confidence"),
            "time_adjusted_reflex_confidence": state.get("latest_reflex_confidence"),
            "confidence_level": reflection_meta.get("confidence_level", "unknown"),
            "reflex_explanation": explanation["reflex"][0] if explanation["reflex"] else "No reflex explanation available.",
        },
        "what_changed": reflection_changes or reflection_meta.get("what_changed_since_last_reflection", "unknown"),
        "recommended_observation": reflection_observation or "Continue observing current telemetry.",
        "reflection_current_condition": reflection_current,
        "reflection_recent_incidents": reflection_recent,
        "blocked_actions_reminder": blocked_actions,
        "source_summary": {
            "system_state": str(STATE_JSON.relative_to(ROOT)),
            "self_reflection": str(REFLECTION_MD.relative_to(ROOT)),
            "anomaly_explanation": str(EXPLANATION_MD.relative_to(ROOT)),
            "daily_digest": str(DIGEST_MD.relative_to(ROOT)),
        },
    }


def write_briefing(briefing: dict[str, Any]) -> None:
    BRIEFING_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Operator Briefing",
        "",
        f"- generated_at: {briefing['generated_at']}",
        f"- state_generated_at: {briefing['state_generated_at']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Executive Summary",
        "",
        briefing["executive_summary"],
        "",
        "## Current Health",
        "",
        f"- health_score: {briefing['current_health']['health_score']}",
        f"- health_risk: {briefing['current_health']['health_risk']}",
        f"- trend: {briefing['current_health']['trend']}",
        f"- incident_count: {briefing['current_health']['incident_count']}",
        f"- dmn_append_count: {briefing['current_health']['dmn_append_count']}",
        f"- baseline_deviation: {briefing['current_health']['baseline_deviation']}",
        f"- circadian_deviation: {briefing['current_health']['circadian_deviation']}",
        "",
        "## Active Risks",
        "",
    ]
    for item in briefing["active_risks"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Confidence Assessment",
            "",
            f"- base_reflex_confidence: {briefing['confidence_assessment']['base_reflex_confidence']}",
            f"- time_adjusted_reflex_confidence: {briefing['confidence_assessment']['time_adjusted_reflex_confidence']}",
            f"- confidence_level: {briefing['confidence_assessment']['confidence_level']}",
            f"- reflex_explanation: {briefing['confidence_assessment']['reflex_explanation']}",
            "",
            "## What Changed",
            "",
            briefing["what_changed"],
            "",
            "## Reflection Context",
            "",
            briefing["reflection_current_condition"],
            "",
            "## Recent Incidents",
            "",
        ]
    )
    for item in briefing["reflection_recent_incidents"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Recommended Observation",
            "",
            briefing["recommended_observation"],
            "",
            "## Blocked Actions Reminder",
            "",
        ]
    )
    for item in briefing["blocked_actions_reminder"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Sources",
            "",
        ]
    )
    for key, value in briefing["source_summary"].items():
        lines.append(f"- {key}: {value}")
    LATEST_BRIEFING.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_briefing() -> dict[str, Any]:
    briefing = build_briefing()
    write_briefing(briefing)
    record_checksum(LATEST_BRIEFING, "operator_briefing_write", {"source": "system_state_reflection_explanation_digest"})
    summary = {
        "briefing": str(LATEST_BRIEFING.relative_to(ROOT)),
        "health_score": briefing["current_health"]["health_score"],
        "active_risks": briefing["active_risks"],
        "time_adjusted_reflex_confidence": briefing["confidence_assessment"]["time_adjusted_reflex_confidence"],
        "recommended_observation": briefing["recommended_observation"],
        "recommendations_only": True,
    }
    append_memory(stable_json(summary), ["operator", "briefing", "night20"], "operator_briefing")
    log_action("operator:briefing", "completed", "ALLOW", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an operator briefing.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_briefing()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
