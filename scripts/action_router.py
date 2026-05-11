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
}


def route_command(name: str) -> dict[str, object]:
    if name not in ROUTES:
        result = {"route": name, "status": "unknown_route"}
        log_action(f"route:{name}", "blocked", "BLOCK", result)
        return result

    command = ROUTES[name]
    action = " ".join(command)
    guardian = classify_action(action)
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
    args = parser.parse_args()
    result = route_command(args.route)
    print(stable_json(result))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
