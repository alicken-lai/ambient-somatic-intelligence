#!/usr/bin/env python3
"""Health check for the persistent Hermes nervous system."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, stable_json
from guardian_check import classify_action


ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / "state" / "daemon" / "dmn_tick_status.json"
INSTALLED_SHIM = Path.home() / ".hermes" / "mcp_shim" / "mcp_serve.py"
ROUTE = "persistent-nervous-system-build"
DMN_FILE = ROOT / "memory" / "dmn.jsonl"
SYSTEM_STATE = ROOT / "state" / "system_state.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def launchd_state(label: str) -> dict[str, Any]:
    uid = str(run(["id", "-u"]).stdout.strip())
    result = run(["launchctl", "print", f"gui/{uid}/{label}"])
    if result.returncode != 0:
        return {"label": label, "loaded": False, "detail": result.stderr.strip() or result.stdout.strip()}
    state = "unknown"
    pid = None
    last_exit_code = None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("state = "):
            state = stripped.split("=", 1)[1].strip()
        if stripped.startswith("pid = "):
            pid = stripped.split("=", 1)[1].strip()
        if stripped.startswith("last exit code = "):
            last_exit_code = stripped.split("=", 1)[1].strip()
    return {
        "label": label,
        "loaded": True,
        "state": state,
        "pid": pid,
        "last_exit_code": last_exit_code,
    }


def status_file_health(max_age_seconds: int) -> dict[str, Any]:
    if not STATUS_JSON.exists():
        return {"exists": False, "fresh": False, "path": str(STATUS_JSON.relative_to(ROOT))}
    data = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
    mtime_age = time.time() - STATUS_JSON.stat().st_mtime
    return {
        "exists": True,
        "fresh": mtime_age <= max_age_seconds,
        "age_seconds": round(mtime_age, 2),
        "path": str(STATUS_JSON.relative_to(ROOT)),
        "status": data,
    }


def mcp_reload_health() -> dict[str, Any]:
    if not INSTALLED_SHIM.exists():
        return {"installed_shim": str(INSTALLED_SHIM), "memory_recall_visible": False}
    text = INSTALLED_SHIM.read_text(encoding="utf-8")
    return {
        "installed_shim": str(INSTALLED_SHIM),
        "memory_recall_visible": "def memory_recall" in text,
    }


def dmn_state_consistency() -> dict[str, Any]:
    actual_count = 0
    last_record: dict[str, Any] | None = None
    if DMN_FILE.exists():
        with DMN_FILE.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                actual_count += 1
                last_record = json.loads(line)

    state_count = None
    if SYSTEM_STATE.exists():
        state = json.loads(SYSTEM_STATE.read_text(encoding="utf-8"))
        state_count = state.get("dmn_append_count")

    return {
        "actual_dmn_count": actual_count,
        "system_state_dmn_append_count": state_count,
        "consistent": state_count == actual_count,
        "last_dmn_append": last_record,
    }


def health(max_age_seconds: int = 180) -> dict[str, Any]:
    guardian = classify_action("persistent nervous system local daemon health check", ROUTE)
    result = {
        "checked_at": utc_now(),
        "guardian": guardian,
        "hermes_gateway": launchd_state("ai.hermes.gateway"),
        "dmn_tick_loop": launchd_state("ai.ambient-os.dmn-tick"),
        "dmn_tick_status": status_file_health(max_age_seconds),
        "dmn_state_consistency": dmn_state_consistency(),
        "mcp": mcp_reload_health(),
        "external_actions_enabled": False,
        "interactive_cua_enabled": False,
    }
    result["ok"] = (
        guardian.get("risk") == "ALLOW"
        and result["dmn_tick_status"].get("fresh") is True
        and result["dmn_state_consistency"].get("consistent") is True
        and result["mcp"].get("memory_recall_visible") is True
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check persistent nervous system health.")
    parser.add_argument("--max-age-seconds", type=int, default=180)
    args = parser.parse_args()
    result = health(args.max_age_seconds)
    log_action("night35:persistent-health", "completed" if result["ok"] else "warning", "ALLOW", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
