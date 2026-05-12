#!/usr/bin/env python3
"""Convert Guardian Dreaming candidates into a reviewable recalibration queue."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json
from build_system_state import build_system_state
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
STATE_JSON = ROOT / "state" / "system_state.json"
DREAM_JSON = ROOT / "guardian" / "dreams" / "latest_dream.json"
INCIDENT_INDEX = ROOT / "guardian" / "incidents" / "index.json"
CALIBRATION_JSON = ROOT / "guardian" / "incidents" / "reflex_confidence_calibration.json"
QUEUE_DIR = ROOT / "guardian" / "recalibration"
QUEUE_JSON = QUEUE_DIR / "queue.json"
QUEUE_MD = QUEUE_DIR / "queue.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def incident_patterns(index: dict[str, Any]) -> dict[str, Any]:
    patterns = index.get("patterns", {})
    return {
        "incident_count": index.get("incident_count", 0),
        "latest_severity": patterns.get("latest_severity"),
        "repeated_anomaly_types": patterns.get("repeated_anomaly_types", {}),
        "confidence_classes": patterns.get("confidence_classes", {}),
        "severity_by_rule": patterns.get("severity_by_rule", {}),
    }


def calibration_context(calibration: dict[str, Any]) -> dict[str, Any]:
    anomalies = calibration.get("anomalies", [])
    latest = anomalies[-1] if anomalies else {}
    return {
        "anomaly_count": len(anomalies),
        "latest_rule": latest.get("rule"),
        "latest_confidence": latest.get("confidence"),
        "latest_confidence_class": latest.get("confidence_class"),
        "latest_true_anomaly": latest.get("true_anomaly"),
        "latest_recommendation": latest.get("recommendation"),
    }


def build_queue_item(candidate: dict[str, Any], state: dict[str, Any], patterns: dict[str, Any], calibration: dict[str, Any]) -> dict[str, Any]:
    incident = candidate.get("incident")
    rule = candidate.get("rule")
    suggestion = candidate.get("recalibration_suggestion", "")
    suggested_confidence = candidate.get("suggested_confidence")
    repeated = patterns.get("repeated_anomaly_types", {}).get(rule, 0)
    source_evidence = [
        f"dream_candidate={DREAM_JSON.relative_to(ROOT)}",
        f"incident={incident}",
        f"rule={rule}",
        f"incident_count={patterns.get('incident_count')}",
        f"repeated_anomaly_types={stable_json(patterns.get('repeated_anomaly_types', {}))}",
        f"confidence_classes={stable_json(patterns.get('confidence_classes', {}))}",
        f"latest_reflex_confidence={state.get('latest_reflex_confidence')}",
        f"calibration_latest_rule={calibration.get('anomalies', [{}])[-1].get('rule') if calibration.get('anomalies') else 'none'}",
    ]
    expected_benefit = (
        "Keeps repeated high-memory warnings visible in review while reducing the chance that low-confidence artifacts remain underweighted."
        if rule == "high_memory_usage"
        else "Creates a structured review item for the recalibration candidate."
    )
    risk_of_overfitting = (
        "medium"
        if repeated >= 2
        else "high"
    )
    return {
        "candidate_rule": rule,
        "incident": incident,
        "source_evidence": source_evidence,
        "expected_benefit": expected_benefit,
        "risk_of_overfitting": risk_of_overfitting,
        "required_approval_level": "PREPARE_FOR_APPROVAL",
        "rollback_note": "Discard the queue item and preserve the current calibration if review rejects the candidate.",
        "recommended_confidence": suggested_confidence,
        "candidate_suggestion": suggestion,
    }


def build_queue() -> dict[str, Any]:
    state = load_json(STATE_JSON)
    if not state:
        raise RuntimeError("state/system_state.json is missing; run system-state-build first")
    dream = load_json(DREAM_JSON)
    if not dream:
        raise RuntimeError("guardian/dreams/latest_dream.json is missing; run dream-build first")
    incidents = load_json(INCIDENT_INDEX)
    calibration = load_json(CALIBRATION_JSON)
    patterns = incident_patterns(incidents)
    calibration_meta = calibration_context(calibration)
    items = [
        build_queue_item(candidate, state, patterns, calibration)
        for candidate in dream.get("recalibration_candidates", [])
    ]
    return {
        "generated_at": utc_now(),
        "queue_count": len(items),
        "items": items,
        "incident_patterns": patterns,
        "calibration_context": calibration_meta,
        "corrective_actions": "none",
        "recommendations_only": True,
        "sources": {
            "dream": str(DREAM_JSON.relative_to(ROOT)),
            "system_state": str(STATE_JSON.relative_to(ROOT)),
            "incident_patterns": str(INCIDENT_INDEX.relative_to(ROOT)),
            "reflex_confidence_calibration": str(CALIBRATION_JSON.relative_to(ROOT)),
        },
    }


def write_queue(queue: dict[str, Any]) -> None:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Recalibration Queue",
        "",
        f"- generated_at: {queue['generated_at']}",
        f"- queue_count: {queue['queue_count']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Queue Items",
        "",
    ]
    for item in queue["items"]:
        lines.extend(
            [
                f"### {item['candidate_rule']}",
                "",
                f"- incident: {item['incident']}",
                f"- recommended_confidence: {item['recommended_confidence']}",
                f"- candidate_suggestion: {item['candidate_suggestion']}",
                f"- expected_benefit: {item['expected_benefit']}",
                f"- risk_of_overfitting: {item['risk_of_overfitting']}",
                f"- required_approval_level: {item['required_approval_level']}",
                f"- rollback_note: {item['rollback_note']}",
                "- source_evidence:",
            ]
        )
        for evidence in item["source_evidence"]:
            lines.append(f"  - {evidence}")
        lines.append("")
    lines.extend(
        [
            "## Incident Patterns",
            "",
            f"- {stable_json(queue['incident_patterns'])}",
            "",
            "## Calibration Context",
            "",
            f"- {stable_json(queue['calibration_context'])}",
            "",
            "## Sources",
            "",
        ]
    )
    for key, value in queue["sources"].items():
        lines.append(f"- {key}: {value}")
    QUEUE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    QUEUE_JSON.write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_queue_build() -> dict[str, Any]:
    queue = build_queue()
    write_queue(queue)
    build_system_state()
    record_checksum(QUEUE_MD, "recalibration_queue_write", {"source": "dream_recalibration_candidates"})
    record_checksum(QUEUE_JSON, "recalibration_queue_index_write", {"source": "dream_recalibration_candidates"})
    summary = {
        "queue": str(QUEUE_MD.relative_to(ROOT)),
        "queue_json": str(QUEUE_JSON.relative_to(ROOT)),
        "queue_count": queue["queue_count"],
        "recommendations_only": True,
    }
    append_memory(stable_json(summary), ["guardian", "recalibration", "night25"], "recalibration_queue")
    log_action("recalibration:queue-build", "completed", "ALLOW", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a recalibration queue from Guardian Dreaming candidates.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_queue_build()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
