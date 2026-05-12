#!/usr/bin/env python3
"""Simulate how current anomalies may evolve if they continue."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json
from build_system_state import build_system_state
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
STATE_JSON = ROOT / "state" / "system_state.json"
BASELINE_JSON = ROOT / "guardian" / "baselines" / "telemetry_baseline.json"
CIRCADIAN_JSON = ROOT / "guardian" / "baselines" / "circadian_baseline.json"
INCIDENT_INDEX = ROOT / "guardian" / "incidents" / "index.json"
EXPLANATION_MD = ROOT / "guardian" / "explanations" / "latest_anomaly.md"
SIMULATION_DIR = ROOT / "guardian" / "simulations"
LATEST_SIMULATION_MD = SIMULATION_DIR / "latest_simulation.md"
LATEST_SIMULATION_JSON = SIMULATION_DIR / "latest_simulation.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_warning_metrics(path: Path) -> list[str]:
    if not path.exists():
        return []
    metrics: list[str] = []
    in_section = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "## Metric Warnings":
            in_section = True
            continue
        if not in_section:
            continue
        if line.startswith("## "):
            break
        match = re.match(r"^### ([A-Za-z0-9_]+)$", line)
        if match:
            metrics.append(match.group(1))
    return metrics


def metric_source(metric: str) -> str:
    return {
        "disk_used_percent": "disk",
        "load_average_15m": "load",
        "load_average_5m": "load",
        "memory_used_percent": "memory",
        "reflex_confidence": "reflex",
    }.get(metric, "mixed")


def metric_path(metric: str) -> tuple[str, ...]:
    return {
        "disk_used_percent": ("disk_usage", "used_percent"),
        "load_average_15m": ("load_average", "15m"),
        "load_average_5m": ("load_average", "5m"),
        "memory_used_percent": ("memory_usage", "used_percent"),
    }.get(metric, (metric,))


def nested_get(record: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = record
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def severity_score(label: str | None) -> int:
    return {
        "normal": 0,
        "elevated": 1,
        "warning": 2,
        "critical": 3,
        "unknown": 0,
        None: 0,
    }.get(label, 0)


def horizon_labels(metric: str, state: dict[str, Any], flat_severity: str, circadian_severity: str) -> dict[str, str]:
    base = max(severity_score(flat_severity), severity_score(circadian_severity))
    repeated = state.get("repeated_anomalies", {})
    if metric == "memory_used_percent" and repeated.get("high_memory_usage", 0):
        return {
            "5m": "watch",
            "30m": "review",
            "2h": "review",
        }
    if base >= 2:
        return {
            "5m": "watch",
            "30m": "watch",
            "2h": "review",
        }
    if base == 1:
        return {
            "5m": "watch",
            "30m": "watch",
            "2h": "watch",
        }
    return {
        "5m": "watch",
        "30m": "watch",
        "2h": "watch",
    }


def degradation_path(metric: str, state: dict[str, Any], flat_severity: str, circadian_severity: str) -> str:
    if metric == "memory_used_percent":
        if state.get("repeated_anomalies", {}).get("high_memory_usage", 0):
            return "continued memory pressure could recreate the earlier high-memory pattern and push the host toward a repeat incident"
        return "memory pressure likely stays watch-level with intermittent recovery"
    if metric == "disk_used_percent":
        return "disk headroom likely tightens slowly, but the current drift looks bounded"
    if metric.startswith("load_average"):
        if severity_score(circadian_severity) < severity_score(flat_severity):
            return "the time-aware baseline suggests a mild local anomaly that may fade rather than compound"
        return "load stays modestly elevated against the learned baseline"
    if metric == "reflex_confidence":
        return "reflex confidence stays suppressed while incident memory remains active"
    return "the anomaly remains persistent but not yet structurally severe"


def subsystem_impact(metric: str, state: dict[str, Any]) -> str:
    subsystem_map = {
        "memory_used_percent": "memory subsystem headroom and local task scheduling",
        "disk_used_percent": "disk capacity margin",
        "load_average_15m": "load balancing and short-term scheduling",
        "load_average_5m": "load balancing and short-term scheduling",
        "reflex_confidence": "decision routing and conservative behavior",
    }
    base = subsystem_map.get(metric, "mixed host telemetry")
    subsystem_scores = state.get("subsystems", {})
    if metric == "memory_used_percent":
        score = (subsystem_scores.get("memory_health") or {}).get("score")
        return f"{base}; current memory_health score is {score}"
    if metric == "disk_used_percent":
        score = (subsystem_scores.get("disk_health") or {}).get("score")
        return f"{base}; current disk_health score is {score}"
    if metric.startswith("load_average"):
        score = (subsystem_scores.get("load_health") or {}).get("score")
        return f"{base}; current load_health score is {score}"
    return base


def incident_similarity(metric: str, state: dict[str, Any], incidents: dict[str, Any]) -> dict[str, Any]:
    repeated = state.get("repeated_anomalies", {})
    matches = []
    for incident in incidents.get("incidents", []):
        for anomaly in incident.get("anomalies", []):
            rule = str(anomaly.get("rule", ""))
            if metric == "memory_used_percent" and "memory" in rule:
                matches.append(
                    {
                        "incident": incident.get("incident"),
                        "rule": rule,
                        "severity": anomaly.get("severity"),
                        "value": anomaly.get("value"),
                    }
                )
            elif metric.startswith("load_average") and "load" in rule:
                matches.append(
                    {
                        "incident": incident.get("incident"),
                        "rule": rule,
                        "severity": anomaly.get("severity"),
                        "value": anomaly.get("value"),
                    }
                )
            elif metric == "disk_used_percent" and "disk" in rule:
                matches.append(
                    {
                        "incident": incident.get("incident"),
                        "rule": rule,
                        "severity": anomaly.get("severity"),
                        "value": anomaly.get("value"),
                    }
                )
    return {
        "resembles_prior_incidents": bool(matches),
        "repeat_count": repeated.get("high_memory_usage", 0) if metric == "memory_used_percent" else 0,
        "matches": matches,
    }


def confidence_value(state: dict[str, Any], metric: str) -> float:
    base = float(state.get("latest_reflex_confidence") or 0.0)
    if metric == "memory_used_percent":
        return min(1.0, base + 0.55)
    if metric == "disk_used_percent":
        return min(1.0, base + 0.2)
    if metric.startswith("load_average"):
        return min(1.0, base + 0.15)
    return min(1.0, base + 0.1)


def false_positive_likelihood(metric: str, flat_severity: str, circadian_severity: str, similarity: dict[str, Any]) -> str:
    if metric == "memory_used_percent" and similarity.get("resembles_prior_incidents"):
        return "low"
    if severity_score(circadian_severity) < severity_score(flat_severity):
        return "medium"
    return "medium"


def reflex_simulation(state: dict[str, Any], incidents: dict[str, Any]) -> dict[str, Any]:
    similarity = incident_similarity("memory_used_percent", state, incidents)
    base_confidence = float(state.get("base_reflex_confidence") or 0.0)
    current_confidence = float(state.get("latest_reflex_confidence") or 0.0)
    return {
        "metric": "reflex_confidence",
        "source": "reflex",
        "observed_value": current_confidence,
        "flat_baseline": {
            "mean": base_confidence,
            "severity": "watch" if current_confidence <= base_confidence else "elevated",
            "delta_from_mean": round(current_confidence - base_confidence, 4),
            "z_score": None,
        },
        "circadian_baseline": {
            "comparison_basis": state.get("time_context", {}).get("day_type"),
            "mean": current_confidence,
            "severity": state.get("circadian_deviation", {}).get("overall_severity", "warning"),
            "delta_from_mean": state.get("circadian_deviation", {}).get("time_adjusted_reflex_confidence", {}).get("adjustment"),
            "z_score": None,
        },
        "likely_degradation_path": "reflex confidence stays suppressed while incident memory remains active",
        "subsystem_impact": "decision routing and conservative behavior",
        "incident_similarity": similarity,
        "confidence": 0.6,
        "false_positive_likelihood": "medium",
        "horizons": {
            "5m": {"projected_risk": "watch", "expected_behavior": "bounded watch-level persistence"},
            "30m": {"projected_risk": "watch", "expected_behavior": "bounded watch-level persistence"},
            "2h": {"projected_risk": "watch", "expected_behavior": "bounded watch-level persistence"},
        },
        "current_simulation_result": "watch",
    }


def summarize_warning(metric: str, state: dict[str, Any], telemetry: dict[str, Any], baseline: dict[str, Any], circadian: dict[str, Any], incidents: dict[str, Any]) -> dict[str, Any]:
    flat = (baseline.get("metrics") or {}).get(metric, {})
    circ = (circadian.get("metrics") or {}).get(metric, {})
    observed = nested_get(telemetry, metric_path(metric))
    flat_severity = str((flat.get("deviation") or {}).get("severity", "unknown"))
    circadian_severity = str((circ.get("deviation") or {}).get("severity", "unknown"))
    horizons = horizon_labels(metric, state, flat_severity, circadian_severity)
    similarity = incident_similarity(metric, state, incidents)
    confidence = round(confidence_value(state, metric), 2)
    fp_likelihood = false_positive_likelihood(metric, flat_severity, circadian_severity, similarity)
    current_risk = horizons["2h"]
    return {
        "metric": metric,
        "source": metric_source(metric),
        "observed_value": observed,
        "flat_baseline": {
            "mean": (flat.get("baseline") or {}).get("mean"),
            "severity": flat_severity,
            "delta_from_mean": (flat.get("deviation") or {}).get("delta_from_mean"),
            "z_score": (flat.get("deviation") or {}).get("z_score"),
        },
        "circadian_baseline": {
            "comparison_basis": circadian.get("comparison_basis"),
            "mean": (circ.get("baseline") or {}).get("mean"),
            "severity": circadian_severity,
            "delta_from_mean": (circ.get("deviation") or {}).get("delta_from_mean"),
            "z_score": (circ.get("deviation") or {}).get("z_score"),
        },
        "likely_degradation_path": degradation_path(metric, state, flat_severity, circadian_severity),
        "subsystem_impact": subsystem_impact(metric, state),
        "incident_similarity": similarity,
        "confidence": confidence,
        "false_positive_likelihood": fp_likelihood,
        "horizons": {
            window: {
                "projected_risk": risk,
                "expected_behavior": (
                    "bounded watch-level persistence"
                    if risk == "watch"
                    else "continued drift toward review"
                ),
            }
            for window, risk in horizons.items()
        },
        "current_simulation_result": current_risk,
    }


def build_simulation() -> dict[str, Any]:
    state = load_json(STATE_JSON)
    if not state:
        raise RuntimeError("state/system_state.json is missing; run system-state-build first")
    telemetry_path = ROOT / str(state.get("latest_telemetry_snapshot", ""))
    telemetry = load_json(telemetry_path)
    baseline = load_json(BASELINE_JSON)
    circadian = load_json(CIRCADIAN_JSON)
    incidents = load_json(INCIDENT_INDEX)
    warning_metrics = parse_warning_metrics(EXPLANATION_MD)
    if not warning_metrics:
        warning_metrics = ["memory_used_percent"]

    simulations = [
        summarize_warning(metric, state, telemetry, baseline, circadian, incidents)
        for metric in warning_metrics
    ]
    simulations.append(reflex_simulation(state, incidents))
    overall_risk = "review" if any(item["current_simulation_result"] == "review" for item in simulations) else "watch"
    if any(item["metric"] == "memory_used_percent" and item["incident_similarity"]["resembles_prior_incidents"] for item in simulations):
        overall_risk = "review"
    summary = {
        "generated_at": utc_now(),
        "simulation_active": True,
        "latest_telemetry": str(telemetry_path.relative_to(ROOT)) if telemetry_path.exists() else str(state.get("latest_telemetry_snapshot")),
        "system_state": str(STATE_JSON.relative_to(ROOT)),
        "baseline": str(BASELINE_JSON.relative_to(ROOT)),
        "circadian_baseline": str(CIRCADIAN_JSON.relative_to(ROOT)),
        "incident_memory": str(INCIDENT_INDEX.relative_to(ROOT)),
        "anomaly_explanations": str(EXPLANATION_MD.relative_to(ROOT)),
        "predicted_risk": {
            "level": overall_risk,
            "confidence": round(max(item["confidence"] for item in simulations) if simulations else 0.0, 2),
            "primary_driver": next((item["metric"] for item in simulations if item["metric"] == "memory_used_percent"), simulations[0]["metric"] if simulations else "unknown"),
            "incident_similarity": next((item["metric"] for item in simulations if item["incident_similarity"].get("resembles_prior_incidents")), simulations[0]["metric"] if simulations else "unknown"),
            "false_positive_likelihood": "low" if any(item["false_positive_likelihood"] == "low" for item in simulations) else "medium",
            "horizon_summary": {
                "5m": "watch",
                "30m": "review" if any(item["current_simulation_result"] == "review" for item in simulations) else "watch",
                "2h": overall_risk,
            },
        },
        "active_warnings": simulations,
        "corrective_actions": "none",
        "recommendations_only": True,
    }
    return summary


def write_simulation(simulation: dict[str, Any]) -> None:
    SIMULATION_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pre-Accident Simulation",
        "",
        f"- generated_at: {simulation['generated_at']}",
        f"- simulation_active: {str(simulation['simulation_active']).lower()}",
        f"- predicted_risk: {simulation['predicted_risk']['level']}",
        f"- confidence: {simulation['predicted_risk']['confidence']}",
        "- corrective_actions: none",
        "- response_mode: recommendations only",
        "",
        "## Predicted Risk",
        "",
        f"Overall predicted risk is {simulation['predicted_risk']['level']} with {simulation['predicted_risk']['confidence']} confidence.",
        f"Primary driver: {simulation['predicted_risk']['primary_driver']}.",
        f"Incident similarity: {simulation['predicted_risk']['incident_similarity']}.",
        f"False-positive likelihood: {simulation['predicted_risk']['false_positive_likelihood']}.",
        "",
        "## Horizon Summary",
        "",
    ]
    for window, label in simulation["predicted_risk"]["horizon_summary"].items():
        lines.append(f"- {window}: {label}")
    lines.extend(["", "## Active Warnings", ""])
    for warning in simulation["active_warnings"]:
        lines.extend(
            [
                f"### {warning['metric']}",
                "",
                f"- observed_value: {warning['observed_value']}",
                f"- flat_baseline: mean={warning['flat_baseline']['mean']}, severity={warning['flat_baseline']['severity']}, z={warning['flat_baseline']['z_score']}, delta={warning['flat_baseline']['delta_from_mean']}",
                f"- circadian_baseline: basis={warning['circadian_baseline']['comparison_basis']}, mean={warning['circadian_baseline']['mean']}, severity={warning['circadian_baseline']['severity']}, z={warning['circadian_baseline']['z_score']}, delta={warning['circadian_baseline']['delta_from_mean']}",
                f"- likely_degradation_path: {warning['likely_degradation_path']}",
                f"- subsystem_impact: {warning['subsystem_impact']}",
                f"- incident_similarity: {stable_json(warning['incident_similarity'])}",
                f"- confidence: {warning['confidence']}",
                f"- false_positive_likelihood: {warning['false_positive_likelihood']}",
                "",
                "#### 5 Minutes",
                "",
                f"- projected_risk: {warning['horizons']['5m']['projected_risk']}",
                f"- expected_behavior: {warning['horizons']['5m']['expected_behavior']}",
                "",
                "#### 30 Minutes",
                "",
                f"- projected_risk: {warning['horizons']['30m']['projected_risk']}",
                f"- expected_behavior: {warning['horizons']['30m']['expected_behavior']}",
                "",
                "#### 2 Hours",
                "",
                f"- projected_risk: {warning['horizons']['2h']['projected_risk']}",
                f"- expected_behavior: {warning['horizons']['2h']['expected_behavior']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Sources",
            "",
            f"- system_state: {simulation['system_state']}",
            f"- latest_telemetry: {simulation['latest_telemetry']}",
            f"- baseline: {simulation['baseline']}",
            f"- circadian_baseline: {simulation['circadian_baseline']}",
            f"- incident_memory: {simulation['incident_memory']}",
            f"- anomaly_explanations: {simulation['anomaly_explanations']}",
        ]
    )
    LATEST_SIMULATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    LATEST_SIMULATION_JSON.write_text(json.dumps(simulation, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_simulation() -> dict[str, Any]:
    simulation = build_simulation()
    write_simulation(simulation)
    build_system_state()
    record_checksum(LATEST_SIMULATION_MD, "incident_simulation_write", {"source": "system_state_and_anomaly_explanations"})
    record_checksum(LATEST_SIMULATION_JSON, "incident_simulation_index_write", {"source": "system_state_and_anomaly_explanations"})
    summary = {
        "simulation": str(LATEST_SIMULATION_MD.relative_to(ROOT)),
        "simulation_json": str(LATEST_SIMULATION_JSON.relative_to(ROOT)),
        "simulation_active": True,
        "predicted_risk": simulation["predicted_risk"],
        "recommendations_only": True,
    }
    append_memory(stable_json(summary), ["guardian", "simulation", "night23"], "simulation")
    log_action("simulation:build", "completed", "ALLOW", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate anomaly continuation in Ambient OS.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(run_simulation()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
