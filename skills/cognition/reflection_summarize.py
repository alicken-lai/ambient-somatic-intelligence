"""
Skill: Reflection Summarize — Generate self-reflection from system state.

Migrated from scripts/self_reflect.py. Wraps the core reflection logic
as a registered skill with formal inputs, outputs, and governance declarations.
"""

from __future__ import annotations

import json
import logging
import os
import re
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
INCIDENT_INDEX = AMBIENT_ROOT / "guardian" / "incidents" / "index.json"
DAILY_DIGEST = AMBIENT_ROOT / "dashboard" / "daily_digest.md"
LATEST_REFLECTION = AMBIENT_ROOT / "docs" / "reflections" / "latest.md"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_digest(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- ([^:]+): (.*)$", line)
        if match:
            values[match.group(1).strip()] = match.group(2).strip()
    return values


def _previous_reflection() -> dict[str, str]:
    if not LATEST_REFLECTION.exists():
        return {}
    values: dict[str, str] = {}
    for line in LATEST_REFLECTION.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- ([^:]+): (.*)$", line)
        if match:
            values[match.group(1).strip()] = match.group(2).strip()
    return values


def _dominant_risk(state: dict[str, Any], incidents: dict[str, Any]) -> str:
    repeated = state.get("repeated_anomalies", {})
    if repeated:
        top_rule, count = max(repeated.items(), key=lambda item: int(item[1]))
        return f"{top_rule} repeated {count} times"
    baseline = (state.get("baseline_deviation") or {}).get("overall_severity")
    if baseline and baseline != "normal":
        return f"baseline deviation is {baseline}"
    latest = incidents.get("patterns", {}).get("latest_severity")
    if latest:
        return f"latest incident severity is {latest}"
    return "no dominant risk detected"


def _confidence_level(state: dict[str, Any]) -> str:
    confidence = float(state.get("latest_reflex_confidence") or 0.0)
    risk_class = state.get("current_risk_class", "unknown")
    if confidence >= 0.75:
        band = "high"
    elif confidence >= 0.4:
        band = "medium"
    else:
        band = "low"
    return f"{band} ({confidence:.2f}, {risk_class})"


def _current_condition(state: dict[str, Any], digest: dict[str, str]) -> str:
    health = state.get("health_score")
    trend = state.get("trend")
    memory = state.get("memory_status", {})
    baseline = (state.get("baseline_deviation") or {}).get("overall_severity")
    return (
        f"Health is {health} with {trend} trend; memory risk is {memory.get('true_risk')} "
        f"at {memory.get('used_percent')}% used; baseline deviation is {baseline}."
    )


def _changes_since_last(state: dict[str, Any], previous: dict[str, str], incidents: dict[str, Any]) -> str:
    if not previous:
        return "No prior reflection; this establishes the baseline."
    checks = [
        ("health_score", str(state.get("health_score"))),
        ("incident_count", str(state.get("incident_count"))),
        ("risk_class", str(state.get("current_risk_class"))),
        ("dominant_risk", _dominant_risk(state, incidents)),
    ]
    changed = [f"{k}: {previous.get(k)} -> {v}" for k, v in checks if previous.get(k) != v]
    return "; ".join(changed) if changed else "No material state change."


def _execute_reflection(ctx: SkillContext) -> SkillResult:
    """Build self-reflection from system state and incident history."""
    state = _load_json(STATE_JSON)
    if not state:
        return SkillResult(
            success=False,
            error="state/system_state.json is missing; run system-state-build first",
            trace_id=ctx.trace_id,
        )

    incidents = _load_json(INCIDENT_INDEX)
    digest = _parse_digest(DAILY_DIGEST)
    previous = _previous_reflection()

    risk = _dominant_risk(state, incidents)
    condition = _current_condition(state, digest)
    confidence = _confidence_level(state)
    changes = _changes_since_last(state, previous, incidents)

    reflection = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "health_score": state.get("health_score"),
        "risk_class": state.get("current_risk_class"),
        "current_condition": condition,
        "dominant_risk": risk,
        "confidence_level": confidence,
        "what_changed": changes,
        "recommended_next": state.get("recommendations", ["Continue monitoring"])[0]
            if state.get("recommendations") else "Continue monitoring",
        "recommendations_only": True,
    }

    return SkillResult(
        success=True,
        outputs=reflection,
        confidence=0.85,
        memory_updates=["appends to episodic", "updates self-model reflections"],
        trace_id=ctx.trace_id,
    )


reflection_summarize_skill = SkillSchema(
    name="reflection_summarize",
    version="1.0.0",
    description="Generate self-reflection summary from system state, incidents, and prior reflections",
    inputs=[
        SkillInput("task_description", "str", True, "Description of the reflection request"),
        SkillInput("focus_areas", "list[str]", False, "Optional areas to focus the reflection on"),
    ],
    outputs=[
        SkillOutput("generated_at", "str", "ISO timestamp of reflection generation"),
        SkillOutput("health_score", "float", "Current system health score"),
        SkillOutput("risk_class", "str", "Current risk classification"),
        SkillOutput("current_condition", "str", "Human-readable condition summary"),
        SkillOutput("dominant_risk", "str", "The most significant current risk"),
        SkillOutput("what_changed", "str", "Changes since the last reflection"),
    ],
    execute=_execute_reflection,
    confidence_range=(0.6, 0.9),
    routing_conditions=["reflect", "reflection", "self-model", "introspect", "summarize", "condition"],
    memory_updates=["appends to episodic", "updates self-model reflections"],
    governance_level="ALLOW",
    observability_hooks=["log_execution", "trace_reflection"],
    metadata=SkillMetadata(
        tags=["cognition", "reflection", "self-model"],
        category="cognition",
        migration_source="scripts.self_reflect",
    ),
)
