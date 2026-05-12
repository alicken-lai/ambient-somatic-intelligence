#!/usr/bin/env python3
"""Generate a short self-reflection from Ambient OS self-model state."""

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
INCIDENT_INDEX = ROOT / "guardian" / "incidents" / "index.json"
DAILY_DIGEST = ROOT / "dashboard" / "daily_digest.md"
REFLECTION_DIR = ROOT / "docs" / "reflections"
LATEST_REFLECTION = REFLECTION_DIR / "latest.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_digest(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- ([^:]+): (.*)$", line)
        if match:
            values[match.group(1).strip()] = match.group(2).strip()
    return values


def previous_reflection_summary() -> dict[str, str]:
    if not LATEST_REFLECTION.exists():
        return {}
    values: dict[str, str] = {}
    for line in LATEST_REFLECTION.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- ([^:]+): (.*)$", line)
        if match:
            values[match.group(1).strip()] = match.group(2).strip()
    return values


def recent_incidents(index: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    incidents = index.get("incidents", [])
    return sorted(incidents, key=lambda item: str(item.get("timestamp", "")))[-limit:]


def incident_summary(incident: dict[str, Any]) -> str:
    anomalies = incident.get("anomalies", [])
    rules = sorted({str(item.get("rule", "unknown")) for item in anomalies})
    severities = sorted({str(item.get("severity", "unknown")) for item in anomalies})
    timestamp = incident.get("timestamp", "unknown")
    path = incident.get("incident", "unknown")
    return f"{timestamp}: {', '.join(rules) or 'unknown'} ({', '.join(severities) or 'unknown'}) in {path}"


def dominant_risk(state: dict[str, Any], incidents: dict[str, Any]) -> str:
    repeated = state.get("repeated_anomalies", {})
    if repeated:
        top_rule, count = max(repeated.items(), key=lambda item: int(item[1]))
        return f"{top_rule} repeated {count} times"
    baseline = (state.get("baseline_deviation") or {}).get("overall_severity")
    if baseline and baseline != "normal":
        return f"baseline deviation is {baseline}"
    latest = incidents.get("patterns", {}).get("latest_severity")
    if latest:
        return f"latest incident severity is {latest}"
    return "no dominant risk detected"


def confidence_level(state: dict[str, Any]) -> str:
    confidence = float(state.get("latest_reflex_confidence") or 0.0)
    risk_class = state.get("current_risk_class", "unknown")
    if confidence >= 0.75:
        band = "high"
    elif confidence >= 0.4:
        band = "medium"
    else:
        band = "low"
    return f"{band} ({confidence:.2f}, {risk_class})"


def current_condition(state: dict[str, Any], digest: dict[str, str]) -> str:
    health = state.get("health_score")
    trend = state.get("trend")
    memory = state.get("memory_status", {})
    baseline = (state.get("baseline_deviation") or {}).get("overall_severity")
    digest_state = digest.get("state_generated_at", "unknown")
    return (
        f"Health is {health} with {trend} trend; memory risk is {memory.get('true_risk')} "
        f"at {memory.get('used_percent')}% used; baseline deviation is {baseline}. "
        f"Latest digest references state generated {digest_state}."
    )


def changes_since_last(state: dict[str, Any], previous: dict[str, str]) -> str:
    if not previous:
        return "No prior reflection found; this establishes the first reflection baseline."
    checks = [
        ("health_score", str(state.get("health_score"))),
        ("incident_count", str(state.get("incident_count"))),
        ("dmn_append_count", str(state.get("dmn_append_count"))),
        ("risk_class", str(state.get("current_risk_class"))),
        ("dominant_risk", dominant_risk(state, load_json(INCIDENT_INDEX))),
    ]
    changed = [f"{key}: {previous.get(key)} -> {value}" for key, value in checks if previous.get(key) != value]
    return "; ".join(changed) if changed else "No material state change since the last reflection."


def next_observation(state: dict[str, Any]) -> str:
    recommendations = state.get("recommendations", [])
    if recommendations:
        return str(recommendations[0])
    risk = dominant_risk(state, load_json(INCIDENT_INDEX))
    return f"Continue observing {risk}."


def build_reflection() -> dict[str, Any]:
    state = load_json(STATE_JSON)
    if not state:
        raise RuntimeError("state/system_state.json is missing; run system-state-build first")
    incidents = load_json(INCIDENT_INDEX)
    digest = parse_digest(DAILY_DIGEST)
    previous = previous_reflection_summary()
    recent = recent_incidents(incidents)
    risk = dominant_risk(state, incidents)
    return {
        "generated_at": utc_now(),
        "state_generated_at": state.get("generated_at"),
        "digest_generated_at": digest.get("generated_at"),
        "health_score": state.get("health_score"),
        "incident_count": state.get("incident_count"),
        "dmn_append_count": state.get("dmn_append_count"),
        "risk_class": state.get("current_risk_class"),
        "current_condition": current_condition(state, digest),
        "dominant_risk": risk,
        "confidence_level": confidence_level(state),
        "what_changed_since_last_reflection": changes_since_last(state, previous),
        "recommended_next_observation": next_observation(state),
        "recent_incidents": [incident_summary(item) for item in recent],
        "corrective_actions": "none",
        "recommendations_only": True,
        "sources": {
            "system_state": str(STATE_JSON.relative_to(ROOT)),
            "incident_index": str(INCIDENT_INDEX.relative_to(ROOT)),
            "daily_digest": str(DAILY_DIGEST.relative_to(ROOT)),
        },
    }


def write_reflection(reflection: dict[str, Any]) -> None:
    REFLECTION_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Self-Reflection",
        "",
        f"- generated_at: {reflection['generated_at']}",
        f"- state_generated_at: {reflection['state_generated_at']}",
        f"- digest_generated_at: {reflection['digest_generated_at']}",
        f"- health_score: {reflection['health_score']}",
        f"- incident_count: {reflection['incident_count']}",
        f"- dmn_append_count: {reflection['dmn_append_count']}",
        f"- risk_class: {reflection['risk_class']}",
        f"- dominant_risk: {reflection['dominant_risk']}",
        f"- confidence_level: {reflection['confidence_level']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Current Condition",
        "",
        reflection["current_condition"],
        "",
        "## What Changed",
        "",
        reflection["what_changed_since_last_reflection"],
        "",
        "## Recommended Next Observation",
        "",
        reflection["recommended_next_observation"],
        "",
        "## Recent Incidents",
        "",
    ]
    for incident in reflection["recent_incidents"]:
        lines.append(f"- {incident}")
    lines.extend(
        [
            "",
            "## Sources",
            "",
        ]
    )
    for key, value in reflection["sources"].items():
        lines.append(f"- {key}: {value}")
    LATEST_REFLECTION.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_reflection() -> dict[str, Any]:
    reflection = build_reflection()
    write_reflection(reflection)
    record_checksum(LATEST_REFLECTION, "self_reflection_write", {"source": "system_state_and_incidents"})
    memory = {
        "reflection": str(LATEST_REFLECTION.relative_to(ROOT)),
        "current_condition": reflection["current_condition"],
        "dominant_risk": reflection["dominant_risk"],
        "confidence_level": reflection["confidence_level"],
        "recommended_next_observation": reflection["recommended_next_observation"],
        "recommendations_only": True,
    }
    append_memory(stable_json(memory), ["self-model", "reflection", "night17"], "self_reflection")
    log_action("self-reflection:generate", "completed", "ALLOW", memory)
    return memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Ambient OS self-reflection.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_reflection()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
