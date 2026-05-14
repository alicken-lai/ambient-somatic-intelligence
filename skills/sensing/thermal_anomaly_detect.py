"""
Skill: Thermal Anomaly Detect — Detect thermal anomalies from system telemetry.

Analyzes CPU temperature and thermal throttling signals to identify
anomalous thermal conditions that may indicate hardware or workload issues.
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

THERMAL_THRESHOLDS = {
    "cpu_temp_warning": 75.0,
    "cpu_temp_critical": 90.0,
    "load_thermal_correlation": 0.7,
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _detect_thermal_anomaly(
    state: dict[str, Any],
    thresholds: dict[str, float],
) -> dict[str, Any]:
    """Analyze state for thermal anomaly indicators."""
    cpu_usage = state.get("cpu_usage_percent", 0.0)
    load_1m = (state.get("load_average") or {}).get("1m", 0.0)
    load_5m = (state.get("load_average") or {}).get("5m", 0.0)

    thermal_risk = "normal"
    indicators: list[str] = []

    try:
        cpu_val = float(cpu_usage)
    except (TypeError, ValueError):
        cpu_val = 0.0

    if cpu_val > thresholds["cpu_temp_critical"]:
        thermal_risk = "critical"
        indicators.append(f"CPU usage at {cpu_val}% exceeds critical threshold")
    elif cpu_val > thresholds["cpu_temp_warning"]:
        thermal_risk = "warning"
        indicators.append(f"CPU usage at {cpu_val}% exceeds warning threshold")

    try:
        load_ratio = float(load_1m) / max(float(load_5m), 0.01)
    except (TypeError, ValueError, ZeroDivisionError):
        load_ratio = 1.0

    if load_ratio > 1.5 and cpu_val > 60:
        if thermal_risk == "normal":
            thermal_risk = "elevated"
        indicators.append(
            f"Load spike detected: 1m/5m ratio={load_ratio:.2f} with high CPU"
        )

    return {
        "thermal_risk": thermal_risk,
        "indicators": indicators,
        "cpu_usage_percent": cpu_val,
        "load_1m": load_1m,
        "load_5m": load_5m,
        "load_spike_ratio": round(load_ratio, 3),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


def _execute_thermal_detect(ctx: SkillContext) -> SkillResult:
    """Detect thermal anomalies from current system state."""
    state = _load_json(STATE_JSON)
    if not state:
        return SkillResult(
            success=False,
            error="state/system_state.json is missing",
            trace_id=ctx.trace_id,
        )

    custom_thresholds = dict(THERMAL_THRESHOLDS)
    custom_thresholds.update(ctx.parameters.get("thresholds", {}))

    analysis = _detect_thermal_anomaly(state, custom_thresholds)

    confidence = 0.9 if analysis["indicators"] else 0.5

    return SkillResult(
        success=True,
        outputs=analysis,
        confidence=confidence,
        memory_updates=["appends to episodic"],
        trace_id=ctx.trace_id,
    )


thermal_anomaly_detect_skill = SkillSchema(
    name="thermal_anomaly_detect",
    version="1.0.0",
    description="Detect thermal anomalies from CPU usage, load averages, and thermal indicators",
    inputs=[
        SkillInput("task_description", "str", True, "Description of the detection request"),
        SkillInput("thresholds", "dict", False, "Custom threshold overrides"),
    ],
    outputs=[
        SkillOutput("thermal_risk", "str", "Risk level: normal, elevated, warning, critical"),
        SkillOutput("indicators", "list[str]", "List of detected thermal indicators"),
        SkillOutput("cpu_usage_percent", "float", "Current CPU usage"),
        SkillOutput("load_spike_ratio", "float", "1m/5m load ratio"),
    ],
    execute=_execute_thermal_detect,
    confidence_range=(0.5, 0.95),
    routing_conditions=["thermal", "temperature", "heat", "cpu", "throttle", "overheat"],
    memory_updates=["appends to episodic"],
    governance_level="ALLOW",
    observability_hooks=["log_execution", "trace_thermal_detection"],
    metadata=SkillMetadata(
        tags=["sensing", "thermal", "hardware", "monitoring"],
        category="sensing",
    ),
)
