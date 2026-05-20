"""Reflection boundary — limits what meta-cognition may assess."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observability.v04.metric_normalizer import clamp01


@dataclass
class ReflectionBoundaryVerdict:
    within_bounds: bool
    pressure: float = 0.0
    violations: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "within_bounds": self.within_bounds,
            "pressure": round(self.pressure, 4),
            "violations": list(self.violations or []),
            "disclaimer": "reflection_advisory_not_introspection_claim",
        }


class ReflectionBoundary:
    """Blocks reflection on protected surfaces (Guardian, constitution core)."""

    PROTECTED_PREFIXES = ("guardian", "constitutional_mutation", "ontology_core")

    def pressure(self, *, route_name: str, metadata: dict[str, Any] | None = None) -> float:
        meta = dict(metadata or {})
        violations: list[str] = []
        lower_route = route_name.lower()
        for prefix in self.PROTECTED_PREFIXES:
            if prefix in lower_route:
                violations.append(f"protected_route:{prefix}")
        if meta.get("reflect_guardian_internals"):
            violations.append("guardian_internals_forbidden")
        if meta.get("recursive_self_modify"):
            violations.append("self_modification_forbidden")
        if not violations:
            return 0.0
        return clamp01(0.35 + 0.15 * len(violations))

    def evaluate(
        self, *, route_name: str, metadata: dict[str, Any] | None = None
    ) -> ReflectionBoundaryVerdict:
        p = self.pressure(route_name=route_name, metadata=metadata)
        violations: list[str] = []
        lower_route = route_name.lower()
        for prefix in self.PROTECTED_PREFIXES:
            if prefix in lower_route:
                violations.append(f"protected_route:{prefix}")
        meta = dict(metadata or {})
        if meta.get("reflect_guardian_internals"):
            violations.append("guardian_internals_forbidden")
        if meta.get("recursive_self_modify"):
            violations.append("self_modification_forbidden")
        return ReflectionBoundaryVerdict(
            within_bounds=p < 0.35,
            pressure=p,
            violations=violations or None,
        )
