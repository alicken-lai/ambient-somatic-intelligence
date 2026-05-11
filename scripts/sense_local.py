#!/usr/bin/env python3
"""Collect local machine telemetry and optionally append it to DMN."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, stable_json
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "observability" / "snapshots"


def _run(command: list[str]) -> str:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"{command[0]} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _cpu_usage_percent() -> float:
    output = _run(["ps", "-A", "-o", "%cpu="])
    total_process_cpu = sum(float(line.strip()) for line in output.splitlines() if line.strip())
    cpu_count = os.cpu_count() or 1
    return round(max(0.0, min(100.0, total_process_cpu / cpu_count)), 2)


def _memory_usage() -> dict[str, int | float]:
    output = _run(["vm_stat"])
    page_size = 4096
    pages: dict[str, int] = {}
    for line in output.splitlines():
        if "page size of" in line:
            page_size = int(line.split("page size of", 1)[1].split("bytes", 1)[0].strip())
            continue
        key, _, raw_value = line.partition(":")
        if raw_value:
            pages[key.strip()] = int(raw_value.strip().rstrip(".") or "0")
    free_pages = pages.get("Pages free", 0)
    used_pages = (
        pages.get("Pages active", 0)
        + pages.get("Pages inactive", 0)
        + pages.get("Pages speculative", 0)
        + pages.get("Pages wired down", 0)
        + pages.get("Pages occupied by compressor", 0)
    )
    total_bytes = (free_pages + used_pages) * page_size
    used_bytes = used_pages * page_size
    return {
        "total_bytes": total_bytes,
        "used_bytes": used_bytes,
        "free_bytes": free_pages * page_size,
        "used_percent": round((used_bytes / total_bytes) * 100, 2) if total_bytes else 0.0,
    }


def _disk_usage(path: str = "/") -> dict[str, int | float | str]:
    usage = os.statvfs(path)
    total = usage.f_blocks * usage.f_frsize
    free = usage.f_bavail * usage.f_frsize
    used = total - free
    return {
        "path": path,
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
        "used_percent": round((used / total) * 100, 2) if total else 0.0,
    }


def _uptime_seconds() -> int:
    boot_time = int(_run(["sysctl", "-n", "kern.boottime"]).split("sec = ", 1)[1].split(",", 1)[0])
    return int(time.time()) - boot_time


def _process_count() -> int:
    output = _run(["ps", "-axo", "pid="])
    return len([line for line in output.splitlines() if line.strip()])


def collect_snapshot() -> dict[str, Any]:
    load_average = os.getloadavg()
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": os.uname().nodename,
        "cpu_usage_percent": _cpu_usage_percent(),
        "memory_usage": _memory_usage(),
        "disk_usage": _disk_usage("/"),
        "uptime_seconds": _uptime_seconds(),
        "process_count": _process_count(),
        "load_average": {
            "1m": round(load_average[0], 2),
            "5m": round(load_average[1], 2),
            "15m": round(load_average[2], 2),
        },
    }
    validate_snapshot(snapshot)
    return snapshot


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    required = {
        "timestamp",
        "host",
        "cpu_usage_percent",
        "memory_usage",
        "disk_usage",
        "uptime_seconds",
        "process_count",
        "load_average",
    }
    missing = required - set(snapshot)
    if missing:
        raise ValueError(f"missing telemetry fields: {', '.join(sorted(missing))}")
    if not 0 <= float(snapshot["cpu_usage_percent"]) <= 100:
        raise ValueError("cpu_usage_percent outside 0..100")
    if int(snapshot["uptime_seconds"]) < 0:
        raise ValueError("uptime_seconds must be non-negative")
    if int(snapshot["process_count"]) <= 0:
        raise ValueError("process_count must be positive")


def write_snapshot(snapshot: dict[str, Any]) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = snapshot["timestamp"].replace(":", "").replace("+", "Z")
    path = SNAPSHOT_DIR / f"telemetry-{stamp}.json"
    path.write_text(stable_json(snapshot) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect local telemetry as JSON.")
    parser.add_argument("--append-dmn", action="store_true")
    parser.add_argument("--write-snapshot", action="store_true")
    args = parser.parse_args()

    try:
        snapshot = collect_snapshot()
        snapshot_path = write_snapshot(snapshot) if args.write_snapshot else None
        if args.append_dmn:
            append_memory(stable_json(snapshot), ["telemetry", "local", "night2"], "sense_local")
        detail = {"fields": sorted(snapshot), "snapshot": str(snapshot_path.relative_to(ROOT)) if snapshot_path else None}
        log_action("telemetry:collect", "completed", "ALLOW", detail)
        print(stable_json(snapshot))
        return 0
    except Exception as exc:
        log_action("telemetry:collect", "failed", "ALLOW", {"error": str(exc)})
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
