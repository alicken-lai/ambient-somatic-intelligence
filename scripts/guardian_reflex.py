#!/usr/bin/env python3
"""Detect local anomalies and trigger safe Guardian reflex responses."""

from __future__ import annotations

import argparse
import json
import re
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
BASELINE_JSON = ROOT / "guardian" / "baselines" / "telemetry_baseline.json"
CALIBRATION_JSON = ROOT / "guardian" / "incidents" / "reflex_confidence_calibration.json"
CALIBRATION_REPORT = ROOT / "guardian" / "incidents" / "reflex_confidence_calibration.md"

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


def docker_container_stats() -> list[dict[str, Any]]:
    completed = run(["docker", "stats", "--no-stream", "--format", "{{json .}}"])
    stats: list[dict[str, Any]] = []
    if completed.returncode != 0:
        return stats
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        stats.append({
            "name": raw.get("Name"),
            "memory_usage": raw.get("MemUsage"),
            "memory_percent": raw.get("MemPerc"),
            "cpu_percent": raw.get("CPUPerc"),
        })
    return stats


def percent_value(value: object) -> float:
    match = re.search(r"([0-9.]+)", str(value))
    return float(match.group(1)) if match else 0.0


def swap_usage() -> dict[str, Any]:
    completed = run(["sysctl", "vm.swapusage"])
    line = completed.stdout.strip()
    used_match = re.search(r"used = ([0-9.]+)([MGT])", line)
    return {
        "raw": line,
        "used": used_match.group(1) + used_match.group(2) if used_match else "unknown",
        "used_mb": size_to_mb(used_match.group(1), used_match.group(2)) if used_match else None,
    }


def size_to_mb(amount: str, unit: str) -> float:
    value = float(amount)
    if unit == "G":
        return value * 1024
    if unit == "T":
        return value * 1024 * 1024
    return value


def docker_vm_context() -> dict[str, Any]:
    completed = run(["ps", "-axo", "pid,rss,%mem,args"])
    for line in completed.stdout.splitlines()[1:]:
        if "com.docker.virtualization" not in line:
            continue
        match = re.match(r"\s*(\d+)\s+(\d+)\s+([0-9.]+)\s+(.*)", line)
        if not match:
            continue
        pid, rss_kb, memory_percent, command = match.groups()
        memory_match = re.search(r"--memoryMiB\s+(\d+)", command)
        cpu_match = re.search(r"--cpus\s+(\d+)", command)
        return {
            "detected": True,
            "pid": int(pid),
            "rss_mb": round(int(rss_kb) / 1024, 1),
            "memory_percent": float(memory_percent),
            "memory_mib": int(memory_match.group(1)) if memory_match else None,
            "cpus": int(cpu_match.group(1)) if cpu_match else None,
        }
    return {"detected": False, "pid": None, "rss_mb": None, "memory_percent": None, "memory_mib": None, "cpus": None}


def memory_baseline_context(value: float) -> dict[str, Any]:
    baseline = load_json_file(BASELINE_JSON) or {}
    metric = baseline.get("metrics", {}).get("memory_used_percent", {}).get("baseline", {})
    mean = float(metric.get("mean", value))
    stddev = float(metric.get("stddev", 0.0))
    delta = round(value - mean, 4)
    if delta > 0:
        direction = "above_baseline"
    elif delta < 0:
        direction = "below_baseline"
    else:
        direction = "at_baseline"
    z_score = round(delta / stddev, 4) if stddev > 0 else 0.0
    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "delta": delta,
        "direction": direction,
        "z_score": z_score,
    }


def confidence_class(score: float) -> str:
    if score < 0.4:
        return "low_confidence_watch"
    if score < 0.75:
        return "medium_confidence_review"
    return "high_confidence_incident"


