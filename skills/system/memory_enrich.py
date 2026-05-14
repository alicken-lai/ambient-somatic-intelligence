"""
Skill: Memory Enrich — Enrich memory entries with contextual metadata.

Takes a raw memory entry and augments it with temporal context, relevance
scoring, and cross-references to related memories.
"""

from __future__ import annotations

import logging
import time
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


def _execute_memory_enrich(ctx: SkillContext) -> SkillResult:
    """Enrich a memory entry with contextual metadata."""
    params = ctx.parameters
    entry = params.get("memory_entry", {})
    memory_ctx = ctx.memory_context

    now = datetime.now(timezone.utc)
    enriched = dict(entry)
    enriched["enriched_at"] = now.isoformat()
    enriched["attention_level"] = ctx.attention_state.get("level", "normal")

    related_tags = memory_ctx.get("recent_tags", [])
    entry_tags = entry.get("tags", [])
    cross_refs = [t for t in related_tags if t in entry_tags]
    enriched["cross_references"] = cross_refs

    staleness = 0.0
    if "created_at" in entry:
        try:
            created = datetime.fromisoformat(entry["created_at"])
            age_hours = (now - created).total_seconds() / 3600
            staleness = min(age_hours / 168.0, 1.0)
        except (ValueError, TypeError):
            pass
    enriched["staleness_score"] = round(staleness, 4)

    relevance = 1.0 - (staleness * 0.3)
    if cross_refs:
        relevance = min(relevance + 0.1 * len(cross_refs), 1.0)
    enriched["relevance_score"] = round(relevance, 4)

    return SkillResult(
        success=True,
        outputs={"enriched_entry": enriched},
        confidence=0.9,
        memory_updates=["updates scratchpad"],
    )


memory_enrich_skill = SkillSchema(
    name="memory_enrich",
    version="1.0.0",
    description="Enrich memory entries with temporal context, relevance scoring, and cross-references",
    inputs=[
        SkillInput("memory_entry", "dict", True, "Raw memory entry to enrich"),
        SkillInput("context_window", "int", False, "Hours of context to consider"),
    ],
    outputs=[
        SkillOutput("enriched_entry", "dict", "Memory entry with added metadata"),
    ],
    execute=_execute_memory_enrich,
    confidence_range=(0.7, 0.95),
    routing_conditions=["memory", "enrich", "context", "augment", "metadata"],
    memory_updates=["updates scratchpad"],
    governance_level="ALLOW",
    observability_hooks=["log_execution", "trace_memory_update"],
    metadata=SkillMetadata(
        tags=["system", "memory", "enrichment"],
        category="system",
    ),
)
