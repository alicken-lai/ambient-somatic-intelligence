"""Single-source capability registry for provider orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping


@dataclass(frozen=True)
class CapabilitySpec:
    name: str
    material_action: bool = False
    tool_exposure: bool = False
    description: str = ""


_SPECS = {
    spec.name: spec
    for spec in (
        CapabilitySpec("terminal", True, True),
        CapabilitySpec("filesystem", True, True),
        CapabilitySpec("local_file_access", True, True),
        CapabilitySpec("repo_edit", True, True),
        CapabilitySpec("mcp_tools", True, True),
        CapabilitySpec("test_runner", True, True),
        CapabilitySpec("local_sensitive", True, True),
        CapabilitySpec("codebase_context"),
        CapabilitySpec("general_reasoning"),
        CapabilitySpec("codebase_analysis"),
        CapabilitySpec("architecture_design"),
        CapabilitySpec("long_context"),
        CapabilitySpec("creative_generation"),
        CapabilitySpec("fast_answer"),
        CapabilitySpec("cheap_batch"),
        CapabilitySpec("refactor"),
        CapabilitySpec("diff_generation"),
        CapabilitySpec("long_reasoning"),
        CapabilitySpec("writing"),
        CapabilitySpec("architecture_review"),
        # Legacy provider vocabulary remains registered for compatibility.
        CapabilitySpec("reasoning"),
        CapabilitySpec("coding"),
        CapabilitySpec("synthesis"),
        CapabilitySpec("repo_context"),
        CapabilitySpec("critique"),
        CapabilitySpec("web"),
        CapabilitySpec("realtime_context"),
    )
}

CAPABILITY_REGISTRY: Mapping[str, CapabilitySpec] = MappingProxyType(_SPECS)
KNOWN_CAPABILITIES = frozenset(CAPABILITY_REGISTRY)
TOOL_EXPOSURE_CAPABILITIES = frozenset(
    name for name, spec in CAPABILITY_REGISTRY.items() if spec.tool_exposure
)
MATERIAL_ACTION_CAPABILITIES = frozenset(
    name for name, spec in CAPABILITY_REGISTRY.items() if spec.material_action
)


def authorization_requirement_for(name: str) -> str:
    """Material capabilities require Guardian. The model does not choose this."""

    spec = CAPABILITY_REGISTRY[name]
    if spec.material_action:
        return "guardian_allow_required"
    return "not_material"


def validate_capabilities(values: Iterable[str], *, tool_exposure_only: bool = False) -> frozenset[str]:
    """Return normalized capabilities or fail closed on unknown vocabulary."""

    normalized = frozenset(str(value) for value in values)
    allowed = TOOL_EXPOSURE_CAPABILITIES if tool_exposure_only else KNOWN_CAPABILITIES
    unknown = sorted(normalized.difference(allowed))
    if unknown:
        kind = "tool exposure " if tool_exposure_only else ""
        raise ValueError(f"unknown {kind}capabilities: {', '.join(unknown)}")
    return normalized

