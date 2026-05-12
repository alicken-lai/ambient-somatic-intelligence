#!/usr/bin/env python3
"""Explain active anomaly and reflex signals from Ambient OS memory."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
STATE_JSON = ROOT / "state" / "system_state.json"
BASELINE_JSON = ROOT / "guardian" / "baselines" / "telemetry_baseline.json"
CIRCADIAN_JSON = ROOT / "guardian" / "baselines" / "circadian_baseline.json"
HEALTH_JSON = ROOT / "guardian" / "health" / "health_scores.json"
INCIDENT_INDEX = ROOT / "guardian" / "incidents" / "index.json"
EXPLANATION_DIR = ROOT / "guardian" / "explanations"
LATEST_EXPLANATION = EXPLANATION_DIR / "latest_anomaly.md"

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
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def nested_get(record: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = record
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def severity_active(value: Any) -> bool:
    return str(value) in {"warning", "critical"}


def classify_deviation(current: Any, baseline_stats: dict[str, Any]) -> dict[str, Any]:
    if current is None:
        return {"current": None, "delta_from_mean": None, "z_score": None, "severity": "unknown"}
    try:
        current_value = float(current)
        mean = float(baseline_stats.get("mean", 0.0))
        stddev = float(baseline_stats.get("stddev", 0.0))
    except (TypeError, ValueError):
        return {"current": current, "delta_from_mean": None, "z_score": None, "severity": "unknown"}
    delta = current_value - mean
    if stddev > 0:
        z_score: float | str = round(delta / stddev, 4)
        abs_z = abs(float(z_score))
    else:
        z_score = 0.0 if abs(delta) < 0.0001 else "inf"
        abs_z = 0.0 if z_score == 0.0 else float("inf")
    if abs_z >= 3:
        severity = "critical"
    elif abs_z >= 2:
        severity = "warning"
    elif abs_z >= 1:
        severity = "elevated"
    else:
        severity = "normal"
    return {
        "current": round(current_value, 4),
        "delta_from_mean": round(delta, 4),
        "z_score": z_score,
        "severity": severity,
    }


def prior_incident_rules(index: dict[str, Any], metric: str) -> list[dict[str, Any]]:
    matches = []
    token = metric.split("_")[0]
    for incident in index.get("incidents", []):
        for anomaly in incident.get("anomalies", []):
            rule = str(anomaly.get("rule", ""))
            if token in rule or (metric == "memory_used_percent" and "memory" in rule):
                matches.append(
                    {
                        "incident": incident.get("incident"),
                        "timestamp": incident.get("timestamp"),
                        "rule": rule,
                        "severity": anomaly.get("severity"),
                        "value": anomaly.get("value"),
                    }
                )
    return matches


def likely_cause(metric: str, flat: dict[str, Any], circadian: dict[str, Any], state: dict[str, Any]) -> str:
    flat_severity = flat.get("deviation", {}).get("severity", "unknown")
    circadian_severity = circadian.get("deviation", {}).get("severity", "unknown")
    circadian_delta = circadian.get("deviation", {}).get("delta_from_mean")
    flat_delta = flat.get("deviation", {}).get("delta_from_mean")
    if metric == "memory_used_percent":
        if circadian_severity in {"warning", "critical"} and isinstance(circadian_delta, (int, float)) and circadian_delta < 0:
            return "memory is lower than the learned weekday pattern, while prior memory incidents keep the reflex cautious"
        return "host memory pressure remains the dominant learned risk"
    if metric == "disk_used_percent":
        return "disk usage is slightly above both broad and time-aware local baselines"
    if metric.startswith("load_average"):
        if isinstance(flat_delta, (int, float)) and flat_delta < 0:
            return "load is lower than the broad learned baseline; circadian context reduces but does not erase the deviation"
        return "load differs from the learned local baseline for this time context"
    if metric == "process_count":
        return "process count differs from learned local process-count behavior"
    if flat_severity != "normal" and circadian_severity == "normal":
        return "the value differs from the broad baseline but matches the current time context"
    if circadian_severity in {"warning", "critical"}:
        return "the value is unusual for this time context"
    if state.get("current_risk_class") == "low_confidence_watch":
        return "reflex confidence remains low because recent incident evidence is weak or time-adjusted"
    return "local telemetry differs from learned baseline behavior"


def health_trend(health: dict[str, Any]) -> str:
    history = health.get("history", [])
    if len(history) < 2:
        return "insufficient health history"
    previous = history[-2].get("health_score")
    current = history[-1].get("health_score")
    return f"{previous} -> {current}"


def active_metric_explanations(
    state: dict[str, Any],
    latest: dict[str, Any],
    baseline: dict[str, Any],
    circadian: dict[str, Any],
    health: dict[str, Any],
    incidents: dict[str, Any],
) -> list[dict[str, Any]]:
    metrics = set()
    for name, data in (baseline.get("metrics") or {}).items():
        observed = nested_get(latest, METRIC_PATHS.get(name, (name,)))
        latest_flat_deviation = classify_deviation(observed, data.get("baseline", {}))
        if severity_active(latest_flat_deviation.get("severity")):
            metrics.add(name)
    for name, data in (circadian.get("metrics") or {}).items():
        if severity_active(data.get("deviation", {}).get("severity")):
            metrics.add(name)
    explanations = []
    for metric in sorted(metrics):
        flat = (baseline.get("metrics") or {}).get(metric, {})
        circ = (circadian.get("metrics") or {}).get(metric, {})
        observed = nested_get(latest, METRIC_PATHS.get(metric, (metric,)))
        flat_deviation = classify_deviation(observed, flat.get("baseline", {}))
        circadian_deviation = classify_deviation(observed, circ.get("baseline", {}))
        prior = prior_incident_rules(incidents, metric)
        explanations.append(
            {
                "metric": metric,
                "observed_value": observed,
                "flat_baseline": {
                    "mean": flat.get("baseline", {}).get("mean"),
                    "stddev": flat.get("baseline", {}).get("stddev"),
                    "severity": flat_deviation.get("severity"),
                    "z_score": flat_deviation.get("z_score"),
                    "delta_from_mean": flat_deviation.get("delta_from_mean"),
                },
                "circadian_baseline": {
                    "comparison_basis": circadian.get("comparison_basis"),
                    "mean": circ.get("baseline", {}).get("mean"),
                    "stddev": circ.get("baseline", {}).get("stddev"),
                    "severity": circadian_deviation.get("severity"),
                    "z_score": circadian_deviation.get("z_score"),
                    "delta_from_mean": circadian_deviation.get("delta_from_mean"),
                    "group_counts": circadian.get("group_counts", {}),
                },
                "confidence": {
                    "base": state.get("base_reflex_confidence"),
                    "time_adjusted": state.get("latest_reflex_confidence"),
                    "class": state.get("current_risk_class"),
                    "reason": (state.get("circadian_deviation") or {})
                    .get("time_adjusted_reflex_confidence", {})
                    .get("reason"),
                },
                "likely_cause": likely_cause(
                    metric,
                    {"deviation": flat_deviation},
                    {"deviation": circadian_deviation},
                    state,
                ),
                "resembles_prior_incidents": bool(prior),
                "prior_incidents": prior,
                "health_history": health_trend(health),
            }
        )
    return explanations


def reflex_explanation(state: dict[str, Any], incidents: dict[str, Any]) -> dict[str, Any] | None:
    confidence = float(state.get("latest_reflex_confidence") or 0.0)
    if confidence > 0.25 and state.get("current_risk_class") != "low_confidence_watch":
        return None
    repeated = state.get("repeated_anomalies", {})
    return {
        "signal": "reflex_confidence",
        "observed_value": confidence,
        "base_confidence": state.get("base_reflex_confidence"),
        "risk_class": state.get("current_risk_class"),
        "circadian_adjustment": (state.get("circadian_deviation") or {}).get("time_adjusted_reflex_confidence", {}),
        "likely_cause": "time-aware warning reduced confidence while prior high-memory incident memory remains present",
        "resembles_prior_incidents": "high_memory_usage" in repeated,
        "prior_incident_count": repeated.get("high_memory_usage", 0),
        "latest_incident": incidents.get("patterns", {}).get("latest_incident"),
    }


def build_explanation() -> dict[str, Any]:
    state = load_json(STATE_JSON)
    if not state:
        raise RuntimeError("state/system_state.json is missing; run system-state-build first")
    latest_path = ROOT / str(state.get("latest_telemetry_snapshot", ""))
    latest = load_json(latest_path)
    baseline = load_json(BASELINE_JSON)
    circadian = load_json(CIRCADIAN_JSON)
    health = load_json(HEALTH_JSON)
    incidents = load_json(INCIDENT_INDEX)
    metric_explanations = active_metric_explanations(state, latest, baseline, circadian, health, incidents)
    reflex = reflex_explanation(state, incidents)
    active_count = len(metric_explanations) + (1 if reflex else 0)
    return {
        "generated_at": utc_now(),
        "active_warning_count": active_count,
        "latest_telemetry": str(latest_path.relative_to(ROOT)) if latest_path.exists() else str(state.get("latest_telemetry_snapshot")),
        "time_context": state.get("time_context", {}),
        "overall_flat_deviation": state.get("baseline_deviation", {}).get("overall_severity"),
        "overall_circadian_deviation": state.get("circadian_deviation", {}).get("overall_severity"),
        "metric_explanations": metric_explanations,
        "reflex_explanation": reflex,
        "corrective_actions": "none",
        "recommendations_only": True,
        "sources": {
            "system_state": str(STATE_JSON.relative_to(ROOT)),
            "latest_telemetry": str(latest_path.relative_to(ROOT)) if latest_path.exists() else str(state.get("latest_telemetry_snapshot")),
            "baseline": str(BASELINE_JSON.relative_to(ROOT)),
            "circadian_baseline": str(CIRCADIAN_JSON.relative_to(ROOT)),
            "health_history": str(HEALTH_JSON.relative_to(ROOT)),
            "incident_memory": str(INCIDENT_INDEX.relative_to(ROOT)),
        },
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    return str(value)


def write_explanation(explanation: dict[str, Any]) -> None:
    EXPLANATION_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Latest Anomaly Explanation",
        "",
        f"- generated_at: {explanation['generated_at']}",
        f"- active_warning_count: {explanation['active_warning_count']}",
        f"- latest_telemetry: {explanation['latest_telemetry']}",
        f"- time_context: {stable_json(explanation['time_context']) if explanation['time_context'] else 'unknown'}",
        f"- overall_flat_deviation: {explanation['overall_flat_deviation']}",
        f"- overall_circadian_deviation: {explanation['overall_circadian_deviation']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Metric Warnings",
        "",
    ]
    if not explanation["metric_explanations"]:
        lines.append("- No active metric warnings.")
    for item in explanation["metric_explanations"]:
        flat = item["flat_baseline"]
        circ = item["circadian_baseline"]
        confidence = item["confidence"]
        lines.extend(
            [
                f"### {item['metric']}",
                "",
                f"- observed_value: {fmt(item['observed_value'])}",
                f"- flat_baseline: mean={fmt(flat['mean'])}, severity={fmt(flat['severity'])}, z={fmt(flat['z_score'])}, delta={fmt(flat['delta_from_mean'])}",
                f"- circadian_baseline: basis={fmt(circ['comparison_basis'])}, mean={fmt(circ['mean'])}, severity={fmt(circ['severity'])}, z={fmt(circ['z_score'])}, delta={fmt(circ['delta_from_mean'])}",
                f"- confidence: base={fmt(confidence['base'])}, time_adjusted={fmt(confidence['time_adjusted'])}, class={fmt(confidence['class'])}",
                f"- confidence_reason: {fmt(confidence['reason'])}",
                f"- likely_cause: {item['likely_cause']}",
                f"- resembles_prior_incidents: {item['resembles_prior_incidents']}",
                f"- health_history: {item['health_history']}",
                "",
            ]
        )
        if item["prior_incidents"]:
            lines.append("Prior incident memory:")
            for prior in item["prior_incidents"]:
                lines.append(
                    f"- {prior['timestamp']}: {prior['rule']} {prior['severity']} value={fmt(prior['value'])} in {prior['incident']}"
                )
            lines.append("")
    lines.extend(["## Reflex Signal", ""])
    reflex = explanation["reflex_explanation"]
    if reflex:
        lines.extend(
            [
                f"- observed_value: {reflex['observed_value']}",
                f"- base_confidence: {reflex['base_confidence']}",
                f"- risk_class: {reflex['risk_class']}",
                f"- circadian_adjustment: {stable_json(reflex['circadian_adjustment'])}",
                f"- likely_cause: {reflex['likely_cause']}",
                f"- resembles_prior_incidents: {reflex['resembles_prior_incidents']}",
                f"- prior_incident_count: {reflex['prior_incident_count']}",
                f"- latest_incident: {reflex['latest_incident']}",
            ]
        )
    else:
        lines.append("- No active reflex signal.")
    lines.extend(["", "## Sources", ""])
    for key, value in explanation["sources"].items():
        lines.append(f"- {key}: {value}")
    LATEST_EXPLANATION.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_explanation() -> dict[str, Any]:
    explanation = build_explanation()
    write_explanation(explanation)
    record_checksum(LATEST_EXPLANATION, "anomaly_explanation_write", {"source": "system_state"})
    warning_metrics = [item["metric"] for item in explanation["metric_explanations"]]
    summary = {
        "explanation": str(LATEST_EXPLANATION.relative_to(ROOT)),
        "active_warning_count": explanation["active_warning_count"],
        "warning_metrics": warning_metrics,
        "reflex_confidence": (explanation["reflex_explanation"] or {}).get("observed_value"),
        "overall_circadian_deviation": explanation["overall_circadian_deviation"],
        "recommendations_only": True,
    }
    append_memory(stable_json(summary), ["guardian", "explanation", "anomaly", "night19"], "anomaly_explanation")
    log_action("anomaly:explain", "completed", "ALLOW", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain active Ambient OS anomaly signals.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_explanation()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
