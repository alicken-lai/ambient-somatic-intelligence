"""Run civilization lineage pytest suites repeatedly for determinism audit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = 10
SUITES = [
    "tests/v060",
    "tests/v061",
    "tests/v062",
    "tests/v063",
    "tests/v064",
    "tests/v065",
    "tests/v065b",
    "tests/v065c",
    "tests/v070",
    "tests/v071",
    "tests/v072",
    "tests/v073",
    "tests/v074",
    "tests/v075",
    "tests/v076",
    "tests/v077",
]


def main() -> int:
    results: list[dict] = []
    for run in range(1, RUNS + 1):
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", *SUITES, "-q", "--tb=no"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        results.append(
            {
                "run": run,
                "exit_code": proc.returncode,
                "passed": proc.returncode == 0,
                "tail": proc.stdout.strip().splitlines()[-1] if proc.stdout else "",
            }
        )
        if proc.returncode != 0:
            print(proc.stdout[-2000:], file=sys.stderr)
            print(proc.stderr[-2000:], file=sys.stderr)
            break
    out_path = Path(__file__).resolve().parent / "repeated_execution_matrix.json"
    payload = {
        "runs_requested": RUNS,
        "runs_completed": len(results),
        "all_passed": all(r["passed"] for r in results),
        "results": results,
    }
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
