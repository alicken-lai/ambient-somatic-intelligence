#!/usr/bin/env python3
"""Minimal Guardian-gated action router."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from action_log import log_action, stable_json
from guardian_check import classify_action, record_approval
from guardian_check import route_boundary_level


ROOT = Path(__file__).resolve().parents[1]


ROUTES = {
    "system-info": ["uname", "-a"],
    "uptime": ["uptime"],
    "disk-usage": ["df", "-h", "/"],
    "memory-usage": ["vm_stat"],
    "telemetry-local": [sys.executable, "scripts/sense_local.py", "--append-dmn", "--write-snapshot"],
    "vision-capture": [sys.executable, "scripts/vision_capture.py"],
    "vision-capture-smoke": [
        sys.executable,
        "scripts/vision_capture.py",
        "--target",
        "desktop",
        "--target",
        "terminal",
        "--target",
        "grafana",
    ],
    "vision-capture-ocr-smoke": [
        sys.executable,
        "scripts/vision_capture.py",
        "--target",
        "terminal",
        "--target",
        "grafana",
        "--target",
        "docker",
    ],
    "cua-guarded-smoke": [sys.executable, "scripts/cua_guarded_action.py", "--smoke"],
    "guardian-reflex-once": [sys.executable, "scripts/guardian_reflex.py", "--once"],
    "incident-recall-build": [sys.executable, "scripts/incident_recall.py", "--build"],
    "baseline-learn-build": [sys.executable, "scripts/baseline_learn.py", "--build"],
    "health-score-build": [sys.executable, "scripts/health_score.py", "--build"],
    "memory-pressure-diagnose": [sys.executable, "scripts/memory_pressure_diagnosis.py", "--build"],
    "circadian-baseline-build": [sys.executable, "scripts/circadian_baseline.py", "--build"],
    "system-state-build": [sys.executable, "scripts/build_system_state.py", "--build"],
    "somatic-dashboard-build": [sys.executable, "scripts/build_somatic_dashboard.py", "--build"],
    "daily-digest-build": [sys.executable, "scripts/daily_digest.py", "--build"],
    "anomaly-explain-build": [sys.executable, "scripts/explain_anomaly.py", "--build"],
    "memory-integrity-audit": [sys.executable, "scripts/memory_integrity_audit.py", "--build"],
    "state-query": [sys.executable, "scripts/query_state.py"],
    "self-reflect-build": [sys.executable, "scripts/self_reflect.py", "--build"],
    "operator-briefing-build": [sys.executable, "scripts/operator_briefing.py", "--build"],
    "approval-packet-build": [sys.executable, "scripts/build_approval_packet.py", "--build"],
    "simulation-build": [sys.executable, "scripts/simulate_incident.py", "--build"],
    "dream-build": [sys.executable, "scripts/guardian_dream.py", "--build"],
    "recalibration-queue-build": [sys.executable, "scripts/build_recalibration_queue.py", "--build"],
}

ROUTE_EXTRA_ARGS = {
    "state-query": {"health", "incidents", "memory", "reflex", "dashboard", "digest", "summary", "--json"},
}


def route_command(name: str, extra_args: list[str] | None = None) -> dict[str, object]:
    if name not in ROUTES:
        result = {"route": name, "status": "unknown_route"}
        log_action(f"route:{name}", "blocked", "BLOCK", result)
        return result

    extra_args = extra_args or []
    if name == "state-query" and not extra_args:
        extra_args = ["summary"]
    allowed_extra = ROUTE_EXTRA_ARGS.get(name)
    if extra_args and allowed_extra is None:
        result = {"route": name, "status": "unsupported_args", "args": extra_args}
        log_action(f"route:{name}", "blocked", "BLOCK", result)
        return result
    invalid_args = [arg for arg in extra_args if allowed_extra is not None and arg not in allowed_extra]
    if invalid_args:
        result = {"route": name, "status": "invalid_args", "args": invalid_args}
        log_action(f"route:{name}", "blocked", "BLOCK", result)
        return result

    command = ROUTES[name] + extra_args
    action = " ".join(command)
    boundary_level = route_boundary_level(name)
    guardian = classify_action(action, name)
    guardian["boundary_level"] = boundary_level
    if guardian["risk"] == "BLOCK":
        log_action(action, "blocked", "BLOCK", guardian)
        return {"route": name, "guardian": guardian, "status": "blocked"}

    approval = None
    if guardian["risk"] == "REVIEW_REQUIRED":
        approval = record_approval(action, str(guardian["risk"]), "router:auto-record")

    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    status = "completed" if completed.returncode == 0 else "failed"
    detail = {
        "route": name,
        "boundary_level": boundary_level,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "approval": approval,
    }
    log_action(action, status, str(guardian["risk"]), detail)
    return {"route": name, "guardian": guardian, "status": status, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description="Route local actions through Guardian.")
    parser.add_argument("route", choices=sorted(ROUTES))
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    result = route_command(args.route, args.args)
    print(stable_json(result))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
