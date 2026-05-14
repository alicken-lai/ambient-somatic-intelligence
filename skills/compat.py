"""
Compatibility Layer — Wrap legacy scripts as registered skills.

Provides an adapter that takes an existing script module and a metadata
dict and produces a SkillSchema that can be registered in the skill layer
without modifying the original script.
"""

from __future__ import annotations

import importlib
import logging
import time
from types import ModuleType
from typing import Any, Callable

from skills.core.skill_schema import (
    SkillContext,
    SkillInput,
    SkillMetadata,
    SkillOutput,
    SkillResult,
    SkillSchema,
)

logger = logging.getLogger(__name__)


def _make_execute_fn(
    script_module: ModuleType,
    entry_point: str,
) -> Callable[[SkillContext], SkillResult]:
    """Build an execute callable that wraps a legacy script's entry point."""
    fn = getattr(script_module, entry_point, None)
    if fn is None or not callable(fn):
        raise AttributeError(
            f"Module '{script_module.__name__}' has no callable '{entry_point}'"
        )

    def _execute(ctx: SkillContext) -> SkillResult:
        start = time.monotonic()
        try:
            raw_result = fn()
            elapsed = (time.monotonic() - start) * 1000
            outputs = raw_result if isinstance(raw_result, dict) else {"result": raw_result}
            return SkillResult(
                success=True,
                outputs=outputs,
                confidence=1.0,
                memory_updates=[],
                execution_time_ms=elapsed,
                trace_id=ctx.trace_id,
            )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return SkillResult(
                success=False,
                error=str(exc),
                execution_time_ms=elapsed,
                trace_id=ctx.trace_id,
            )

    return _execute


def wrap_legacy_script(
    script_module: ModuleType | str,
    skill_metadata: dict[str, Any],
) -> SkillSchema:
    """
    Wrap an existing script module as a SkillSchema.

    Parameters:
        script_module: A loaded module or a dotted import path string.
        skill_metadata: Dict with keys:
            - name (required): skill name
            - version (required): semver string
            - description (required): what the skill does
            - entry_point (optional): callable name in the module (default "run_explanation" / "run_reflection" / "main")
            - inputs (optional): list of input dicts
            - outputs (optional): list of output dicts
            - routing_conditions (optional): keyword list
            - memory_updates (optional): declared side effects
            - governance_level (optional): default "ALLOW"
            - observability_hooks (optional): hook list
            - tags (optional): tag list for metadata

    Returns:
        A fully-formed SkillSchema ready for registration.
    """
    if isinstance(script_module, str):
        script_module = importlib.import_module(script_module)

    name = skill_metadata["name"]
    version = skill_metadata["version"]
    description = skill_metadata["description"]

    entry_point = skill_metadata.get("entry_point", "main")
    for candidate in [entry_point, "run_explanation", "run_reflection", "main"]:
        if hasattr(script_module, candidate) and callable(getattr(script_module, candidate)):
            entry_point = candidate
            break

    execute_fn = _make_execute_fn(script_module, entry_point)

    raw_inputs = skill_metadata.get("inputs", [{"name": "task_description", "type_hint": "str", "required": True, "description": "Task to execute"}])
    inputs = [
        SkillInput(
            name=i["name"],
            type_hint=i.get("type_hint", "Any"),
            required=i.get("required", True),
            description=i.get("description", ""),
        )
        for i in raw_inputs
    ]

    raw_outputs = skill_metadata.get("outputs", [{"name": "result", "type_hint": "dict", "description": "Script output"}])
    outputs = [
        SkillOutput(
            name=o["name"],
            type_hint=o.get("type_hint", "Any"),
            description=o.get("description", ""),
        )
        for o in raw_outputs
    ]

    metadata = SkillMetadata(
        author=skill_metadata.get("author", "ambient-os"),
        tags=skill_metadata.get("tags", []),
        category=skill_metadata.get("category", "legacy"),
        migration_source=script_module.__name__,
    )

    skill = SkillSchema(
        name=name,
        version=version,
        description=description,
        inputs=inputs,
        outputs=outputs,
        execute=execute_fn,
        routing_conditions=skill_metadata.get("routing_conditions", []),
        memory_updates=skill_metadata.get("memory_updates", []),
        governance_level=skill_metadata.get("governance_level", "ALLOW"),
        observability_hooks=skill_metadata.get("observability_hooks", ["log_execution"]),
        metadata=metadata,
    )

    logger.info(
        "Wrapped legacy script '%s' as skill '%s' v%s",
        script_module.__name__, name, version,
    )
    return skill
