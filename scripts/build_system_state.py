#!/usr/bin/env python3
"""Build the Ambient OS single source of truth state file."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "state"
STATE_JSON = STATE_DIR / "system_state.json"
REPORT_MD = ROOT / "guardian" / "audits" / "ssot_report.md"
DMN_FILE = ROOT / "memory" / "dmn.jsonl"
HEALTH_JSON = ROOT / "guardian" / "health" / "health_scores.json"
INCIDENT_INDEX = ROOT / "guardian" / "incidents" / "index.json"
CALIBRATION_JSON = ROOT / "guardian" / "incidents" / "reflex_confidence_calibration.json"
BASELINE_JSON = ROOT / "guardian" / "baselines" / "telemetry_baseline.json"
MEMORY_PRESSURE_JSON = ROOT / "guardian" / "health" / "memory_pressure_report.json"
TELEMETRY_DIR = ROOT / "observability" / "snapshots"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def dmn_append_count() -> int:
    if not DMN_FILE.exists():
        return 0
    with DMN_FILE.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def latest_telemetry_snapshot() -> str:
    snapshots = sorted(TELEMETRY_DIR.glob("telemetry-*.json"))
    if not snapshots:
        return "unknown"
    return str(snapshots[-1].relative_to(ROOT))


def risk_label(score: float) -> str:
    if score >= 80:
        return "steady"
    if score >= 60:
        return "watch"
    if score >= 40:
        return "review"
    return "incident"


def class_from_confidence(confidence_class: str) -> str:
    if confidence_class == "high_confidence_incident":
        return "incident"
    if confidence_class == "medium_confidence_review":
        return "review"
    return "watch"


def recommendations(calibration: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    values = {
        item.get("recommendation", "")
        for item in calibration.get("anomalies", [])
        if item.get("recommendation")
    }
    values.update(item for item in baseline.get("recommendations", []) if item)
    return sorted(values) or ["No corrective action recommended; continue observation."]


def authoritative_sources() -> dict[str, dict[str, str]]:
    return {
        "dmn_append_count": {
            "path": str(DMN_FILE.relative_to(ROOT)),
            "method": "count non-empty JSONL records",
        },
        "health_score": {
            "path": str(HEALTH_JSON.relative_to(ROOT)),
            "field": "/current/health_score",
        },
        "incident_count": {
            "path": str(INCIDENT_INDEX.relative_to(ROOT)),
            "field": "/incident_count",
        },
        "repeated_anomalies": {
            "path": str(INCIDENT_INDEX.relative_to(ROOT)),
            "field": "/patterns/repeated_anomaly_types",
        },
        "reflex_confidence": {
            "path": str(CALIBRATION_JSON.relative_to(ROOT)),
            "field": "/anomalies/-1/confidence",
        },
        "baseline_deviation": {
            "path": str(BASELINE_JSON.relative_to(ROOT)),
            "field": "/overall_deviation_severity and /metrics/*/deviation",
        },
    }


def source_values() -> dict[str, Any]:
    health = load_json(HEALTH_JSON)
    incidents = load_json(INCIDENT_INDEX)
    calibration = load_json(CALIBRATION_JSON)
    baseline = load_json(BASELINE_JSON)
    memory_pressure = load_json(MEMORY_PRESSURE_JSON)

    current = health.get("current", {})
    subsystems = current.get("subsystems", {})
    latest_anomaly = (calibration.get("anomalies") or [{}])[-1]
    confidence = float(latest_anomaly.get("confidence") or 0.0)
    confidence_class = str(latest_anomaly.get("confidence_class") or "low_confidence_watch")
    repeated = incidents.get("patterns", {}).get("repeated_anomaly_types", {})
    docker_context = calibration.get("context", {})
    memory_fields = memory_pressure.get("memory_fields", {})
    memory_risk = memory_pressure.get("risk_assessment", {})
    health_score = float(current.get("health_score") or 0.0)

    return {
        "dmn_append_count": dmn_append_count(),
        "health_score": health_score,
        "health_risk": risk_label(health_score),
        "trend": health.get("trend", "unknown"),
        "subsystems": {
            name: {
                "score": data.get("score"),
                "raw_score": data.get("raw_score"),
                "incident_penalty": data.get("incident_penalty"),
            }
            for name, data in sorted(subsystems.items())
        },
        "incident_count": int(incidents.get("incident_count") or 0),
        "repeated_anomalies": repeated,
        "repeated_anomaly_count": sum(int(value) for value in repeated.values()),
        "latest_reflex_confidence": confidence,
        "current_risk_class": confidence_class,
        "display_risk": class_from_confidence(confidence_class),
        "baseline_deviation": {
            "overall_severity": baseline.get("overall_deviation_severity", "unknown"),
            "current_timestamp": baseline.get("current_timestamp"),
            "metrics": {
                name: {
                    "current": data.get("current"),
                    "severity": data.get("deviation", {}).get("severity"),
                    "z_score": data.get("deviation", {}).get("z_score"),
                    "delta_from_mean": data.get("deviation", {}).get("delta_from_mean"),
                }
                for name, data in sorted(baseline.get("metrics", {}).items())
            },
        },
        "latest_telemetry_snapshot": latest_telemetry_snapshot(),
        "docker_context": {
            "vm": docker_context.get("docker_vm", {}),
            "containers": docker_context.get("docker_stats", []),
        },
        "memory_status": {
            "used_percent": memory_fields.get("used_percent"),
            "free_bytes": memory_fields.get("free_bytes"),
            "true_risk": memory_risk.get("true_risk"),
            "scoring_artifact": memory_risk.get("scoring_artifact"),
            "swap": (memory_pressure.get("swap") or {}).get("raw") or (docker_context.get("swap") or {}).get("raw"),
        },
        "recommendations": recommendations(calibration, baseline),
    }


def stale_state_detection(state: dict[str, Any]) -> dict[str, Any]:
    expected = source_values()
    mismatches = []
    for key, value in expected.items():
        if state.get(key) != value:
            mismatches.append({"field": key, "state": state.get(key), "source": value})

    newer_sources = []
    if STATE_JSON.exists():
        state_mtime = STATE_JSON.stat().st_mtime
        for path in [DMN_FILE, HEALTH_JSON, INCIDENT_INDEX, CALIBRATION_JSON, BASELINE_JSON, MEMORY_PRESSURE_JSON]:
            if path.exists() and path.stat().st_mtime > state_mtime:
                newer_sources.append(str(path.relative_to(ROOT)))

    return {
        "status": "ok" if not mismatches and not newer_sources else "warning",
        "mismatches": mismatches,
        "newer_sources": newer_sources,
    }


def build_state() -> dict[str, Any]:
    state = {
        "generated_at": utc_now(),
        "state_version": 1,
        "corrective_actions": "none",
        "recommendations_only": True,
        "authoritative_sources": authoritative_sources(),
        **source_values(),
    }
    state["validation"] = {"stale_state_detection": stale_state_detection(state)}
    return state


def write_report(state: dict[str, Any]) -> None:
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    validation = state["validation"]["stale_state_detection"]
    lines = [
        "# Single Source of Truth Report",
        "",
        f"- generated_at: {state['generated_at']}",
        f"- state_file: {STATE_JSON.relative_to(ROOT)}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        f"- stale_state_detection: {validation['status']}",
        "",
        "## Authoritative Sources",
        "",
        "| Value | Source | Field / Method |",
        "| --- | --- | --- |",
    ]
    for key, source in state["authoritative_sources"].items():
        method = source.get("field") or source.get("method") or ""
        lines.append(f"| {key} | {source['path']} | {method} |")

    lines.extend(
        [
            "",
            "## Current Values",
            "",
            f"- dmn_append_count: {state['dmn_append_count']}",
            f"- health_score: {state['health_score']}",
            f"- incident_count: {state['incident_count']}",
            f"- repeated_anomaly_count: {state['repeated_anomaly_count']}",
            f"- repeated_anomalies: {stable_json(state['repeated_anomalies']) if state['repeated_anomalies'] else 'none'}",
            f"- reflex_confidence: {state['latest_reflex_confidence']}",
            f"- risk_class: {state['current_risk_class']}",
            f"- baseline_deviation: {state['baseline_deviation']['overall_severity']}",
            "",
            "## Validation",
            "",
            f"- stale_state_detection.status: {validation['status']}",
            f"- stale_state_detection.mismatches: {json.dumps(validation['mismatches'], sort_keys=True) if validation['mismatches'] else 'none'}",
            f"- stale_state_detection.newer_sources: {json.dumps(validation['newer_sources'], sort_keys=True) if validation['newer_sources'] else 'none'}",
            "",
            "## Recommendations",
            "",
            "- Rebuild `state/system_state.json` before regenerating dashboard or daily digest metadata.",
            "- Keep dashboard and digest builders read-only against source artifacts; they should render state, not recompute it.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_system_state() -> dict[str, Any]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state = build_state()
    STATE_JSON.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    state["validation"] = {"stale_state_detection": stale_state_detection(state)}
    STATE_JSON.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(state)
    record_checksum(STATE_JSON, "system_state_build", {"source": "authoritative_local_artifacts"})
    record_checksum(REPORT_MD, "ssot_report_build", {"source": str(STATE_JSON.relative_to(ROOT))})
    memory = {
        "system_state": str(STATE_JSON.relative_to(ROOT)),
        "report": str(REPORT_MD.relative_to(ROOT)),
        "stale_state_detection": state["validation"]["stale_state_detection"]["status"],
        "dmn_append_count": state["dmn_append_count"],
        "health_score": state["health_score"],
        "incident_count": state["incident_count"],
        "recommendations_only": True,
    }
    log_action("state:system-state-build", "completed", "ALLOW", memory)
    return memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Ambient OS system_state.json.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(build_system_state()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
