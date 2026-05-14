"""
Skill: Risk Escalation — Escalate risk events through governance channels.

Evaluates the current risk state and determines if escalation is required
based on severity, persistence, and governance policy thresholds.
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
INCIDENT_INDEX = AMBIENT_ROOT / "guardian" / "incidents" / "index.json"

ESCALATION_THRESHOLDS = {
    "confidence_critical": 0.15,
    "confidence_warning": 0.3,
    "repeated_anomaly_limit": 3,
    "health_score_critical": 40.0,
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _assess_escalation(
    state: dict[str, Any],
    incidents: dict[str, Any],
    thresholds: dict[str, float],
) -> dict[str, Any]:
    """Determine if the current risk state warrants escalation."""
    confidence = float(state.get("latest_reflex_confidence") or 1.0)
    risk_class = state.get("current_risk_class", "unknown")
    health_score = float(state.get("health_score") or 100.0)
    repeated = state.get("repeated_anomalies", {})

    reasons: list[str] = []
    escalation_level = "none"

    if confidence < thresholds["confidence_critical"]:
        escalation_level = "critical"
        reasons.append(f"Reflex confidence critically low: {confidence:.3f}")
    elif confidence < thresholds["confidence_warning"]:
        if escalation_level != "critical":
            escalation_level = "warning"
        reasons.append(f"Reflex confidence below warning threshold: {confidence:.3f}")

    if health_score < thresholds["health_score_critical"]:
        escalation_level = "critical"
        reasons.append(f"Health score critically low: {health_score}")

    for rule, count in repeated.items():
        if int(count) >= thresholds["repeated_anomaly_limit"]:
            if escalation_level not in {"critical"}:
                escalation_level = "warning"
            reasons.append(f"Anomaly '{rule}' repeated {count} times")

    recent = incidents.get("incidents", [])[-5:]
    critical_recent = sum(
        1 for inc in recent
        for a in inc.get("anomalies", [])
        if str(a.get("severity")) == "critical"
    )
    if critical_recent >= 2:
        escalation_level = "critical"
        reasons.append(f"{critical_recent} critical anomalies in recent incidents")

    return {
        "escalation_level": escalation_level,
        "reasons": reasons,
        "should_escalate": escalation_level != "none",
        "governance_action": (
            "BLOCK_WITHOUT_APPROVAL" if escalation_level == "critical"
            else "REVIEW_REQUIRED" if escalation_level == "warning"
            else "ALLOW"
        ),
        "reflex_confidence": confidence,
        "health_score": health_score,
        "risk_class": risk_class,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def _execute_risk_escalation(ctx: SkillContext) -> SkillResult:
    """Evaluate and potentially escalate current risk state."""
    state = _load_json(STATE_JSON)
    if not state:
        return SkillResult(
            success=False,
            error="state/system_state.json is missing",
            trace_id=ctx.trace_id,
        )

    incidents = _load_json(INCIDENT_INDEX)

    custom_thresholds = dict(ESCALATION_THRESHOLDS)
    custom_thresholds.update(ctx.parameters.get("thresholds", {}))

    assessment = _assess_escalation(state, incidents, custom_thresholds)

    if assessment["should_escalate"]:
        logger.warning(
            "Risk escalation triggered [%s]: %s",
            assessment["escalation_level"],
            "; ".join(assessment["reasons"]),
        )

    return SkillResult(
        success=True,
        outputs=assessment,
        confidence=0.9,
        memory_updates=["appends to episodic", "updates governance audit"],
        trace_id=ctx.trace_id,
    )


risk_escalation_skill = SkillSchema(
    name="risk_escalation",
    version="1.0.0",
    description="Evaluate system risk state and escalate through governance channels when thresholds are breached",
    inputs=[
        SkillInput("task_description", "str", True, "Description of the escalation request"),
        SkillInput("thresholds", "dict", False, "Custom threshold overrides"),
    ],
    outputs=[
        SkillOutput("escalation_level", "str", "Level: none, warning, critical"),
        SkillOutput("reasons", "list[str]", "Reasons for escalation"),
        SkillOutput("should_escalate", "bool", "Whether escalation is warranted"),
        SkillOutput("governance_action", "str", "Recommended governance action"),
    ],
    execute=_execute_risk_escalation,
    confidence_range=(0.7, 0.95),
    routing_conditions=["risk", "escalate", "escalation", "alert", "governance", "breach"],
    memory_updates=["appends to episodic", "updates governance audit"],
    governance_level="REVIEW_REQUIRED",
    observability_hooks=["log_execution", "trace_risk_escalation", "alert_on_critical"],
    metadata=SkillMetadata(
        tags=["governance", "risk", "escalation", "safety"],
        category="governance",
    ),
)
