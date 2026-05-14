"""
Skill: Anomaly Explain — Explain active anomaly and reflex signals.

Migrated from scripts/explain_anomaly.py. Wraps the core explanation logic
as a registered skill with formal inputs, outputs, and governance declarations.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from skills.core.skill_schema import (
    SkillContext,
    SkillInput,
    SkillMetadata,
    SkillOutput,
    SkillResult,
    SkillSchema,
)

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
STATE_JSON = AMBIENT_ROOT / "state" / "system_state.json"
BASELINE_JSON = AMBIENT_ROOT / "guardian" / "baselines" / "telemetry_baseline.json"
CIRCADIAN_JSON = AMBIENT_ROOT / "guardian" / "baselines" / "circadian_baseline.json"
HEALTH_JSON = AMBIENT_ROOT / "guardian" / "health" / "health_scores.json"
INCIDENT_INDEX = AMBIENT_ROOT / "guardian" / "incidents" / "index.json"

METRIC_PATHS: dict[str, tuple[str, ...]] = {
    "cpu_usage_percent": ("cpu_usage_percent",),
    "memory_used_percent": ("memory_usage", "used_percent"),
    "disk_used_percent": ("disk_usage", "used_percent"),
    "load_average_1m": ("load_average", "1m"),
    "load_average_5m": ("load_average", "5m"),
    "load_average_15m": ("load_average", "15m"),
    "process_count": ("process_count",),
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _nested_get(record: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = record
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _classify_deviation(current: Any, baseline_stats: dict[str, Any]) -> dict[str, Any]:
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


def _severity_active(value: Any) -> bool:
    return str(value) in {"warning", "critical"}


def _build_metric_explanations(
    state: dict[str, Any],
    latest: dict[str, Any],
    baseline: dict[str, Any],
    circadian: dict[str, Any],
) -> list[dict[str, Any]]:
    metrics: set[str] = set()
    for name, data in (baseline.get("metrics") or {}).items():
        observed = _nested_get(latest, METRIC_PATHS.get(name, (name,)))
        deviation = _classify_deviation(observed, data.get("baseline", {}))
        if _severity_active(deviation.get("severity")):
            metrics.add(name)
    for name, data in (circadian.get("metrics") or {}).items():
        if _severity_active(data.get("deviation", {}).get("severity")):
            metrics.add(name)

    explanations: list[dict[str, Any]] = []
    for metric in sorted(metrics):
        flat = (baseline.get("metrics") or {}).get(metric, {})
        circ = (circadian.get("metrics") or {}).get(metric, {})
        observed = _nested_get(latest, METRIC_PATHS.get(metric, (metric,)))
        flat_deviation = _classify_deviation(observed, flat.get("baseline", {}))
        circadian_deviation = _classify_deviation(observed, circ.get("baseline", {}))
        explanations.append({
            "metric": metric,
            "observed_value": observed,
            "flat_severity": flat_deviation.get("severity"),
            "circadian_severity": circadian_deviation.get("severity"),
            "z_score_flat": flat_deviation.get("z_score"),
            "z_score_circadian": circadian_deviation.get("z_score"),
        })
    return explanations


def _execute_anomaly_explain(ctx: SkillContext) -> SkillResult:
    """Build anomaly explanation from system state and baselines."""
    state = _load_json(STATE_JSON)
    if not state:
        return SkillResult(
            success=False,
            error="state/system_state.json is missing; run system-state-build first",
            trace_id=ctx.trace_id,
        )

    latest_path = AMBIENT_ROOT / str(state.get("latest_telemetry_snapshot", ""))
    latest = _load_json(latest_path)
    baseline = _load_json(BASELINE_JSON)
    circadian = _load_json(CIRCADIAN_JSON)
    health = _load_json(HEALTH_JSON)

    metric_explanations = _build_metric_explanations(state, latest, baseline, circadian)

    reflex_confidence = float(state.get("latest_reflex_confidence") or 0.0)
    risk_class = state.get("current_risk_class", "unknown")

    explanation = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "active_warning_count": len(metric_explanations),
        "metric_explanations": metric_explanations,
        "reflex_confidence": reflex_confidence,
        "risk_class": risk_class,
        "overall_flat_deviation": (state.get("baseline_deviation") or {}).get("overall_severity"),
        "overall_circadian_deviation": (state.get("circadian_deviation") or {}).get("overall_severity"),
        "health_score": health.get("history", [{}])[-1].get("health_score") if health.get("history") else None,
        "recommendations_only": True,
    }

    return SkillResult(
        success=True,
        outputs=explanation,
        confidence=0.85,
        memory_updates=["appends to episodic", "updates guardian explanations"],
        trace_id=ctx.trace_id,
    )


anomaly_explain_skill = SkillSchema(
    name="anomaly_explain",
    version="1.0.0",
    description="Explain active anomaly and reflex signals from system state, baselines, and incident history",
    inputs=[
        SkillInput("task_description", "str", True, "Description of what to explain"),
        SkillInput("metric_filter", "list[str]", False, "Optional list of metrics to focus on"),
    ],
    outputs=[
        SkillOutput("generated_at", "str", "ISO timestamp of when the explanation was generated"),
        SkillOutput("active_warning_count", "int", "Number of active metric warnings"),
        SkillOutput("metric_explanations", "list[dict]", "Per-metric deviation explanations"),
        SkillOutput("reflex_confidence", "float", "Current reflex confidence value"),
        SkillOutput("risk_class", "str", "Current risk classification"),
    ],
    execute=_execute_anomaly_explain,
    confidence_range=(0.6, 0.9),
    routing_conditions=["anomaly", "explain", "warning", "deviation", "metric", "alert"],
    memory_updates=["appends to episodic", "updates guardian explanations"],
    governance_level="ALLOW",
    observability_hooks=["log_execution", "trace_anomaly_explain"],
    metadata=SkillMetadata(
        tags=["system", "anomaly", "explanation", "guardian"],
        category="system",
        migration_source="scripts.explain_anomaly",
    ),
)