def calibrated_anomaly(rule: str, severity: str, evidence: Any, recommendation: str, value: float | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    score = 0.55 if severity == "warning" else 0.8
    artifact = False
    true_anomaly = severity == "critical"

    if rule == "high_memory_usage" and value is not None:
        baseline = context.get("baseline", {})
        swap = context.get("swap", {})
        containers = context.get("containers", [])
        docker_vm = context.get("docker_vm", {})
        max_container_memory = max([percent_value(item.get("memory_percent")) for item in containers] or [0.0])

        score = 0.35
        if value >= 98.0:
            score += 0.15
        if baseline.get("direction") == "above_baseline":
            score += 0.2
        if baseline.get("direction") == "below_baseline":
            score -= 0.15
            artifact = True
        if float(swap.get("used_mb") or 0.0) > 0:
            score += 0.25
            true_anomaly = True
        if max_container_memory >= 70.0:
            score += 0.15
        elif docker_vm.get("detected") and max_container_memory < 10.0:
            score -= 0.1
            artifact = True
        context["max_container_memory_percent"] = round(max_container_memory, 2)
        if value >= 95.0:
            true_anomaly = not artifact or float(swap.get("used_mb") or 0.0) > 0

    score = max(0.0, min(1.0, score))
    return {
        "rule": rule,
        "severity": severity,
        "value": value,
        "evidence": evidence,
        "recommendation": recommendation,
        "confidence": round(score, 2),
        "confidence_class": confidence_class(score),
        "true_anomaly": true_anomaly,
        "scoring_artifact": artifact,
        "context": context,
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
    container_stats = docker_container_stats()
    swap = swap_usage()
    docker_vm = docker_vm_context()
    ocr_records = latest_ocr_records()

    if len(telemetry) >= 3 and all(float(item.get("cpu_usage_percent", 0)) >= 85.0 for item in telemetry[-3:]):
        anomalies.append(calibrated_anomaly(
            "high_cpu_sustained",
            "warning",
            [item["_path"] for item in telemetry[-3:]],
            "Review local process load before enabling broader CUA actions.",
        ))

    if telemetry:
        latest = telemetry[-1]
        memory_percent = float(latest.get("memory_usage", {}).get("used_percent", 0))
        if memory_percent >= 90.0:
            anomalies.append(calibrated_anomaly(
                "high_memory_usage",
                "warning",
                latest["_path"],
                "Review memory pressure and avoid launching additional heavy local tasks.",
                memory_percent,
                {
                    "baseline": memory_baseline_context(memory_percent),
                    "swap": swap,
                    "docker_vm": docker_vm,
                    "containers": container_stats,
                },
            ))
        if len(telemetry) >= 2:
            previous_disk = float(telemetry[-2].get("disk_usage", {}).get("used_percent", 0))
            current_disk = float(latest.get("disk_usage", {}).get("used_percent", 0))
            growth = round(current_disk - previous_disk, 2)
            if growth >= 2.0:
                anomalies.append(calibrated_anomaly(
                    "disk_usage_growth",
                    "warning",
                    [telemetry[-2]["_path"], latest["_path"]],
                    "Inspect recent local artifact growth and archive only after manual review.",
                    growth,
                ))

    for service in (prometheus, grafana):
        if not service["reachable"]:
            anomalies.append(calibrated_anomaly(
                f"{service['name']}_unreachable",
                "critical",
                service,
                f"Check {service['name']} container status; do not restart automatically.",
            ))

    expected = {"ambient-prometheus", "ambient-grafana"}
    running = {item.get("Name") for item in docker["containers"] if item.get("State") == "running"}
    missing = sorted(expected - running)
    if missing or not docker["ok"]:
        anomalies.append(calibrated_anomaly(
            "container_down",
            "critical",
            {"missing": missing, "docker": docker},
            "Inspect Docker Desktop and compose status manually; no automatic restart.",
        ))

    for record in ocr_records:
        parsed = record.get("ocr", {}).get("parsed", {})
        warnings = parsed.get("warning_labels") or []
        if warnings:
            anomalies.append(calibrated_anomaly(
                "ocr_warning_detected",
                "warning",
                {"path": record["_path"], "warnings": warnings[:5]},
                "Review captured dashboard text before any interactive CUA expansion.",
            ))

    inputs = {
        "telemetry_count": len(telemetry),
        "latest_telemetry": telemetry[-1] if telemetry else None,
        "prometheus": prometheus,
        "grafana": grafana,
        "docker": docker,
        "docker_stats": container_stats,
        "swap": swap,
        "docker_vm": docker_vm,
        "ocr_records": [record.get("_path") for record in ocr_records],
    }
    return anomalies, inputs


def write_calibration_report(anomalies: list[dict[str, Any]], inputs: dict[str, Any]) -> dict[str, Any]:
    enforce_allowed_response("create calibration markdown note")
    CALIBRATION_JSON.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "generated_at": utc_now(),
        "anomaly_count": len(anomalies),
        "confidence_classes": {},
        "recommendations_only": True,
        "corrective_actions": "none",
        "anomalies": anomalies,
        "context": {
            "swap": inputs.get("swap"),
            "docker_vm": inputs.get("docker_vm"),
            "docker_stats": inputs.get("docker_stats"),
            "latest_telemetry": (inputs.get("latest_telemetry") or {}).get("_path"),
        },
    }
    for anomaly in anomalies:
        key = anomaly["confidence_class"]
        summary["confidence_classes"][key] = summary["confidence_classes"].get(key, 0) + 1

    CALIBRATION_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Guardian Reflex Confidence Calibration",
        "",
        f"- generated_at: {summary['generated_at']}",
        f"- anomaly_count: {summary['anomaly_count']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Classification",
        "",
        "| Class | Count |",
        "| --- | ---: |",
    ]
    for name in ("low_confidence_watch", "medium_confidence_review", "high_confidence_incident"):
        lines.append(f"| {name} | {summary['confidence_classes'].get(name, 0)} |")
    lines.extend(["", "## Anomalies", "", "| Rule | Confidence | Class | True Anomaly | Scoring Artifact | Baseline Direction | Swap Used | Max Container Memory |", "| --- | ---: | --- | --- | --- | --- | ---: | ---: |"])
    for anomaly in anomalies:
        context = anomaly.get("context", {})
        baseline = context.get("baseline", {})
        swap_context = context.get("swap", {})
        lines.append(
            f"| {anomaly['rule']} | {anomaly['confidence']} | {anomaly['confidence_class']} | "
            f"{anomaly['true_anomaly']} | {anomaly['scoring_artifact']} | "
            f"{baseline.get('direction', 'n/a')} | {swap_context.get('used', 'n/a')} | "
            f"{context.get('max_container_memory_percent', 'n/a')} |"
        )
    lines.extend(["", "## Context", "", f"```json\n{json.dumps(summary['context'], indent=2, sort_keys=True)}\n```", "", "## Recommendations", ""])
    if anomalies:
        for recommendation in sorted({item["recommendation"] for item in anomalies}):
            lines.append(f"- {recommendation}")
    else:
        lines.append("- No corrective action recommended; continue calibrated observation.")
    CALIBRATION_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log_action("reflex:confidence-calibration", "completed", "ALLOW", {
        "report": str(CALIBRATION_REPORT.relative_to(ROOT)),
        "anomalies": len(anomalies),
        "classes": summary["confidence_classes"],
    })
    return summary


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


