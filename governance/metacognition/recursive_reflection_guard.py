"""Recursive reflection guard — blocks reflection-on-reflection loops."""

from __future__ import annotations

from observability.v04.metric_normalizer import clamp01


class RecursiveReflectionGuard:
    BLOCKED_ROUTES = frozenset({
        "metacognitive_reflect",
        "reflection_on_reflection",
        "recursive_metacognition",
    })

    def __init__(self) -> None:
        self._chain: list[str] = []

    def block_recursive_route(self, route_name: str) -> bool:
        lower = route_name.lower()
        if lower in self.BLOCKED_ROUTES:
            return True
        if len(self._chain) >= 2 and all("reflect" in r for r in self._chain[-2:]):
            if "reflect" in lower:
                return True
        return False

    def record(self, route_name: str) -> None:
        self._chain.append(route_name.lower())
        if len(self._chain) > 8:
            self._chain = self._chain[-8:]

    def pressure(self, route_name: str) -> float:
        if self.block_recursive_route(route_name):
            return 0.9
        recent_reflect = sum(1 for r in self._chain[-4:] if "reflect" in r)
        return clamp01(recent_reflect * 0.2)
