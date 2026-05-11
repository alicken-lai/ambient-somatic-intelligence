#!/usr/bin/env python3
"""Compute temporal local health scores from telemetry baselines."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, stable_json
from baseline_learn import dedupe_telemetry, telemetry_from_dmn, telemetry_from_snapshots
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
BASELINE_JSON = ROOT / "guardian" / "baselines" / "telemetry_baseline.json"
INCIDENT_INDEX = ROOT / "guardian" / "incidents" / "index.json"
HEALTH_DIR = ROOT / "guardian" / "health"
HEALTH_JSON = HEALTH_DIR / "health_scores.json"
HEALTH_REPORT = HEALTH_DIR / "health_report.md"

SUBSYSTEMS = {
    "cpu_health": ["cpu_usage_percent"],
    "memory_health": ["memory_used_percent"],
    "disk_health": ["disk_used_percent"],
    "load_health": ["load_average_1m", "load_average_5m", "load_average_15m"],
    "process_health": ["process_count"],
}

METRIC_PATHS = {
    "cpu_usage_percent": ("cpu_usage_percent",),
    "memory_used_percent": ("memory_usage", "used_percent"),
    "disk_used_percent": ("disk_usage", "used_percent"),
    "load_average_1m": ("load_average", "1m"),
    "load_average_5m": ("load_average", "5m"),
    "load_average_15m": ("load_average", "15m"),
    "process_count": ("process_count",),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def nested_get(record: dict[str, Any], path: tuple[str, ...]) -> float:
    value: Any = record
    for key in path:
        value = value[key]
    return float(value)


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def pressure_score(metric: str, value: float) -> float:
    if metric == "memory_used_percent":
        return clamp(100.0 - max(0.0, value - 80.0) * 3.0)
    if metric == "disk_used_percent":
        return clamp(100.0 - max(0.0, value - 80.0) * 5.0)
    if metric == "cpu_usage_percent":
        return clamp(100.0 - max(0.0, value - 70.0) * 3.0)
    return 100.0


def metric_score(metric: str, value: float, baseline: dict[str, Any]) -> dict[str, Any]:
    mean = float(baseline["mean"])
    stddev = float(baseline["stddev"])
    if stddev <= 0:
        z_score = 0.0 if value <= mean or abs(value - mean) < 0.0001 else 3.0
    else:
        z_score = max(0.0, (value - mean) / stddev)
    deviation_score = clamp(100.0 - z_score * 18.0)
    absolute_score = pressure_score(metric, value)
    score = min(deviation_score, absolute_score)
    return {
        "value": round(value, 4),
        "baseline_mean": round(mean, 4),
        "baseline_stddev": round(stddev, 4),
        "z_score": round(z_score, 4),
        "deviation_score": round(deviation_score, 2),
        "absolute_pressure_score": round(absolute_score, 2),
        "score": round(score, 2),
    }


def incident_links_by_subsystem() -> dict[str, list[dict[str, Any]]]:
    if not INCIDENT_INDEX.exists():
        return {name: [] for name in SUBSYSTEMS}
    index = load_json(INCIDENT_INDEX)
    links: dict[str, list[dict[str, Any]]] = {name: [] for name in SUBSYSTEMS}
    for incident in index.get("incidents", []):
        for anomaly in incident.get("anomalies", []):
            rule = str(anomaly.get("rule", ""))
            targets: list[str] = []
            if "cpu" in rule:
                targets.append("cpu_health")
            if "memory" in rule:
                targets.append("memory_health")
            if "disk" in rule:
                targets.append("disk_health")
            if "container" in rule or "prometheus" in rule or "grafana" in rule:
                targets.append("process_health")
            for target in targets:
                links[target].append({
                    "incident": incident.get("incident"),
                    "rule": rule,
                    "severity": anomaly.get("severity"),
                    "timestamp": incident.get("timestamp"),
                })
    return links


def compute_score_for_record(record: dict[str, Any], baseline: dict[str, Any], links: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    subsystem_scores: dict[str, Any] = {}
    for subsystem, metrics in SUBSYSTEMS.items():
        metric_scores = []
        for metric in metrics:
            value = nested_get(record, METRIC_PATHS[metric])
            metric_scores.append({metric: metric_score(metric, value, baseline["metrics"][metric]["baseline"])})
        score = sum(next(iter(item.values()))["score"] for item in metric_scores) / len(metric_scores)
        incident_penalty = min(10.0, 3.0 * len(links.get(subsystem, [])))
        subsystem_scores[subsystem] = {
            "score": round(clamp(score - incident_penalty), 2),
            "raw_score": round(score, 2),
            "incident_penalty": incident_penalty,
            "metrics": metric_scores,
            "incident_links": links.get(subsystem, []),
        }
    overall = sum(item["score"] for item in subsystem_scores.values()) / len(subsystem_scores)
    return {
        "timestamp": record.get("timestamp"),
        "source": record.get("_source"),
        "path": record.get("_path"),
        "subsystems": subsystem_scores,
        "health_score": round(clamp(overall), 2),
    }


def detect_trend(history: list[dict[str, Any]], window: int = 5) -> str:
    if len(history) < 3:
        return "stable"
    sample = history[-window:]
    first = sample[0]["health_score"]
    last = sample[-1]["health_score"]
    delta = last - first
    if delta >= 3:
        return "improving"
    if delta <= -3:
        return "degrading"
    return "stable"


def recommendations(current: dict[str, Any], trend: str) -> list[str]:
    recs: list[str] = []
    if trend == "degrading":
        recs.append("Review recent local workload before expanding CUA activity.")
    for name, data in current["subsystems"].items():
        if data["score"] < 70:
            recs.append(f"Observe {name}; score is below 70.")
        if data["incident_links"]:
            recs.append(f"Keep {name} linked to incident memory during future reflex checks.")
    if not recs:
        recs.append("No corrective action recommended; continue temporal observation.")
    return sorted(set(recs))


def write_report(result: dict[str, Any]) -> None:
    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    HEALTH_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    current = result["current"]
    lines = [
        "# Temporal Health Score Report",
        "",
        f"- generated_at: {result['generated_at']}",
        f"- telemetry_count: {result['telemetry_count']}",
        f"- current_timestamp: {current['timestamp']}",
        f"- overall_health_score: {current['health_score']}",
        f"- trend: {result['trend']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Subsystems",
        "",
        "| Subsystem | Score | Raw Score | Incident Penalty | Incident Links |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, data in current["subsystems"].items():
        lines.append(f"| {name} | {data['score']} | {data['raw_score']} | {data['incident_penalty']} | {len(data['incident_links'])} |")
    lines.extend(["", "## Recent History", "", "| Timestamp | Health Score |", "| --- | ---: |"])
    for item in result["history"][-10:]:
        lines.append(f"| {item['timestamp']} | {item['health_score']} |")
    lines.extend(["", "## Recommendations", ""])
    for rec in result["recommendations"]:
        lines.append(f"- {rec}")
    HEALTH_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_health_scoring() -> dict[str, Any]:
    records = dedupe_telemetry(telemetry_from_snapshots() + telemetry_from_dmn())
    if len(records) < 20:
        raise RuntimeError(f"at least 20 telemetry snapshots required, found {len(records)}")
    baseline = load_json(BASELINE_JSON)
    links = incident_links_by_subsystem()
    history = [compute_score_for_record(record, baseline, links) for record in records]
    trend = detect_trend(history)
    current = history[-1]
    result = {
        "generated_at": utc_now(),
        "telemetry_count": len(records),
        "baseline": str(BASELINE_JSON.relative_to(ROOT)),
        "history": history,
        "current": current,
        "trend": trend,
        "recommendations": recommendations(current, trend),
        "recommendations_only": True,
    }
    write_report(result)
    memory = {
        "health_report": str(HEALTH_REPORT.relative_to(ROOT)),
        "health_scores": str(HEALTH_JSON.relative_to(ROOT)),
        "health_score": current["health_score"],
        "trend": trend,
        "telemetry_count": len(records),
        "recommendations": result["recommendations"],
        "recommendations_only": True,
    }
    append_memory(stable_json(memory), ["guardian", "health-score", "night9"], "health_score")
    log_action("health:score", "completed", "ALLOW", memory)
    return memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute temporal Guardian health score.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_health_scoring()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
