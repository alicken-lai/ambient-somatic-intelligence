#!/usr/bin/env python3
"""Generate v0.4.4 migration audit artifacts (unknown surface + file write status)."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
INVENTORY = OUT_DIR / "legacy_mutation_inventory.json"

UNKNOWN_DISPOSITION = {
    "SAFE": lambda e: e.get("risk_score", 1) < 0.4,
    "MIGRATE": lambda e: e.get("risk_score", 0) >= 0.5,
    "DEPRECATED": lambda e: "replay/" in e.get("path", "") or "telemetry/" in e.get("path", ""),
    "EXPERIMENTAL": lambda e: "sandbox" in e.get("path", "").lower(),
}


def classify_unknown(entry: dict) -> str:
    for label, pred in UNKNOWN_DISPOSITION.items():
        if pred(entry):
            return label
    return "MIGRATE"


def main() -> None:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    entries = inventory.get("entries", [])
    unknowns = [e for e in entries if e.get("category") == "UNKNOWN"]

    classified = []
    for entry in unknowns:
        classified.append({**entry, "disposition": classify_unknown(entry)})

    by_disp = {k: 0 for k in UNKNOWN_DISPOSITION}
    by_disp.update(Counter(c["disposition"] for c in classified))
    unknown_report = {
        "version": "0.4.4",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "unknown_count": len(classified),
        "by_disposition": by_disp,
        "entries": classified,
    }
    (OUT_DIR / "unknown_mutation_report.json").write_text(
        json.dumps(unknown_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    file_writes = [e for e in entries if e.get("category") == "FILE_WRITE"]
    migrated = [e for e in file_writes if e.get("migrated")]
    fw_report = {
        "version": "0.4.4",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_file_writes": len(file_writes),
        "migrated_count": len(migrated),
        "remaining_count": len(file_writes) - len(migrated),
        "critical_modules_with_guard": [
            "governance/audit_log.py",
            "memory/memory_kernel.py",
        ],
        "guard_infrastructure": "kernel/isolation/guarded_file_writer.py",
        "high_risk_remaining": [
            e["path"]
            for e in file_writes
            if e.get("risk_level") == "high" and not e.get("migrated")
        ][:25],
    }
    (OUT_DIR / "file_write_migration_report.json").write_text(
        json.dumps(fw_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"unknown={len(classified)} file_write={len(file_writes)}")


if __name__ == "__main__":
    main()
