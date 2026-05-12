#!/usr/bin/env python3
"""Build a structured human-approval packet for a review-bound action."""

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
BRIEFING_MD = ROOT / "docs" / "briefings" / "latest_operator_briefing.md"
EXPLANATION_MD = ROOT / "guardian" / "explanations" / "latest_anomaly.md"
BOUNDARY_YAML = ROOT / "guardian" / "decision_boundary.yaml"
PACKET_DIR = ROOT / "guardian" / "approval_packets"
LATEST_PACKET = PACKET_DIR / "latest_approval_packet.md"
PACKET_INDEX = PACKET_DIR / "latest_approval_packet.json"


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


def load_boundary_map() -> dict[str, str]:
    if not BOUNDARY_YAML.exists():
        return {}
    routes: dict[str, str] = {}
    in_routes = False
    for raw_line in BOUNDARY_YAML.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped == "routes:":
            in_routes = True
            continue
        if in_routes and raw_line.startswith("  ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            routes[key.strip()] = value.strip()
    return routes


def build_packet() -> dict[str, Any]:
    state = load_json(STATE_JSON)
    if not state:
        raise RuntimeError("state/system_state.json is missing; run system-state-build first")
    briefing = parse_markdown_kv(BRIEFING_MD)
    explanation = parse_markdown_kv(EXPLANATION_MD)
    boundary_map = load_boundary_map()
    proposed_action = "guardian-reflex-once"
    boundary_level = boundary_map.get(proposed_action, "PREPARE_FOR_APPROVAL")
    reason = section_text(BRIEFING_MD, "Executive Summary") or "The current state remains watch-level with low reflex confidence."
    evidence = [
        f"health_score={state.get('health_score')} ({state.get('health_risk')})",
        f"trend={state.get('trend')}",
        f"incident_count={state.get('incident_count')}",
        f"circadian_deviation={state.get('circadian_deviation', {}).get('overall_severity')}",
        f"reflex_confidence={state.get('latest_reflex_confidence')}",
        f"briefing={BRIEFING_MD.relative_to(ROOT)}",
        f"explanation={EXPLANATION_MD.relative_to(ROOT)}",
    ]
    expected_impact = (
        "Prepare a guarded reflex pass that refreshes incident-aware context without executing corrective changes."
    )
    rollback_plan = (
        "Discard the packet, keep the current no-corrective-action posture, and rebuild the packet after the next state refresh."
    )
    checklist = [
        "Confirm the proposed action matches the current boundary level.",
        "Confirm the evidence references the latest operator briefing and anomaly explanation.",
        "Confirm the packet does not authorize execution.",
        "Confirm the rollback plan preserves no-corrective-action posture.",
    ]
    return {
        "generated_at": utc_now(),
        "proposed_action": proposed_action,
        "decision_boundary_level": boundary_level,
        "risk_class": state.get("current_risk_class"),
        "reason": reason,
        "evidence": evidence,
        "expected_impact": expected_impact,
        "rollback_plan": rollback_plan,
        "approval_checklist": checklist,
        "corrective_actions": "none",
        "recommendations_only": True,
        "source_summary": {
            "system_state": str(STATE_JSON.relative_to(ROOT)),
            "operator_briefing": str(BRIEFING_MD.relative_to(ROOT)),
            "anomaly_explanation": str(EXPLANATION_MD.relative_to(ROOT)),
            "decision_boundary": str(BOUNDARY_YAML.relative_to(ROOT)),
        },
        "briefing_context": briefing,
        "explanation_context": explanation,
    }


def write_packet(packet: dict[str, Any]) -> None:
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Approval Packet",
        "",
        f"- generated_at: {packet['generated_at']}",
        f"- proposed_action: {packet['proposed_action']}",
        f"- decision_boundary_level: {packet['decision_boundary_level']}",
        f"- risk_class: {packet['risk_class']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Proposed Action",
        "",
        packet["proposed_action"],
        "",
        "## Reason",
        "",
        packet["reason"],
        "",
        "## Evidence",
        "",
    ]
    for item in packet["evidence"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Expected Impact",
            "",
            packet["expected_impact"],
            "",
            "## Rollback Plan",
            "",
            packet["rollback_plan"],
            "",
            "## Approval Checklist",
            "",
        ]
    )
    for item in packet["approval_checklist"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Sources",
            "",
        ]
    )
    for key, value in packet["source_summary"].items():
        lines.append(f"- {key}: {value}")
    LATEST_PACKET.write_text("\n".join(lines) + "\n", encoding="utf-8")
    PACKET_INDEX.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_packet_build() -> dict[str, Any]:
    packet = build_packet()
    write_packet(packet)
    record_checksum(LATEST_PACKET, "approval_packet_write", {"proposed_action": packet["proposed_action"]})
    record_checksum(PACKET_INDEX, "approval_packet_index_write", {"proposed_action": packet["proposed_action"]})
    summary = {
        "approval_packet": str(LATEST_PACKET.relative_to(ROOT)),
        "proposed_action": packet["proposed_action"],
        "decision_boundary_level": packet["decision_boundary_level"],
        "risk_class": packet["risk_class"],
        "recommendations_only": True,
    }
    append_memory(stable_json(summary), ["guardian", "approval-packet", "night22"], "approval_packet")
    log_action("approval:packet-build", "completed", "ALLOW", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a human-approval packet.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_packet_build()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