def write_incident_note(anomalies: list[dict[str, Any]], inputs: dict[str, Any], extra: dict[str, Any], screenshot: dict[str, Any], calibration: dict[str, Any]) -> Path:
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
        f"- confidence_classes: {stable_json(calibration.get('confidence_classes', {}))}",
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
                f"- confidence: {anomaly['confidence']}",
                f"- confidence_class: {anomaly['confidence_class']}",
                f"- true_anomaly: {anomaly['true_anomaly']}",
                f"- scoring_artifact: {anomaly['scoring_artifact']}",
                f"- recommendation: {anomaly['recommendation']}",
                f"- evidence: `{stable_json(anomaly.get('evidence', {}))}`",
                f"- context: `{stable_json(anomaly.get('context', {}))}`",
                "",
            ])
    else:
        lines.extend(["No active anomalies detected.", ""])
    lines.extend(["## Inputs", "", f"```json\n{json.dumps(inputs, indent=2, sort_keys=True)}\n```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    log_action("reflex:create-incident-note", "completed", "ALLOW", {"incident": str(path.relative_to(ROOT)), "anomalies": len(anomalies)})
    return path


def log_incident(anomalies: list[dict[str, Any]], incident_path: Path, extra: dict[str, Any], screenshot: dict[str, Any], calibration: dict[str, Any]) -> dict[str, Any]:
    enforce_allowed_response("log incident")
    record = {
        "timestamp": utc_now(),
        "policy": str(POLICY_FILE.relative_to(ROOT)),
        "anomalies": anomalies,
        "incident": str(incident_path.relative_to(ROOT)),
        "extra_telemetry": extra.get("path"),
        "screenshot": screenshot.get("path"),
        "confidence_classes": calibration.get("confidence_classes", {}),
        "calibration_report": str(CALIBRATION_REPORT.relative_to(ROOT)),
    }
    REFLEX_LOG.parent.mkdir(parents=True, exist_ok=True)
    with REFLEX_LOG.open("a", encoding="utf-8") as handle:
        handle.write(stable_json(record) + "\n")
    log_action("reflex:log-incident", "completed", "ALLOW", {"incident": record["incident"], "anomalies": len(anomalies)})
    return record


def append_reflex_memory(record: dict[str, Any]) -> None:
    enforce_allowed_response("append DMN memory")
    append_memory(stable_json(record), ["guardian", "reflex", "incident", "confidence", "night11"], "guardian_reflex")


def run_reflex() -> dict[str, Any]:
    anomalies, inputs = detect_anomalies()
    calibration = write_calibration_report(anomalies, inputs)
    extra = collect_extra_telemetry()
    screenshot = capture_reflex_screenshot()
    incident_path = write_incident_note(anomalies, inputs, extra, screenshot, calibration)
    incident = log_incident(anomalies, incident_path, extra, screenshot, calibration)
    append_reflex_memory(incident)
    return {
        "status": "completed",
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "incident": str(incident_path.relative_to(ROOT)),
        "extra_telemetry": extra.get("path"),
        "screenshot": screenshot,
        "confidence_classes": calibration.get("confidence_classes", {}),
        "calibration_report": str(CALIBRATION_REPORT.relative_to(ROOT)),
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
