#!/usr/bin/env python3
"""Detect local anomalies and trigger safe Guardian reflex responses."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from action_log import log_action, stable_json
from guardian_check import classify_action
from remember import append_memory
from sense_local import collect_snapshot, write_snapshot
from vision_capture import capture as capture_visual


ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = ROOT / "guardian" / "reflex_policy.yaml"
INCIDENT_DIR = ROOT / "guardian" / "incidents"
REFLEX_LOG = ROOT / "guardian" / "reflex.jsonl"
TELEMETRY_DIR = ROOT / "observability" / "snapshots"
CUA_ANALYSIS_DIR = ROOT / "tools" / "cua" / "analysis"

BLOCKED_RESPONSE_TERMS = {
    "restart",
    "kill",
    "delete",
    "modify system settings",
    "send external notifications",
    "shutdown",
    "rm ",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def safe_action(action: str) -> dict[str, object]:
    lowered = action.casefold()
    blocked = sorted(term for term in BLOCKED_RESPONSE_TERMS if term in lowered)
    if blocked:
        return {"risk": "BLOCK", "matched": blocked, "action": action}
    guardian = classify_action(action)
    if guardian["risk"] == "BLOCK":
        return guardian
    return {"risk": "ALLOW", "matched": guardian.get("matched", []), "action": action}


def enforce_allowed_response(action: str) -> None:
    guardian = safe_action(action)
    if guardian["risk"] != "ALLOW":
        log_action(action, "blocked", str(guardian["risk"]), guardian)
        raise RuntimeError(f"blocked reflex response: {action}")


def load_json_file(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def telemetry_snapshots(limit: int = 5) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(TELEMETRY_DIR.glob("telemetry-*.json"))[-limit:]:
        record = load_json_file(path)
        if record:
            record["_path"] = str(path.relative_to(ROOT))
            records.append(record)
    return records


def health_check(name: str, url: str) -> dict[str, Any]:
    try:
        status = urlopen(url, timeout=5).status
        return {"name": name, "url": url, "reachable": 200 <= status < 400, "status": status}
    except (OSError, URLError) as exc:
        return {"name": name, "url": url, "reachable": False, "error": exc.__class__.__name__}


def docker_status() -> dict[str, Any]:
    completed = run(["docker", "compose", "-f", "observability/docker-compose.yml", "ps", "--format", "json"])
    containers: list[dict[str, Any]] = []
    if completed.returncode == 0:
        for line in completed.stdout.splitlines():
            if line.strip():
                containers.append(json.loads(line))
    return {
        "ok": completed.returncode == 0,
        "containers": containers,
        "stderr": completed.stderr.strip(),
    }


def latest_ocr_records(limit: int = 12) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(CUA_ANALYSIS_DIR.glob("*.json"))[-limit:]:
        record = load_json_file(path)
        if record and isinstance(record.get("ocr"), dict):
            record["_path"] = str(path.relative_to(ROOT))
            records.append(record)
    return records


def detect_anomalies() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    telemetry = telemetry_snapshots()
    prometheus = health_check("prometheus", "http://127.0.0.1:9090/-/ready")
    grafana = health_check("grafana", "http://127.0.0.1:3000/api/health")
    docker = docker_status()
    ocr_records = latest_ocr_records()

    if len(telemetry) >= 3 and all(float(item.get("cpu_usage_percent", 0)) >= 85.0 for item in telemetry[-3:]):
        anomalies.append({
            "rule": "high_cpu_sustained",
            "severity": "warning",
            "evidence": [item["_path"] for item in telemetry[-3:]],
            "recommendation": "Review local process load before enabling broader CUA actions.",
        })

    if telemetry:
        latest = telemetry[-1]
        memory_percent = float(latest.get("memory_usage", {}).get("used_percent", 0))
        if memory_percent >= 90.0:
            anomalies.append({
                "rule": "high_memory_usage",
                "severity": "warning",
                "value": memory_percent,
                "evidence": latest["_path"],
                "recommendation": "Review memory pressure and avoid launching additional heavy local tasks.",
            })
        if len(telemetry) >= 2:
            previous_disk = float(telemetry[-2].get("disk_usage", {}).get("used_percent", 0))
            current_disk = float(latest.get("disk_usage", {}).get("used_percent", 0))
            growth = round(current_disk - previous_disk, 2)
            if growth >= 2.0:
                anomalies.append({
                    "rule": "disk_usage_growth",
                    "severity": "warning",
                    "value": growth,
                    "evidence": [telemetry[-2]["_path"], latest["_path"]],
                    "recommendation": "Inspect recent local artifact growth and archive only after manual review.",
                })

    for service in (prometheus, grafana):
        if not service["reachable"]:
            anomalies.append({
                "rule": f"{service['name']}_unreachable",
                "severity": "critical",
                "evidence": service,
                "recommendation": f"Check {service['name']} container status; do not restart automatically.",
            })

    expected = {"ambient-prometheus", "ambient-grafana"}
    running = {item.get("Name") for item in docker["containers"] if item.get("State") == "running"}
    missing = sorted(expected - running)
    if missing or not docker["ok"]:
        anomalies.append({
            "rule": "container_down",
            "severity": "critical",
            "evidence": {"missing": missing, "docker": docker},
            "recommendation": "Inspect Docker Desktop and compose status manually; no automatic restart.",
        })

    for record in ocr_records:
        parsed = record.get("ocr", {}).get("parsed", {})
        warnings = parsed.get("warning_labels") or []
        if warnings:
            anomalies.append({
                "rule": "ocr_warning_detected",
                "severity": "warning",
                "evidence": {"path": record["_path"], "warnings": warnings[:5]},
                "recommendation": "Review captured dashboard text before any interactive CUA expansion.",
            })

    inputs = {
        "telemetry_count": len(telemetry),
        "latest_telemetry": telemetry[-1] if telemetry else None,
        "prometheus": prometheus,
        "grafana": grafana,
        "docker": docker,
        "ocr_records": [record.get("_path") for record in ocr_records],
    }
    return anomalies, inputs


def collect_extra_telemetry() -> dict[str, Any]:
    enforce_allowed_response("collect extra telemetry snapshot")
    snapshot = collect_snapshot()
    path = write_snapshot(snapshot)
    append_memory(stable_json(snapshot), ["telemetry", "guardian-reflex", "night6"], "guardian_reflex")
    log_action("reflex:collect-extra-telemetry", "completed", "ALLOW", {"snapshot": str(path.relative_to(ROOT))})
    return {"snapshot": snapshot, "path": str(path.relative_to(ROOT))}


def capture_reflex_screenshot() -> dict[str, Any]:
    enforce_allowed_response("capture screenshot")
    result = capture_visual("grafana")
    log_action("reflex:capture-screenshot", "completed", "ALLOW", {"target": "grafana"})
    return {
        "path": result["metadata"]["path"],
        "confidence": result["ocr"]["confidence"],
        "warnings": result["ocr"]["parsed"].get("warning_labels", []),
    }


def write_incident_note(anomalies: list[dict[str, Any]], inputs: dict[str, Any], extra: dict[str, Any], screenshot: dict[str, Any]) -> Path:
    enforce_allowed_response("create incident markdown note")
    INCIDENT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = utc_now().replace(":", "").replace("+", "Z")
    path = INCIDENT_DIR / f"incident-{stamp}.md"
    lines = [
        "# Guardian Reflex Incident",
        "",
        f"- timestamp: {utc_now()}",
        f"- policy: {POLICY_FILE.relative_to(ROOT)}",
        f"- anomalies: {len(anomalies)}",
        f"- extra_telemetry: {extra.get('path')}",
        f"- screenshot: {screenshot.get('path')}",
        f"- screenshot_ocr_confidence: {screenshot.get('confidence')}",
        "",
        "## Anomalies",
        "",
    ]
    if anomalies:
        for anomaly in anomalies:
            lines.extend([
                f"### {anomaly['rule']}",
                "",
                f"- severity: {anomaly['severity']}",
                f"- recommendation: {anomaly['recommendation']}",
                f"- evidence: `{stable_json(anomaly.get('evidence', {}))}`",
                "",
            ])
    else:
        lines.extend(["No active anomalies detected.", ""])
    lines.extend(["## Inputs", "", f"```json\n{json.dumps(inputs, indent=2, sort_keys=True)}\n```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    log_action("reflex:create-incident-note", "completed", "ALLOW", {"incident": str(path.relative_to(ROOT)), "anomalies": len(anomalies)})
    return path


def log_incident(anomalies: list[dict[str, Any]], incident_path: Path, extra: dict[str, Any], screenshot: dict[str, Any]) -> dict[str, Any]:
    enforce_allowed_response("log incident")
    record = {
        "timestamp": utc_now(),
        "policy": str(POLICY_FILE.relative_to(ROOT)),
        "anomalies": anomalies,
        "incident": str(incident_path.relative_to(ROOT)),
        "extra_telemetry": extra.get("path"),
        "screenshot": screenshot.get("path"),
    }
    REFLEX_LOG.parent.mkdir(parents=True, exist_ok=True)
    with REFLEX_LOG.open("a", encoding="utf-8") as handle:
        handle.write(stable_json(record) + "\n")
    log_action("reflex:log-incident", "completed", "ALLOW", {"incident": record["incident"], "anomalies": len(anomalies)})
    return record


def append_reflex_memory(record: dict[str, Any]) -> None:
    enforce_allowed_response("append DMN memory")
    append_memory(stable_json(record), ["guardian", "reflex", "incident", "night6"], "guardian_reflex")


def run_reflex() -> dict[str, Any]:
    anomalies, inputs = detect_anomalies()
    extra = collect_extra_telemetry()
    screenshot = capture_reflex_screenshot()
    incident_path = write_incident_note(anomalies, inputs, extra, screenshot)
    incident = log_incident(anomalies, incident_path, extra, screenshot)
    append_reflex_memory(incident)
    return {
        "status": "completed",
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "incident": str(incident_path.relative_to(ROOT)),
        "extra_telemetry": extra.get("path"),
        "screenshot": screenshot,
        "recommendations": [item["recommendation"] for item in anomalies],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Guardian Reflex loop.")
    parser.add_argument("--once", action="store_true", help="Run one reflex evaluation.")
    args = parser.parse_args()
    if not args.once:
        parser.error("--once is required for the local reflex runner")

    try:
        result = run_reflex()
    except Exception as exc:
        log_action("reflex:run", "failed", "ALLOW", {"error": str(exc)})
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(stable_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
