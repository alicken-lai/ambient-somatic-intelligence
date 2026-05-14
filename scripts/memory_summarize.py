"""
Telemetry Summarizer — Phase 1 of Memory Architecture Refactor.

Aggregates scratchpad telemetry ticks into hourly summaries:
  - 60 raw ticks/hour → 1 summary record/hour (60x reduction)
  - Summary includes: avg/max/min for CPU, memory, disk, load
  - Anomalies (spikes) are preserved individually in episodic layer
  - Summaries are stored in semantic layer (stable system knowledge)

Operations:
  summarize  — Aggregate current scratchpad into hourly summaries
  --dry-run  — Preview without writing
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
MEMORY_DIR = AMBIENT_ROOT / "memory"
SCRATCHPAD_FILE = MEMORY_DIR / "scratchpad" / "records.jsonl"
SEMANTIC_FILE = MEMORY_DIR / "semantic" / "records.jsonl"
EPISODIC_FILE = MEMORY_DIR / "episodic" / "records.jsonl"

CPU_SPIKE_THRESHOLD = 80.0
MEM_SPIKE_THRESHOLD = 85.0
LOAD_SPIKE_THRESHOLD = 8.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def hour_key(dt: datetime) -> str:
    """Round datetime down to hour for grouping."""
    return dt.strftime("%Y-%m-%dT%H:00:00+00:00")


def extract_telemetry(record: dict[str, Any]) -> dict[str, float] | None:
    """Extract numeric telemetry from a scratchpad record."""
    content = record.get("content", "")
    if isinstance(content, str):
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return None
    elif isinstance(content, dict):
        data = content
    else:
        return None

    telemetry = data.get("telemetry", {})
    if not telemetry:
        return None

    return {
        "cpu": float(telemetry.get("cpu_usage_percent", 0)),
        "memory": float(telemetry.get("memory_used_percent", 0)),
        "disk": float(telemetry.get("disk_used_percent", 0)),
        "load_1m": float(telemetry.get("load_average", [0])[0]) if isinstance(telemetry.get("load_average"), list) else 0,
        "processes": int(telemetry.get("process_count", 0)),
    }


def is_anomaly(metrics: dict[str, float]) -> bool:
    """Check if a telemetry reading is anomalous."""
    return (
        metrics.get("cpu", 0) > CPU_SPIKE_THRESHOLD
        or metrics.get("memory", 0) > MEM_SPIKE_THRESHOLD
        or metrics.get("load_1m", 0) > LOAD_SPIKE_THRESHOLD
    )


def aggregate_hour(readings: list[dict[str, float]]) -> dict[str, Any]:
    """Aggregate a list of telemetry readings into a summary."""
    if not readings:
        return {}

    keys = ["cpu", "memory", "disk", "load_1m", "processes"]
    summary: dict[str, Any] = {"sample_count": len(readings)}

    for key in keys:
        values = [r.get(key, 0) for r in readings]
        summary[key] = {
            "avg": round(sum(values) / len(values), 2),
            "max": round(max(values), 2),
            "min": round(min(values), 2),
        }

    return summary


def summarize_scratchpad(dry_run: bool = False) -> dict[str, Any]:
    """
    Read scratchpad telemetry, group by hour, create summaries.

    Returns stats about what was summarized.
    """
    if not SCRATCHPAD_FILE.exists():
        return {"status": "no_data", "message": "Scratchpad file not found"}

    hourly_readings: dict[str, list[dict[str, float]]] = defaultdict(list)
    anomalies: list[dict[str, Any]] = []
    non_telemetry: list[dict[str, Any]] = []
    total_records = 0

    with SCRATCHPAD_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            total_records += 1
            ts = parse_timestamp(record.get("timestamp", ""))
            metrics = extract_telemetry(record)

            if metrics is None:
                non_telemetry.append(record)
                continue

            if ts is None:
                non_telemetry.append(record)
                continue

            hk = hour_key(ts)
            hourly_readings[hk].append(metrics)

            if is_anomaly(metrics):
                anomalies.append({
                    "timestamp": record.get("timestamp", ""),
                    "metrics": metrics,
                    "source": record.get("source", ""),
                })

    summaries: list[dict[str, Any]] = []
    for hour, readings in sorted(hourly_readings.items()):
        summary = aggregate_hour(readings)
        summary_record = {
            "timestamp": hour,
            "source": "telemetry-summarizer",
            "tags": ["telemetry", "hourly-summary", "system-health"],
            "content": json.dumps({
                "type": "hourly_telemetry_summary",
                "hour": hour,
                "summary": summary,
            }, ensure_ascii=False),
            "_layer": "semantic",
        }
        summaries.append(summary_record)

    if dry_run:
        return {
            "status": "dry_run",
            "total_scratchpad_records": total_records,
            "telemetry_records": sum(len(r) for r in hourly_readings.values()),
            "hours_covered": len(hourly_readings),
            "summaries_to_create": len(summaries),
            "anomalies_detected": len(anomalies),
            "non_telemetry_kept": len(non_telemetry),
        }

    MEMORY_DIR.joinpath("semantic").mkdir(parents=True, exist_ok=True)
    with SEMANTIC_FILE.open("a", encoding="utf-8") as f:
        for record in summaries:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    if anomalies:
        MEMORY_DIR.joinpath("episodic").mkdir(parents=True, exist_ok=True)
        with EPISODIC_FILE.open("a", encoding="utf-8") as f:
            for anomaly in anomalies:
                anomaly_record = {
                    "timestamp": anomaly["timestamp"],
                    "source": "telemetry-summarizer",
                    "tags": ["telemetry", "anomaly", "spike"],
                    "content": json.dumps({
                        "type": "telemetry_anomaly",
                        "metrics": anomaly["metrics"],
                        "thresholds": {
                            "cpu": CPU_SPIKE_THRESHOLD,
                            "memory": MEM_SPIKE_THRESHOLD,
                            "load": LOAD_SPIKE_THRESHOLD,
                        },
                    }, ensure_ascii=False),
                    "_layer": "episodic",
                }
                f.write(json.dumps(anomaly_record, ensure_ascii=False, sort_keys=True) + "\n")

    with SCRATCHPAD_FILE.open("w", encoding="utf-8") as f:
        for record in non_telemetry:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    return {
        "status": "completed",
        "timestamp": utc_now(),
        "total_scratchpad_records": total_records,
        "telemetry_summarized": sum(len(r) for r in hourly_readings.values()),
        "hours_covered": len(hourly_readings),
        "summaries_created": len(summaries),
        "anomalies_preserved": len(anomalies),
        "non_telemetry_kept": len(non_telemetry),
        "scratchpad_reduced_to": len(non_telemetry),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Telemetry Summarizer")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = summarize_scratchpad(dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
