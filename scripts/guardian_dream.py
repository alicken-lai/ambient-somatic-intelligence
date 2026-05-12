#!/usr/bin/env python3
"""Replay recent incidents offline and generate alternative interpretations."""

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
STATE_JSON = ROOT / "state" / "system_state.json"
INCIDENT_INDEX = ROOT / "guardian" / "incidents" / "index.json"
EXPLANATION_MD = ROOT / "guardian" / "explanations" / "latest_anomaly.md"
SIMULATION_MD = ROOT / "guardian" / "simulations" / "latest_simulation.md"
SIMULATION_JSON = ROOT / "guardian" / "simulations" / "latest_simulation.json"
REFLECTION_MD = ROOT / "docs" / "reflections" / "latest.md"
BRIEFING_MD = ROOT / "docs" / "briefings" / "latest_operator_briefing.md"
DREAM_DIR = ROOT / "guardian" / "dreams"
LATEST_DREAM_MD = DREAM_DIR / "latest_dream.md"
LATEST_DREAM_JSON = DREAM_DIR / "latest_dream.json"


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
        if in_section and line.strip():
            collected.append(line.strip())
    return " ".join(collected).strip()


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


def recent_incidents(index: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    incidents = sorted(index.get("incidents", []), key=lambda item: str(item.get("timestamp", "")))
    return incidents[-limit:]


def incident_what_happened(incident: dict[str, Any]) -> str:
    anomalies = incident.get("anomalies", [])
    if not anomalies:
        return "No anomaly records were attached."
    parts = []
    for anomaly in anomalies:
        parts.append(
            f"{anomaly.get('rule', 'unknown')}={anomaly.get('value', 'unknown')} "
            f"({anomaly.get('severity', 'unknown')})"
        )
    return "; ".join(parts)


def incident_prediction(state: dict[str, Any], simulation: dict[str, Any], anomaly: dict[str, str]) -> str:
    predicted = simulation.get("predicted_risk", {})
    if str(anomaly.get("rule", "")).startswith("high_memory_usage"):
        return (
            f"Current simulation predicts {predicted.get('level', 'watch')} risk with "
            f"{predicted.get('confidence', 0.0)} confidence; memory pressure was already the primary driver."
        )
    return "Latest anomaly explanation framed this as a watch-level deviation with no corrective action."


def actual_outcome(incident: dict[str, Any]) -> str:
    anomalies = incident.get("anomalies", [])
    if not anomalies:
        return "No recorded anomaly outcome."
    first = anomalies[0]
    return f"Observed {first.get('rule', 'unknown')} at {first.get('value', 'unknown')} with severity {first.get('severity', 'unknown')}."


def alternative_interpretation(incident: dict[str, Any], anomaly: dict[str, str]) -> str:
    first = (incident.get("anomalies") or [{}])[0]
    if first.get("scoring_artifact") or first.get("true_anomaly") is False:
        return "This may be a scoring artifact amplified by memory-scoring logic rather than a structural fault."
    if str(anomaly.get("rule", "")).startswith("high_memory_usage"):
        return "This may reflect workload-driven memory pressure that the time-aware baseline only partly explains."
    return "The replay does not show a strong alternative beyond the observed deviation."


def false_positive_signal(incident: dict[str, Any]) -> str:
    first = (incident.get("anomalies") or [{}])[0]
    if first.get("true_anomaly") is False or first.get("scoring_artifact"):
        return "likely"
    return "possible"


def missed_warning(incident: dict[str, Any], position: int, total: int) -> str:
    if position < total - 1:
        return "The repeated pattern should have raised the next memory warning sooner."
    return "The earlier incident established the pattern; repeat escalation remains the key missed warning."


def recalibration_suggestion(incident: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    first = (incident.get("anomalies") or [{}])[0]
    value = first.get("value")
    suggestion = "Keep reflex confidence conservative, but escalate repeated memory warnings to review."
    if first.get("true_anomaly") is False or first.get("scoring_artifact"):
        suggestion = "Lower confidence for this rule family and treat the warning as artifact-prone."
    return {
        "incident": incident.get("incident"),
        "rule": first.get("rule"),
        "value": value,
        "current_confidence": state.get("latest_reflex_confidence"),
        "suggested_confidence": 0.2 if first.get("true_anomaly") is False or first.get("scoring_artifact") else 0.15,
        "suggestion": suggestion,
    }


def build_dream() -> dict[str, Any]:
    state = load_json(STATE_JSON)
    if not state:
        raise RuntimeError("state/system_state.json is missing; run system-state-build first")
    incidents = load_json(INCIDENT_INDEX)
    anomaly_meta = parse_markdown_kv(EXPLANATION_MD)
    reflection_meta = parse_markdown_kv(REFLECTION_MD)
    reflection_recent = load_bullets(REFLECTION_MD, "Recent Incidents")
    briefing_meta = parse_markdown_kv(BRIEFING_MD)
    simulation = load_json(SIMULATION_JSON)
    incident_window = recent_incidents(incidents, 5)
    dreams: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for index, incident in enumerate(incident_window):
        first_anomaly = (incident.get("anomalies") or [{}])[0]
        replay = {
            "incident": incident.get("incident"),
            "timestamp": incident.get("timestamp"),
            "what_happened": incident_what_happened(incident),
            "what_was_predicted": incident_prediction(state, simulation, anomaly_meta),
            "what_actually_happened": actual_outcome(incident),
            "alternative_interpretation": alternative_interpretation(incident, anomaly_meta),
            "possible_false_positive": false_positive_signal(incident),
            "possible_missed_warning": missed_warning(incident, index, len(incident_window)),
            "confidence_recalibration_suggestion": recalibration_suggestion(incident, state),
        }
        dreams.append(replay)
        candidates.append(
            {
                "incident": incident.get("incident"),
                "rule": first_anomaly.get("rule"),
                "recalibration_suggestion": replay["confidence_recalibration_suggestion"]["suggestion"],
                "suggested_confidence": replay["confidence_recalibration_suggestion"]["suggested_confidence"],
            }
        )

    dominant_theme = "repeated memory pressure with watch-level reflex suppression" if dreams else "no recent incidents"
    return {
        "generated_at": utc_now(),
        "dream_cycle": {
            "generated_at": utc_now(),
            "incident_window": 5,
            "replayed_incident_count": len(dreams),
            "dominant_theme": dominant_theme,
            "source_context": {
                "self_reflection": str(REFLECTION_MD.relative_to(ROOT)),
                "operator_briefing": str(BRIEFING_MD.relative_to(ROOT)),
                "anomaly_explanation": str(EXPLANATION_MD.relative_to(ROOT)),
                "simulation": str(SIMULATION_MD.relative_to(ROOT)),
            },
        },
        "recalibration_candidates": candidates,
        "replays": dreams,
        "reflection_context": {
            "recent_incidents": reflection_recent,
            "reflection_meta": reflection_meta,
            "briefing_meta": briefing_meta,
        },
        "corrective_actions": "none",
        "recommendations_only": True,
        "sources": {
            "incident_memory": str(INCIDENT_INDEX.relative_to(ROOT)),
            "anomaly_explanations": str(EXPLANATION_MD.relative_to(ROOT)),
            "simulations": str(SIMULATION_JSON.relative_to(ROOT)),
            "self_reflections": str(REFLECTION_MD.relative_to(ROOT)),
            "operator_briefings": str(BRIEFING_MD.relative_to(ROOT)),
        },
    }


def write_dream(dream: dict[str, Any]) -> None:
    DREAM_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Guardian Dream",
        "",
        f"- generated_at: {dream['generated_at']}",
        f"- incident_window: {dream['dream_cycle']['incident_window']}",
        f"- replayed_incident_count: {dream['dream_cycle']['replayed_incident_count']}",
        f"- dominant_theme: {dream['dream_cycle']['dominant_theme']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Replay Window",
        "",
    ]
    for replay in dream["replays"]:
        lines.extend(
            [
                f"### {replay['incident']}",
                "",
                f"- what_happened: {replay['what_happened']}",
                f"- what_was_predicted: {replay['what_was_predicted']}",
                f"- what_actually_happened: {replay['what_actually_happened']}",
                f"- alternative_interpretation: {replay['alternative_interpretation']}",
                f"- possible_false_positive: {replay['possible_false_positive']}",
                f"- possible_missed_warning: {replay['possible_missed_warning']}",
                f"- confidence_recalibration_suggestion: {replay['confidence_recalibration_suggestion']['suggestion']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Recalibration Candidates",
            "",
        ]
    )
    for candidate in dream["recalibration_candidates"]:
        lines.append(f"- {stable_json(candidate)}")
    lines.extend(
        [
            "",
            "## Sources",
            "",
        ]
    )
    for key, value in dream["sources"].items():
        lines.append(f"- {key}: {value}")
    LATEST_DREAM_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    LATEST_DREAM_JSON.write_text(json.dumps(dream, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_dream() -> dict[str, Any]:
    dream = build_dream()
    write_dream(dream)
    build_system_state()
    record_checksum(LATEST_DREAM_MD, "guardian_dream_write", {"source": "incident_memory_and_reflections"})
    record_checksum(LATEST_DREAM_JSON, "guardian_dream_index_write", {"source": "incident_memory_and_reflections"})
    summary = {
        "dream": str(LATEST_DREAM_MD.relative_to(ROOT)),
        "dream_json": str(LATEST_DREAM_JSON.relative_to(ROOT)),
        "dream_cycle": dream["dream_cycle"],
        "recalibration_candidates": dream["recalibration_candidates"],
        "recommendations_only": True,
    }
    append_memory(stable_json(summary), ["guardian", "dream", "night24"], "guardian_dream")
    log_action("dream:build", "completed", "ALLOW", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay recent incidents offline.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_dream()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
