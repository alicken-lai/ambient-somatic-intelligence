"""
Memory TTL (Time-To-Live) Manager — Phase 1 of Memory Architecture Refactor.

Manages the lifecycle of memory records:
  - Scratchpad: 24h TTL, then summarize → archive
  - Episodic: 30d TTL for low-relevance records → archive
  - Archive: permanent cold storage (read-only)

Operations:
  sweep     — Run TTL enforcement on scratchpad and episodic layers
  stats     — Show TTL status and upcoming expirations
  --dry-run — Preview what would be cleaned without modifying files
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
MEMORY_DIR = AMBIENT_ROOT / "memory"

TTL_CONFIG = {
    "scratchpad": timedelta(hours=24),
    "episodic": timedelta(days=30),
}

ARCHIVE_DIR = MEMORY_DIR / "archive"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def is_expired(record: dict[str, Any], ttl: timedelta) -> bool:
    """Check if a record has exceeded its TTL."""
    ts = parse_timestamp(record.get("timestamp", ""))
    if ts is None:
        return False
    return (utc_now() - ts) > ttl


def sweep_layer(
    layer: str,
    ttl: timedelta,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Sweep a memory layer, moving expired records to archive.

    Returns summary of actions taken.
    """
    layer_file = MEMORY_DIR / layer / "records.jsonl"
    if not layer_file.exists():
        return {"layer": layer, "total": 0, "expired": 0, "kept": 0}

    kept: list[dict[str, Any]] = []
    expired: list[dict[str, Any]] = []

    with layer_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if is_expired(record, ttl):
                expired.append(record)
            else:
                kept.append(record)

    if not dry_run and expired:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        archive_file = ARCHIVE_DIR / f"{layer}_archived.jsonl"
        with archive_file.open("a", encoding="utf-8") as f:
            for record in expired:
                record["_archived_at"] = utc_now().isoformat()
                record["_archived_from"] = layer
                f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

        with layer_file.open("w", encoding="utf-8") as f:
            for record in kept:
                f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    return {
        "layer": layer,
        "total": len(kept) + len(expired),
        "expired": len(expired),
        "kept": len(kept),
        "ttl_hours": ttl.total_seconds() / 3600,
        "dry_run": dry_run,
    }


def run_sweep(dry_run: bool = False) -> dict[str, Any]:
    """Run TTL sweep across all configured layers."""
    results: list[dict[str, Any]] = []
    total_expired = 0

    for layer, ttl in TTL_CONFIG.items():
        result = sweep_layer(layer, ttl, dry_run=dry_run)
        results.append(result)
        total_expired += result["expired"]

    return {
        "status": "completed",
        "timestamp": utc_now().isoformat(),
        "dry_run": dry_run,
        "total_expired": total_expired,
        "layers": results,
    }


def ttl_stats() -> dict[str, Any]:
    """Show TTL status for all layers."""
    now = utc_now()
    stats: dict[str, Any] = {"timestamp": now.isoformat(), "layers": {}}

    for layer, ttl in TTL_CONFIG.items():
        layer_file = MEMORY_DIR / layer / "records.jsonl"
        if not layer_file.exists():
            stats["layers"][layer] = {"count": 0, "expired": 0, "expiring_soon": 0}
            continue

        count = 0
        expired = 0
        expiring_soon = 0

        with layer_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                count += 1
                ts = parse_timestamp(record.get("timestamp", ""))
                if ts is None:
                    continue

                age = now - ts
                if age > ttl:
                    expired += 1
                elif age > (ttl * 0.8):
                    expiring_soon += 1

        stats["layers"][layer] = {
            "count": count,
            "expired": expired,
            "expiring_soon": expiring_soon,
            "ttl_hours": ttl.total_seconds() / 3600,
        }

    archive_file = ARCHIVE_DIR / "scratchpad_archived.jsonl"
    archive_count = 0
    if archive_file.exists():
        with archive_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    archive_count += 1

    stats["archive"] = {"total_archived": archive_count}

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Memory TTL Manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sweep_p = sub.add_parser("sweep")
    sweep_p.add_argument("--dry-run", action="store_true")

    sub.add_parser("stats")

    args = parser.parse_args()

    if args.cmd == "sweep":
        result = run_sweep(dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(ttl_stats(), indent=2))
