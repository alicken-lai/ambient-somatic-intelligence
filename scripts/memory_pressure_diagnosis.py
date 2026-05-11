#!/usr/bin/env python3
"""Diagnose local memory pressure without corrective actions."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "observability" / "snapshots"
BASELINE_JSON = ROOT / "guardian" / "baselines" / "telemetry_baseline.json"
HEALTH_JSON = ROOT / "guardian" / "health" / "health_scores.json"
REPORT_MD = ROOT / "guardian" / "health" / "memory_pressure_report.md"
REPORT_JSON = ROOT / "guardian" / "health" / "memory_pressure_report.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_snapshot() -> dict[str, Any]:
    candidates = sorted(SNAPSHOT_DIR.glob("telemetry-*.json"))
    if not candidates:
        raise RuntimeError("no telemetry snapshots found")
    record = load_json(candidates[-1])
    record["_path"] = str(candidates[-1].relative_to(ROOT))
    return record


def legacy_memory_score(value: float, baseline: dict[str, Any]) -> dict[str, Any]:
    mean = float(baseline["mean"])
    stddev = float(baseline["stddev"])
    z_score = abs((value - mean) / stddev) if stddev > 0 else (0.0 if value == mean else 3.0)
    score = max(0.0, min(100.0, 100.0 - z_score * 18.0))
    return {
        "baseline_mean": round(mean, 4),
        "baseline_stddev": round(stddev, 4),
        "z_score": round(z_score, 4),
        "score": round(score, 2),
    }


def parse_ps(stdout: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in stdout.splitlines()[1:]:
        match = re.match(r"\s*(\d+)\s+(\d+)\s+([0-9.]+)\s+(.*)", line)
        if not match:
            continue
        pid, rss_kb, mem_percent, command = match.groups()
        rows.append({
            "pid": int(pid),
            "rss_kb": int(rss_kb),
            "rss_mb": round(int(rss_kb) / 1024, 1),
            "memory_percent": float(mem_percent),
            "command": command,
        })
    return sorted(rows, key=lambda item: item["rss_kb"], reverse=True)


def docker_vm_reservation(processes: list[dict[str, Any]]) -> dict[str, Any]:
    for process in processes:
        command = process["command"]
        if "com.docker.virtualization" not in command:
            continue
        memory_match = re.search(r"--memoryMiB\s+(\d+)", command)
        cpu_match = re.search(r"--cpus\s+(\d+)", command)
        return {
            "detected": True,
            "memory_mib": int(memory_match.group(1)) if memory_match else None,
            "cpus": int(cpu_match.group(1)) if cpu_match else None,
            "process": process,
        }
    return {"detected": False, "memory_mib": None, "cpus": None, "process": None}


def docker_container_stats() -> list[dict[str, Any]]:
    result = run(["docker", "stats", "--no-stream", "--format", "{{json .}}"])
    stats: list[dict[str, Any]] = []
    if result["returncode"] != 0:
        return stats
    for line in result["stdout"].splitlines():
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


def parse_swap(stdout: str) -> dict[str, Any]:
    swap_line = next((line for line in stdout.splitlines() if line.startswith("vm.swapusage:")), "")
    used_match = re.search(r"used = ([0-9.]+)([MGT])", swap_line)
    total_match = re.search(r"total = ([0-9.]+)([MGT])", swap_line)
    return {
        "raw": swap_line,
        "total": total_match.group(1) + total_match.group(2) if total_match else "unknown",
        "used": used_match.group(1) + used_match.group(2) if used_match else "unknown",
    }


def diagnose() -> dict[str, Any]:
    snapshot = latest_snapshot()
    memory = snapshot["memory_usage"]
    baseline = load_json(BASELINE_JSON)["metrics"]["memory_used_percent"]["baseline"]
    health = load_json(HEALTH_JSON)["current"]["subsystems"]["memory_health"]

    ps_result = run(["ps", "-axo", "pid,rss,%mem,args"])
    processes = parse_ps(ps_result["stdout"])
    docker_vm = docker_vm_reservation(processes)
    docker_stats = docker_container_stats()
    sysctl_result = run(["sysctl", "hw.memsize", "vm.swapusage"])
    swap = parse_swap(sysctl_result["stdout"])

    value = float(memory["used_percent"])
    baseline_mean = float(baseline["mean"])
    delta_from_baseline = round(value - baseline_mean, 4)
    legacy = legacy_memory_score(value, baseline)
    current_metric = health["metrics"][0]["memory_used_percent"]
    docker_limit_mib = docker_vm.get("memory_mib")
    docker_limit_gib = round(float(docker_limit_mib) / 1024, 2) if docker_limit_mib else None

    artifact = legacy["score"] == 0.0 and delta_from_baseline < 0
    true_risk = "moderate"
    if value >= 98.0 and swap["used"] not in {"0.00M", "0M", "unknown"}:
        true_risk = "high"
    elif value < 98.0 and swap["used"] in {"0.00M", "0M"}:
        true_risk = "watch"

    recommendations = [
        "Continue observation; do not restart Docker or kill processes automatically.",
        "Treat Docker Desktop's VM reservation as a major host-memory context factor.",
        "Avoid adding heavier local workloads while host memory remains above 95%.",
        "Manually review Docker Desktop memory allocation later if sustained pressure continues.",
        "Manually close unused browser or remote desktop sessions only if interactive performance degrades.",
    ]

    result = {
        "generated_at": utc_now(),
        "latest_snapshot": snapshot["_path"],
        "memory_fields": {
            "total_bytes": memory["total_bytes"],
            "used_bytes": memory["used_bytes"],
            "free_bytes": memory["free_bytes"],
            "used_percent": value,
        },
        "baseline": {
            "mean": round(baseline_mean, 4),
            "min": round(float(baseline["min"]), 4),
            "max": round(float(baseline["max"]), 4),
            "stddev": round(float(baseline["stddev"]), 4),
            "delta_from_mean": delta_from_baseline,
        },
        "legacy_scoring_artifact": {
            "detected": artifact,
            "reason": "absolute z-score penalized memory usage below the baseline mean when baseline variance was tiny",
            "legacy_score": legacy["score"],
            "legacy_z_score": legacy["z_score"],
        },
        "adjusted_scoring": {
            "score": health["score"],
            "raw_score": health["raw_score"],
            "incident_penalty": health["incident_penalty"],
            "metric_score": current_metric["score"],
            "deviation_score": current_metric["deviation_score"],
            "absolute_pressure_score": current_metric["absolute_pressure_score"],
            "z_score": current_metric["z_score"],
        },
        "docker_desktop": {
            "vm_reservation_detected": docker_vm["detected"],
            "vm_memory_mib": docker_limit_mib,
            "vm_memory_gib": docker_limit_gib,
            "containers": docker_stats,
        },
        "swap": swap,
        "top_memory_consumers": processes[:10],
        "risk_assessment": {
            "true_risk": true_risk,
            "scoring_artifact": artifact,
            "summary": "memory_health was zero from formula shape, while host memory still deserves watch-level pressure monitoring",
        },
        "recommendations": recommendations,
        "corrective_actions": "none",
    }
    write_reports(result)
    append_memory(stable_json({
        "memory_pressure_report": str(REPORT_MD.relative_to(ROOT)),
        "latest_snapshot": result["latest_snapshot"],
        "memory_used_percent": value,
        "memory_health": health["score"],
        "artifact_detected": artifact,
        "true_risk": true_risk,
        "docker_vm_memory_mib": docker_limit_mib,
        "recommendations_only": True,
    }), ["guardian", "memory-pressure", "night10"], "memory_pressure_diagnosis")
    log_action("memory:pressure_diagnosis", "completed", "ALLOW", {
        "report": str(REPORT_MD.relative_to(ROOT)),
        "artifact_detected": artifact,
        "true_risk": true_risk,
    })
    record_checksum(REPORT_JSON, "memory_pressure_report_json")
    record_checksum(REPORT_MD, "memory_pressure_report_markdown")
    return result


def write_reports(result: dict[str, Any]) -> None:
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fields = result["memory_fields"]
    baseline = result["baseline"]
    adjusted = result["adjusted_scoring"]
    docker = result["docker_desktop"]
    lines = [
        "# Memory Pressure Diagnosis",
        "",
        f"- generated_at: {result['generated_at']}",
        f"- latest_snapshot: {result['latest_snapshot']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Finding",
        "",
        "memory_health reached 0.0 because the prior formula used absolute z-score deviation against a very narrow memory baseline.",
        f"The latest memory_used_percent is {fields['used_percent']}%, which is {baseline['delta_from_mean']} points from the baseline mean of {baseline['mean']}%.",
        "Because that delta is below the mean, the zero score was a scoring artifact, not evidence of worsening memory pressure.",
        "",
        "## Current Memory",
        "",
        "| Field | Value |",
        "| --- | ---: |",
        f"| total_bytes | {fields['total_bytes']} |",
        f"| used_bytes | {fields['used_bytes']} |",
        f"| free_bytes | {fields['free_bytes']} |",
        f"| used_percent | {fields['used_percent']} |",
        "",
        "## Baseline Comparison",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| baseline_mean | {baseline['mean']} |",
        f"| baseline_min | {baseline['min']} |",
        f"| baseline_max | {baseline['max']} |",
        f"| baseline_stddev | {baseline['stddev']} |",
        f"| delta_from_mean | {baseline['delta_from_mean']} |",
        "",
        "## Scoring",
        "",
        "| Score | Value |",
        "| --- | ---: |",
        f"| legacy_memory_score | {result['legacy_scoring_artifact']['legacy_score']} |",
        f"| adjusted_memory_health | {adjusted['score']} |",
        f"| adjusted_raw_score | {adjusted['raw_score']} |",
        f"| incident_penalty | {adjusted['incident_penalty']} |",
        f"| deviation_score | {adjusted['deviation_score']} |",
        f"| absolute_pressure_score | {adjusted['absolute_pressure_score']} |",
        "",
        "## Docker Desktop",
        "",
        f"- vm_reservation_detected: {docker['vm_reservation_detected']}",
        f"- vm_memory_mib: {docker['vm_memory_mib']}",
        f"- vm_memory_gib: {docker['vm_memory_gib']}",
        "",
        "| Container | Memory | Memory % | CPU % |",
        "| --- | ---: | ---: | ---: |",
    ]
    for container in docker["containers"]:
        lines.append(f"| {container['name']} | {container['memory_usage']} | {container['memory_percent']} | {container['cpu_percent']} |")
    lines.extend([
        "",
        "## Top Memory Consumers",
        "",
        "| PID | RSS MB | Memory % | Command |",
        "| ---: | ---: | ---: | --- |",
    ])
    for process in result["top_memory_consumers"]:
        command = str(process["command"]).replace("|", "/")[:220]
        lines.append(f"| {process['pid']} | {process['rss_mb']} | {process['memory_percent']} | `{command}` |")
    lines.extend([
        "",
        "## Risk Assessment",
        "",
        f"- true_risk: {result['risk_assessment']['true_risk']}",
        f"- scoring_artifact: {result['risk_assessment']['scoring_artifact']}",
        f"- swap: {result['swap']['raw']}",
        f"- summary: {result['risk_assessment']['summary']}",
        "",
        "## Recommendations",
        "",
    ])
    for recommendation in result["recommendations"]:
        lines.append(f"- {recommendation}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose memory pressure without remediation.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    result = diagnose()
    print(stable_json({
        "memory_pressure_report": str(REPORT_MD.relative_to(ROOT)),
        "memory_used_percent": result["memory_fields"]["used_percent"],
        "memory_health": result["adjusted_scoring"]["score"],
        "artifact_detected": result["legacy_scoring_artifact"]["detected"],
        "true_risk": result["risk_assessment"]["true_risk"],
        "recommendations_only": True,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
