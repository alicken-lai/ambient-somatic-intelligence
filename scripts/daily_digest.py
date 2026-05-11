#!/usr/bin/env python3
"""Generate a local Somatic Dashboard daily digest."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = ROOT / "dashboard"
DIGEST_MD = DASHBOARD_DIR / "daily_digest.md"
HEALTH_JSON = ROOT / "guardian" / "health" / "health_scores.json"
CALIBRATION_JSON = ROOT / "guardian" / "incidents" / "reflex_confidence_calibration.json"
INCIDENT_INDEX = ROOT / "guardian" / "incidents" / "index.json"
DMN_FILE = ROOT / "memory" / "dmn.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def dmn_append_count_after_digest() -> int:
    if not DMN_FILE.exists():
        return 1
    with DMN_FILE.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip()) + 1


def build_digest_model() -> dict[str, Any]:
    health = load_json(HEALTH_JSON)
    calibration = load_json(CALIBRATION_JSON)
    incident_index = load_json(INCIDENT_INDEX)
    current = health.get("current", {})
    anomaly = (calibration.get("anomalies") or [{}])[-1]
    patterns = incident_index.get("patterns", {})
    repeated = patterns.get("repeated_anomaly_types", {})
    recommendations = sorted({
        item.get("recommendation", "")
        for item in calibration.get("anomalies", [])
        if item.get("recommendation")
    }) or ["No corrective action recommended; continue observation."]
    return {
        "generated_at": utc_now(),
        "health_score": current.get("health_score"),
        "trend": health.get("trend", "unknown"),
        "reflex_confidence": anomaly.get("confidence"),
        "risk_class": anomaly.get("confidence_class"),
        "incident_count": incident_index.get("incident_count", 0),
        "repeated_anomaly_count": sum(int(value) for value in repeated.values()),
        "repeated_anomalies": repeated,
        "dmn_append_count": dmn_append_count_after_digest(),
        "recommendations": recommendations,
        "recommendations_only": True,
        "corrective_actions": "none",
    }


def write_digest(model: dict[str, Any]) -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    repeated = ", ".join(f"{key}: {value}" for key, value in model["repeated_anomalies"].items()) or "none"
    lines = [
        "# Somatic Daily Digest",
        "",
        f"- generated_at: {model['generated_at']}",
        f"- health_score: {model['health_score']}",
        f"- trend: {model['trend']}",
        f"- reflex_confidence: {model['reflex_confidence']}",
        f"- risk_class: {model['risk_class']}",
        f"- incident_count: {model['incident_count']}",
        f"- repeated_anomaly_count: {model['repeated_anomaly_count']}",
        f"- repeated_anomalies: {repeated}",
        f"- dmn_append_count: {model['dmn_append_count']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Recommendations",
        "",
    ]
    for recommendation in model["recommendations"]:
        lines.append(f"- {recommendation}")
    DIGEST_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_digest() -> dict[str, Any]:
    model = build_digest_model()
    write_digest(model)
    record_checksum(DIGEST_MD, "somatic_daily_digest_build", {"source": "local_artifacts"})
    memory = {
        "daily_digest": str(DIGEST_MD.relative_to(ROOT)),
        "health_score": model["health_score"],
        "trend": model["trend"],
        "reflex_confidence": model["reflex_confidence"],
        "risk_class": model["risk_class"],
        "incident_count": model["incident_count"],
        "repeated_anomaly_count": model["repeated_anomaly_count"],
        "dmn_append_count": model["dmn_append_count"],
        "recommendations_only": True,
        "external_notifications": "none",
    }
    append_memory(stable_json(memory), ["dashboard", "daily-digest", "night13"], "daily_digest")
    log_action("dashboard:daily-digest", "completed", "ALLOW", memory)
    return memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate local Somatic Daily Digest.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(generate_digest()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
