#!/usr/bin/env python3
"""Run scheduled DMN reflection and governance maintenance cycles."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, stable_json


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs" / "dmn_reflection_cycle"

CYCLES: dict[str, list[list[str]]] = {
    "hourly": [
        ["scripts/memory_summarize.py"],
        ["scripts/build_system_state.py", "--build"],
    ],
    "daily": [
        ["scripts/baseline_learn.py", "--build"],
        ["scripts/circadian_baseline.py", "--build"],
        ["scripts/health_score.py", "--build"],
        ["scripts/memory_pressure_diagnosis.py", "--build"],
        ["scripts/incident_recall.py", "--build"],
        ["scripts/explain_anomaly.py", "--build"],
        ["scripts/simulate_incident.py", "--build"],
        ["scripts/self_reflect.py", "--build"],
        ["scripts/operator_briefing.py", "--build"],
        ["scripts/guardian_dream.py", "--build"],
        ["scripts/build_recalibration_queue.py", "--build"],
        ["scripts/build_mem_palace.py", "--build"],
        ["scripts/memory_integrity_audit.py", "--build"],
        ["scripts/build_system_state.py", "--build"],
    ],
    "weekly": [
        ["tools/audit_historical_dmn_governance.py"],
        ["tools/propose_dmn_metadata_sidecars.py"],
        ["scripts/memory_integrity_audit.py", "--build"],
        ["scripts/build_mem_palace.py", "--build"],
        ["scripts/build_system_state.py", "--build"],
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_step(command: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["AMBIENT_OS_ROOT"] = str(ROOT)
    started = utc_now()
    completed = subprocess.run(
        [sys.executable, "-B", *command],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": [sys.executable, "-B", *command],
        "started_at": started,
        "finished_at": utc_now(),
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def run_cycle(cycle: str, keep_going: bool = True) -> dict[str, Any]:
    if cycle not in CYCLES:
        raise ValueError(f"unknown cycle: {cycle}")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    steps = []
    status = "completed"
    for command in CYCLES[cycle]:
        result = run_step(command)
        steps.append(result)
        if result["returncode"] != 0:
            status = "partial_failure"
            if not keep_going:
                break
    summary = {
        "cycle": cycle,
        "generated_at": utc_now(),
        "status": status,
        "step_count": len(steps),
        "failed_steps": [
            {
                "command": step["command"],
                "returncode": step["returncode"],
                "stderr_tail": step["stderr_tail"],
            }
            for step in steps
            if step["returncode"] != 0
        ],
        "steps": steps,
        "corrective_actions": "none",
        "recommendations_only": True,
    }
    stamp = summary["generated_at"].replace(":", "").replace("+", "Z")
    log_path = LOG_DIR / f"{cycle}-{stamp}.json"
    log_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log_action(
        "dmn-reflection-cycle:run",
        status,
        "ALLOW" if status == "completed" else "ALLOW_WITH_WARNINGS",
        {
            "cycle": cycle,
            "log": str(log_path.relative_to(ROOT)),
            "failed_steps": len(summary["failed_steps"]),
        },
    )
    return {
        "cycle": cycle,
        "status": status,
        "log": str(log_path.relative_to(ROOT)),
        "step_count": len(steps),
        "failed_steps": summary["failed_steps"],
        "corrective_actions": "none",
        "recommendations_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run scheduled DMN reflection cycles.")
    parser.add_argument("--cycle", choices=sorted(CYCLES), required=True)
    parser.add_argument("--stop-on-failure", action="store_true")
    args = parser.parse_args()
    result = run_cycle(args.cycle, keep_going=not args.stop_on_failure)
    print(stable_json(result))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
