#!/usr/bin/env python3
"""Learn local telemetry baselines and compare current readings."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, stable_json
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
DMN_FILE = ROOT / "memory" / "dmn.jsonl"
SNAPSHOT_DIR = ROOT / "observability" / "snapshots"
INCIDENT_INDEX = ROOT / "guardian" / "incidents" / "index.json"
BASELINE_DIR = ROOT / "guardian" / "baselines"
BASELINE_JSON = BASELINE_DIR / "telemetry_baseline.json"
REPORT_MD = BASELINE_DIR / "baseline_report.md"

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


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_json_file(path: Path) -> dict[str, Any] | None:
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
    return "cpu_usage_percent" in record and "memory_usage" in record and "disk_usage" in record


def telemetry_from_dmn() -> list[dict[str, Any]]:
    telemetry: list[dict[str, Any]] = []
    for line_number, memory in enumerate(load_jsonl(DMN_FILE), start=1):
        try:
            content = json.loads(str(memory.get("content", "")))
        except json.JSONDecodeError:
            continue
        if not is_telemetry(content):
            continue
        content["_source"] = "dmn"
        content["_dmn_line"] = line_number
        content["_memory_timestamp"] = memory.get("timestamp")
        telemetry.append(content)
    return telemetry


def telemetry_from_snapshots() -> list[dict[str, Any]]:
    telemetry: list[dict[str, Any]] = []
    for path in sorted(SNAPSHOT_DIR.glob("telemetry-*.json")):
        record = load_json_file(path)
        if record and is_telemetry(record):
            record["_source"] = "snapshot"
            record["_path"] = str(path.relative_to(ROOT))
            telemetry.append(record)
    return telemetry


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


def rolling_stats(values: list[float], window: int = 3) -> dict[str, float | int]:
    return stats(values[-window:])


def classify_deviation(current: float, baseline: dict[str, float | int]) -> dict[str, Any]:
    avg = float(baseline["mean"])
    sd = float(baseline["stddev"])
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


def incident_links() -> dict[str, list[dict[str, Any]]]:
    index = load_json_file(INCIDENT_INDEX) or {}
    links: dict[str, list[dict[str, Any]]] = {metric: [] for metric in METRICS}
    for incident in index.get("incidents", []):
        for anomaly in incident.get("anomalies", []):
            rule = str(anomaly.get("rule", ""))
            metric_names: list[str] = []
            if "cpu" in rule:
                metric_names.append("cpu_usage_percent")
            if "memory" in rule:
                metric_names.append("memory_used_percent")
            if "disk" in rule:
                metric_names.append("disk_used_percent")
            for metric in metric_names:
                links[metric].append(
                    {
                        "incident": incident.get("incident"),
                        "rule": rule,
                        "severity": anomaly.get("severity"),
                        "timestamp": incident.get("timestamp"),
                        "recommendation": anomaly.get("recommendation"),
                    }
                )
    return links


def build_baseline(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise RuntimeError("no telemetry records found")
    current = records[-1]
    links = incident_links()
    metrics: dict[str, Any] = {}
    for name, path in METRICS.items():
        values = [value for record in records if (value := nested_get(record, path)) is not None]
        current_value = nested_get(current, path)
        if current_value is None:
            continue
        baseline = stats(values)
        rolling = rolling_stats(values)
        deviation = classify_deviation(current_value, baseline)
        metrics[name] = {
            "baseline": baseline,
            "rolling_window": 3,
            "rolling": rolling,
            "current": current_value,
            "deviation": deviation,
            "incident_links": links.get(name, []),
        }
    max_severity = max(
        (metric["deviation"]["severity"] for metric in metrics.values()),
        key=lambda severity: SEVERITY_RANK[severity],
    )
    return {
        "generated_at": utc_now(),
        "telemetry_count": len(records),
        "current_timestamp": current.get("timestamp"),
        "current_source": current.get("_source"),
        "current_path": current.get("_path"),
        "metrics": metrics,
        "overall_deviation_severity": max_severity,
        "recommendations_only": True,
        "recommendations": recommendations(metrics),
    }


def recommendations(metrics: dict[str, Any]) -> list[str]:
    recs: list[str] = []
    for metric, data in metrics.items():
        severity = data["deviation"]["severity"]
        if severity in {"warning", "critical"}:
            recs.append(f"Review {metric}; current value deviates from learned local baseline.")
        elif data["incident_links"]:
            recs.append(f"Continue observing {metric}; it is linked to prior incident memory.")
    if not recs:
        recs.append("No corrective action recommended; continue collecting local telemetry.")
    return sorted(set(recs))


def write_report(baseline: dict[str, Any]) -> None:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    BASELINE_JSON.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Pattern Threshold Baseline Report",
        "",
        f"- generated_at: {baseline['generated_at']}",
        f"- telemetry_count: {baseline['telemetry_count']}",
        f"- current_timestamp: {baseline['current_timestamp']}",
        f"- overall_deviation_severity: {baseline['overall_deviation_severity']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Metrics",
        "",
        "| Metric | Current | Mean | Min | Max | Stddev | Rolling Mean | Severity | Incident Links |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for name, data in baseline["metrics"].items():
        base = data["baseline"]
        rolling = data["rolling"]
        deviation = data["deviation"]
        lines.append(
            f"| {name} | {deviation['current']} | {base['mean']} | {base['min']} | {base['max']} | "
            f"{base['stddev']} | {rolling['mean']} | {deviation['severity']} | {len(data['incident_links'])} |"
        )
    lines.extend(["", "## Recommendations", ""])
    for rec in baseline["recommendations"]:
        lines.append(f"- {rec}")
    lines.extend(["", "## Incident Links", ""])
    any_links = False
    for name, data in baseline["metrics"].items():
        for link in data["incident_links"]:
            any_links = True
            lines.append(f"- {name}: {link['rule']} in {link['incident']} ({link['severity']})")
    if not any_links:
        lines.append("- No linked incident memory.")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_learning() -> dict[str, Any]:
    records = dedupe_telemetry(telemetry_from_snapshots() + telemetry_from_dmn())
    baseline = build_baseline(records)
    write_report(baseline)
    memory = {
        "baseline": str(BASELINE_JSON.relative_to(ROOT)),
        "report": str(REPORT_MD.relative_to(ROOT)),
        "telemetry_count": baseline["telemetry_count"],
        "overall_deviation_severity": baseline["overall_deviation_severity"],
        "recommendations": baseline["recommendations"],
        "recommendations_only": True,
    }
    append_memory(stable_json(memory), ["guardian", "baseline", "pattern-threshold", "night8"], "baseline_learn")
    log_action("baseline:learn", "completed", "ALLOW", memory)
    return memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Learn adaptive local telemetry baselines.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_learning()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
