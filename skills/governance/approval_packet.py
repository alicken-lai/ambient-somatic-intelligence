"""
Skill: Approval Packet — Generate structured approval packets for governance review.

When an action requires REVIEW_REQUIRED or BLOCK_WITHOUT_APPROVAL clearance,
this skill assembles a complete approval packet with context, risk assessment,
and proposed actions for human review.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
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


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _execute_approval_packet(ctx: SkillContext) -> SkillResult:
    """Assemble an approval packet for governance review."""
    params = ctx.parameters
    action = params.get("proposed_action", "")
    justification = params.get("justification", "")
    risk_assessment = params.get("risk_assessment", "unknown")
    affected_systems = params.get("affected_systems", [])

    if not action:
        return SkillResult(
            success=False,
            error="Approval packet requires 'proposed_action'",
            trace_id=ctx.trace_id,
        )

    state = _load_json(STATE_JSON)
    health_score = state.get("health_score", "unknown")
    risk_class = state.get("current_risk_class", "unknown")

    packet_id = f"approval-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    packet = {
        "packet_id": packet_id,
        "created_at": now.isoformat(),
        "status": "pending_review",
        "proposed_action": action,
        "justification": justification,
        "risk_assessment": risk_assessment,
        "affected_systems": affected_systems,
        "system_context": {
            "health_score": health_score,
            "risk_class": risk_class,
            "attention_level": ctx.attention_state.get("level", "normal"),
            "governance_clearance": ctx.governance_clearance,
        },
        "trace_id": ctx.trace_id,
        "requires_human_approval": risk_assessment in {"high", "critical"},
        "auto_expire_hours": 24,
    }

    logger.info(
        "Generated approval packet %s for action: %s (risk=%s)",
        packet_id, action[:60], risk_assessment,
    )

    return SkillResult(
        success=True,
        outputs={"approval_packet": packet},
        confidence=1.0,
        memory_updates=["appends to episodic", "updates governance audit"],
        trace_id=ctx.trace_id,
    )


approval_packet_skill = SkillSchema(
    name="approval_packet",
    version="1.0.0",
    description="Generate structured approval packets for actions requiring governance review",
    inputs=[
        SkillInput("proposed_action", "str", True, "The action requiring approval"),
        SkillInput("justification", "str", True, "Why this action is needed"),
        SkillInput("risk_assessment", "str", True, "Risk level: low, medium, high, critical"),
        SkillInput("affected_systems", "list[str]", False, "Systems affected by the action"),
    ],
    outputs=[
        SkillOutput("approval_packet", "dict", "Complete approval packet for review"),
    ],
    execute=_execute_approval_packet,
    confidence_range=(0.9, 1.0),
    routing_conditions=["approval", "approve", "packet", "review", "permission", "authorize"],
    memory_updates=["appends to episodic", "updates governance audit"],
    governance_level="REVIEW_REQUIRED",
    observability_hooks=["log_execution", "trace_approval_packet"],
    metadata=SkillMetadata(
        tags=["governance", "approval", "review", "safety"],
        category="governance",
    ),
)
