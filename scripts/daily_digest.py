#!/usr/bin/env python3
"""Generate a local Somatic Dashboard daily digest."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = ROOT / "dashboard"
DIGEST_MD = DASHBOARD_DIR / "daily_digest.md"
STATE_JSON = ROOT / "state" / "system_state.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_digest_model() -> dict[str, Any]:
    state = load_json(STATE_JSON)
    if not state:
        raise RuntimeError("state/system_state.json is missing; run system-state-build first")
    return {
        "generated_at": utc_now(),
        "state_generated_at": state.get("generated_at"),
        "health_score": state.get("health_score"),
        "trend": state.get("trend", "unknown"),
        "reflex_confidence": state.get("latest_reflex_confidence"),
        "risk_class": state.get("current_risk_class"),
        "incident_count": state.get("incident_count", 0),
        "repeated_anomaly_count": state.get("repeated_anomaly_count", 0),
        "repeated_anomalies": state.get("repeated_anomalies", {}),
        "dmn_append_count": state.get("dmn_append_count", 0),
        "baseline_deviation": (state.get("baseline_deviation") or {}).get("overall_severity"),
        "recommendations": state.get("recommendations", []),
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
        f"- state_generated_at: {model['state_generated_at']}",
        f"- health_score: {model['health_score']}",
        f"- trend: {model['trend']}",
        f"- reflex_confidence: {model['reflex_confidence']}",
        f"- risk_class: {model['risk_class']}",
        f"- incident_count: {model['incident_count']}",
        f"- repeated_anomaly_count: {model['repeated_anomaly_count']}",
        f"- repeated_anomalies: {repeated}",
        f"- dmn_append_count: {model['dmn_append_count']}",
        f"- baseline_deviation: {model['baseline_deviation']}",
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
    record_checksum(DIGEST_MD, "somatic_daily_digest_build", {"source": str(STATE_JSON.relative_to(ROOT))})
    memory = {
        "daily_digest": str(DIGEST_MD.relative_to(ROOT)),
        "health_score": model["health_score"],
        "trend": model["trend"],
        "reflex_confidence": model["reflex_confidence"],
        "risk_class": model["risk_class"],
        "incident_count": model["incident_count"],
        "repeated_anomaly_count": model["repeated_anomaly_count"],
        "dmn_append_count": model["dmn_append_count"],
        "baseline_deviation": model["baseline_deviation"],
        "recommendations_only": True,
        "external_notifications": "none",
    }
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
