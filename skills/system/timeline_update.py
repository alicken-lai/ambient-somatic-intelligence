"""
Skill: Timeline Update — Append or update entries in the system timeline.

Manages the structured event timeline that records significant system
events, state transitions, and milestones.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
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


def _execute_timeline_update(ctx: SkillContext) -> SkillResult:
    """Create or update a timeline entry."""
    params = ctx.parameters
    event_type = params.get("event_type", "generic")
    summary = params.get("summary", "")
    details = params.get("details", {})
    severity = params.get("severity", "info")

    if not summary:
        return SkillResult(
            success=False,
            error="Timeline entry requires a non-empty 'summary'",
            trace_id=ctx.trace_id,
        )

    now = datetime.now(timezone.utc)
    entry = {
        "timestamp": now.isoformat(),
        "event_type": event_type,
        "summary": summary,
        "details": details,
        "severity": severity,
        "source": "skills.system.timeline_update",
        "trace_id": ctx.trace_id,
        "attention_level": ctx.attention_state.get("level", "normal"),
    }

    logger.info(
        "Timeline entry [%s] %s: %s", severity, event_type, summary[:80],
    )

    return SkillResult(
        success=True,
        outputs={"timeline_entry": entry},
        confidence=1.0,
        memory_updates=["appends to episodic"],
    )


timeline_update_skill = SkillSchema(
    name="timeline_update",
    version="1.0.0",
    description="Append or update entries in the system event timeline",
    inputs=[
        SkillInput("event_type", "str", True, "Type of event (e.g. 'anomaly', 'milestone', 'transition')"),
        SkillInput("summary", "str", True, "Human-readable summary of the event"),
        SkillInput("details", "dict", False, "Additional structured details"),
        SkillInput("severity", "str", False, "Severity level: info, warning, critical"),
    ],
    outputs=[
        SkillOutput("timeline_entry", "dict", "The constructed timeline entry"),
    ],
    execute=_execute_timeline_update,
    confidence_range=(0.8, 1.0),
    routing_conditions=["timeline", "event", "log", "record", "history", "update"],
    memory_updates=["appends to episodic"],
    governance_level="ALLOW",
    observability_hooks=["log_execution", "trace_timeline_write"],
    metadata=SkillMetadata(
        tags=["system", "timeline", "events"],
        category="system",
    ),
)
