"""Reflection balancer — cap meta-reflection load observational hints."""

from __future__ import annotations

from typing import Any

from observability.v04.metric_normalizer import clamp01


class ReflectionBalancer:
    LOAD_THRESHOLD = 0.40

    def load(
        self,
        *,
        introspection_pressure: float = 0.0,
        recursive_pressure: float = 0.0,
        boundary_pressure: float = 0.0,
        degradation_pressure: float = 0.0,
    ) -> float:
        return clamp01(
            introspection_pressure * 0.30
            + recursive_pressure * 0.30
            + boundary_pressure * 0.25
            + degradation_pressure * 0.15
        )

    def recommend(
        self,
        *,
        introspection_pressure: float = 0.0,
        recursive_pressure: float = 0.0,
        boundary_pressure: float = 0.0,
        degradation_pressure: float = 0.0,
    ) -> list[str]:
        load = self.load(
            introspection_pressure=introspection_pressure,
            recursive_pressure=recursive_pressure,
            boundary_pressure=boundary_pressure,
            degradation_pressure=degradation_pressure,
        )
        if load < self.LOAD_THRESHOLD:
            return []
        recs = ["defer_secondary_reflection_until_load_drops"]
        if recursive_pressure >= 0.5:
            recs.append("avoid_recursive_reflection_routes")
        return recs

    def assess(
        self,
        *,
        introspection_pressure: float = 0.0,
        recursive_pressure: float = 0.0,
        boundary_pressure: float = 0.0,
        degradation_pressure: float = 0.0,
    ) -> dict[str, Any]:
        load = self.load(
            introspection_pressure=introspection_pressure,
            recursive_pressure=recursive_pressure,
            boundary_pressure=boundary_pressure,
            degradation_pressure=degradation_pressure,
        )
        return {
            "reflection_load": round(load, 4),
            "balanced": load < self.LOAD_THRESHOLD,
            "recommendations": self.recommend(
                introspection_pressure=introspection_pressure,
                recursive_pressure=recursive_pressure,
                boundary_pressure=boundary_pressure,
                degradation_pressure=degradation_pressure,
            ),
            "disclaimer": "balance_advisory_only",
        }
