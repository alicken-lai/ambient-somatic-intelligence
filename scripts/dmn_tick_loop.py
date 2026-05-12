#!/usr/bin/env python3
"""Autonomous local-only DMN telemetry tick loop."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, stable_json
from build_system_state import build_system_state
from guardian_check import classify_action
from remember import append_memory
from sense_local import collect_snapshot, write_snapshot


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "state" / "daemon"
STATUS_JSON = RUN_DIR / "dmn_tick_status.json"
LOCK_FILE = RUN_DIR / "dmn_tick_loop.lock"
ROUTE = "persistent-nervous-system-build"
TAGS = ["night35", "telemetry", "autonomous", "local-only"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_status(status: dict[str, Any]) -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def guardian_allow(action: str) -> dict[str, Any]:
    result = classify_action(action, ROUTE)
    if result.get("risk") != "ALLOW":
        raise RuntimeError(f"Guardian blocked tick action: {stable_json(result)}")
    return result


def tick() -> dict[str, Any]:
    action = "autonomous local telemetry DMN tick: collect local telemetry, append DMN, rebuild system_state"
    guardian = guardian_allow(action)
    snapshot = collect_snapshot()
    snapshot_path = write_snapshot(snapshot)
    memory = {
        "type": "autonomous_dmn_tick",
        "route": ROUTE,
        "recommendations_only": True,
        "external_actions_enabled": False,
        "interactive_cua_enabled": False,
        "telemetry_snapshot": str(snapshot_path.relative_to(ROOT)),
        "telemetry": {
            "timestamp": snapshot["timestamp"],
            "cpu_usage_percent": snapshot["cpu_usage_percent"],
            "memory_used_percent": snapshot["memory_usage"]["used_percent"],
            "disk_used_percent": snapshot["disk_usage"]["used_percent"],
            "process_count": snapshot["process_count"],
            "load_average": snapshot["load_average"],
        },
        "guardian": guardian,
    }
    record = append_memory(stable_json(memory), TAGS, "night35-dmn-tick")
    state_summary = build_system_state()
    status = {
        "status": "ok",
        "last_tick_at": utc_now(),
        "last_dmn_timestamp": record["timestamp"],
        "last_snapshot": str(snapshot_path.relative_to(ROOT)),
        "system_state": state_summary,
        "external_actions_enabled": False,
        "interactive_cua_enabled": False,
    }
    write_status(status)
    log_action("night35:dmn-tick", "completed", "ALLOW", status)
    return status


def run_loop(interval: int) -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open("w", encoding="utf-8") as lock:
        try:
            import fcntl

            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            write_status({"status": "already_running", "checked_at": utc_now()})
            return 0

        while True:
            started = time.monotonic()
            try:
                tick()
            except Exception as exc:
                status = {"status": "error", "last_error": str(exc), "last_error_at": utc_now()}
                write_status(status)
                log_action("night35:dmn-tick", "failed", "ALLOW", status)
            elapsed = time.monotonic() - started
            time.sleep(max(1, interval - elapsed))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run autonomous local-only DMN telemetry ticks.")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.once:
        print(stable_json(tick()))
        return 0
    return run_loop(max(1, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
