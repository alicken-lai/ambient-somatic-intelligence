#!/usr/bin/env python3
"""Build time-aware circadian telemetry baselines."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
DMN_FILE = ROOT / "memory" / "dmn.jsonl"
SNAPSHOT_DIR = ROOT / "observability" / "snapshots"
BASELINE_DIR = ROOT / "guardian" / "baselines"
CIRCADIAN_JSON = BASELINE_DIR / "circadian_baseline.json"
CIRCADIAN_REPORT = BASELINE_DIR / "circadian_report.md"
CALIBRATION_JSON = ROOT / "guardian" / "incidents" / "reflex_confidence_calibration.json"

METRICS = {
    "cpu_usage_percent": ("cpu_usage_percent",),
    "memory_used_percent": ("memory_usage", "used_percent"),
    "disk_used_percent": ("disk_usage", "used_percent"),
    "load_average_1m": ("load_average", "1m"),
    "load_average_5m": ("load_average", "5m"),
    "load_average_15m": ("load_average", "15m"),
    "process_count": ("process_count",),
}

SEVERITY_RANK = {"normal": 0, "elevated": 1, "warning": 2, "critical": 3}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_snapshot(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def nested_get(record: dict[str, Any], path: tuple[str, ...]) -> float | None:
    value: Any = record
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_telemetry(record: dict[str, Any]) -> bool:
    return "timestamp" in record and "cpu_usage_percent" in record and "memory_usage" in record and "disk_usage" in record


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def annotate_time(record: dict[str, Any]) -> dict[str, Any]:
    dt = parse_timestamp(str(record["timestamp"]))
    weekday = dt.strftime("%A").lower()
    record["_time_context"] = {
        "hour_of_day": dt.hour,
        "weekday": weekday,
        "day_type": "weekend" if dt.weekday() >= 5 else "weekday",
        "timestamp": dt.isoformat(),
    }
    return record


def telemetry_from_dmn() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, memory in enumerate(load_jsonl(DMN_FILE), start=1):
        try:
            content = json.loads(str(memory.get("content", "")))
        except json.JSONDecodeError:
            continue
        if is_telemetry(content):
            content["_source"] = "dmn"
            content["_dmn_line"] = line_number
            records.append(annotate_time(content))
    return records


def telemetry_from_snapshots() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(SNAPSHOT_DIR.glob("telemetry-*.json")):
        record = load_snapshot(path)
        if record and is_telemetry(record):
            record["_source"] = "snapshot"
            record["_path"] = str(path.relative_to(ROOT))
            records.append(annotate_time(record))
    return records


def dedupe_telemetry(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_timestamp: dict[str, dict[str, Any]] = {}
    for record in records:
        timestamp = str(record.get("timestamp", ""))
        existing = by_timestamp.get(timestamp)
        if existing is None or existing.get("_source") != "snapshot":
            by_timestamp[timestamp] = record
    return sorted(by_timestamp.values(), key=lambda item: str(item.get("timestamp", "")))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / len(values))


def stats(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "mean": round(mean(values), 4),
        "min": round(min(values), 4) if values else 0.0,
        "max": round(max(values), 4) if values else 0.0,
        "stddev": round(stddev(values), 4),
    }


def classify_deviation(current: float, baseline: dict[str, float | int]) -> dict[str, Any]:
    avg = float(baseline.get("mean", 0.0))
    sd = float(baseline.get("stddev", 0.0))
    delta = current - avg
    if sd > 0:
        z_score = delta / sd
    else:
        z_score = 0.0 if abs(delta) < 0.0001 else math.inf
    abs_z = abs(z_score) if math.isfinite(z_score) else math.inf
    if abs_z >= 3:
        severity = "critical"
    elif abs_z >= 2:
        severity = "warning"
    elif abs_z >= 1:
        severity = "elevated"
    else:
        severity = "normal"
    return {
        "current": round(current, 4),
        "delta_from_mean": round(delta, 4),
        "z_score": round(z_score, 4) if math.isfinite(z_score) else "inf",
        "severity": severity,
    }


def metric_stats(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for metric, path in METRICS.items():
        values = [value for record in records if (value := nested_get(record, path)) is not None]
        output[metric] = stats(values)
    return output


def grouped_stats(records: list[dict[str, Any]], key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        value = str(record["_time_context"][key])
        groups[value].append(record)
    return {name: metric_stats(group) for name, group in sorted(groups.items())}


def time_adjusted_confidence(base_confidence: float, severity: str, bucket_count: int) -> dict[str, Any]:
    adjustment = {"normal": 0.1, "elevated": 0.0, "warning": -0.05, "critical": -0.1}.get(severity, 0.0)
    if bucket_count < 3:
        adjustment -= 0.05
    adjusted = min(1.0, max(0.0, round(base_confidence + adjustment, 4)))
    return {
        "base_confidence": base_confidence,
        "adjusted_confidence": adjusted,
        "adjustment": round(adjustment, 4),
        "reason": f"time-aware severity={severity}; comparison bucket count={bucket_count}",
    }


def recommendations(overall: str) -> list[str]:
    if overall in {"warning", "critical"}:
        return ["Continue observing current telemetry against the selected time-aware baseline."]
    return ["No corrective action recommended; continue collecting circadian telemetry."]


def build_circadian_baseline() -> dict[str, Any]:
    records = dedupe_telemetry(telemetry_from_snapshots() + telemetry_from_dmn())
    if not records:
        raise RuntimeError("no telemetry records found")
    current = records[-1]
    context = current["_time_context"]
    hour_records = [record for record in records if record["_time_context"]["hour_of_day"] == context["hour_of_day"]]
    weekday_records = [record for record in records if record["_time_context"]["weekday"] == context["weekday"]]
    day_type_records = [record for record in records if record["_time_context"]["day_type"] == context["day_type"]]
    comparison_basis = "hour_of_day"
    matching_records = hour_records
    if len(matching_records) < 3 and len(weekday_records) >= 3:
        comparison_basis = "weekday"
        matching_records = weekday_records
    elif len(matching_records) < 3 and len(day_type_records) >= 3:
        comparison_basis = "day_type"
        matching_records = day_type_records
    elif len(matching_records) < 3:
        comparison_basis = "all_telemetry"
        matching_records = records
    matching_stats = metric_stats(matching_records)

    metrics: dict[str, Any] = {}
    for metric, path in METRICS.items():
        current_value = nested_get(current, path)
        if current_value is None:
            continue
        baseline = matching_stats[metric]
        metrics[metric] = {
            "current": current_value,
            "baseline": baseline,
            "deviation": classify_deviation(current_value, baseline),
        }
    overall = max(
        (data["deviation"]["severity"] for data in metrics.values()),
        key=lambda severity: SEVERITY_RANK[severity],
    )
    calibration = load_json(CALIBRATION_JSON)
    latest_anomaly = (calibration.get("anomalies") or [{}])[-1]
    base_confidence = float(latest_anomaly.get("confidence") or 0.0)
    return {
        "generated_at": utc_now(),
        "telemetry_count": len(records),
        "current_timestamp": current.get("timestamp"),
        "current_source": current.get("_source"),
        "current_path": current.get("_path"),
        "time_context": context,
        "group_counts": {
            "matching_hour": len(hour_records),
            "matching_weekday": len(weekday_records),
            "matching_day_type": len(day_type_records),
        },
        "baselines": {
            "hour_of_day": grouped_stats(records, "hour_of_day"),
            "weekday": grouped_stats(records, "weekday"),
            "day_type": grouped_stats(records, "day_type"),
        },
        "comparison_basis": comparison_basis,
        "metrics": metrics,
        "overall_deviation_severity": overall,
        "time_adjusted_reflex_confidence": time_adjusted_confidence(base_confidence, overall, len(matching_records)),
        "corrective_actions": "none",
        "recommendations_only": True,
        "recommendations": recommendations(overall),
    }


def write_report(baseline: dict[str, Any]) -> None:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    CIRCADIAN_JSON.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    context = baseline["time_context"]
    lines = [
        "# Circadian Baseline Report",
        "",
        f"- generated_at: {baseline['generated_at']}",
        f"- telemetry_count: {baseline['telemetry_count']}",
        f"- current_timestamp: {baseline['current_timestamp']}",
        f"- time_context.hour_of_day: {context['hour_of_day']}",
        f"- time_context.weekday: {context['weekday']}",
        f"- time_context.day_type: {context['day_type']}",
        f"- overall_deviation_severity: {baseline['overall_deviation_severity']}",
        f"- time_adjusted_reflex_confidence: {baseline['time_adjusted_reflex_confidence']['adjusted_confidence']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Current Time-Aware Comparison",
        "",
        f"Comparison basis: `{baseline['comparison_basis']}`",
        "",
        "| Metric | Current | Baseline Mean | Count | Stddev | Severity | Z Score |",
        "| --- | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for metric, data in baseline["metrics"].items():
        base = data["baseline"]
        deviation = data["deviation"]
        lines.append(
            f"| {metric} | {deviation['current']} | {base['mean']} | {base['count']} | "
            f"{base['stddev']} | {deviation['severity']} | {deviation['z_score']} |"
        )
    lines.extend(["", "## Group Counts", ""])
    for key, value in baseline["group_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Recommendations", ""])
    for recommendation in baseline["recommendations"]:
        lines.append(f"- {recommendation}")
    CIRCADIAN_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_circadian() -> dict[str, Any]:
    baseline = build_circadian_baseline()
    write_report(baseline)
    record_checksum(CIRCADIAN_JSON, "circadian_baseline_build")
    record_checksum(CIRCADIAN_REPORT, "circadian_report_build")
    memory = {
        "circadian_baseline": str(CIRCADIAN_JSON.relative_to(ROOT)),
        "report": str(CIRCADIAN_REPORT.relative_to(ROOT)),
        "time_context": baseline["time_context"],
        "overall_deviation_severity": baseline["overall_deviation_severity"],
        "time_adjusted_reflex_confidence": baseline["time_adjusted_reflex_confidence"],
        "recommendations_only": True,
    }
    append_memory(stable_json(memory), ["guardian", "baseline", "circadian", "night18"], "circadian_baseline")
    log_action("baseline:circadian", "completed", "ALLOW", memory)
    return memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Build circadian telemetry baselines.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_circadian()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
