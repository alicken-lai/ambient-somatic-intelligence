"""Bounded cognition — prevent domain monopolization and governance recursion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01

MAX_DOMAIN_SHARE = 0.45
MAX_GOVERNANCE_DEPTH = 2
FORBIDDEN_RECURSIVE_ROUTES = frozenset({"governance_on_governance", "cognitive_self_loop"})


@dataclass
class SovereigntyLimits:
    max_domain_share: float = MAX_DOMAIN_SHARE
    max_governance_depth: int = MAX_GOVERNANCE_DEPTH

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_domain_share": self.max_domain_share,
            "max_governance_depth": self.max_governance_depth,
        }


@dataclass
class SovereigntyReport:
    compliant: bool
    max_share_observed: float
    monopolization_violation: bool
    governance_depth_ok: bool
    recursive_route_blocked: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "compliant": self.compliant,
            "max_share_observed": round(self.max_share_observed, 4),
            "monopolization_violation": self.monopolization_violation,
            "governance_depth_ok": self.governance_depth_ok,
            "recursive_route_blocked": self.recursive_route_blocked,
            "violations": list(self.violations),
        }


class SovereigntyLimitsChecker:
    """Enforce bounded domain share and shallow governance depth."""

    def __init__(self, limits: SovereigntyLimits | None = None) -> None:
        self.limits = limits or SovereigntyLimits()

    def check_domain_shares(self, shares: dict[str, float]) -> SovereigntyReport:
        if not shares or len(shares) <= 1:
            return SovereigntyReport(
                compliant=True,
                max_share_observed=max(shares.values()) if shares else 0.0,
                monopolization_violation=False,
                governance_depth_ok=True,
                recursive_route_blocked=True,
            )
        total = sum(shares.values()) or 1.0
        normalized = {k: v / total for k, v in shares.items()}
        max_share = max(normalized.values())
        mono = max_share > self.limits.max_domain_share
        violations: list[str] = []
        if mono:
            violations.append("domain_monopolization")
        return SovereigntyReport(
            compliant=not mono,
            max_share_observed=max_share,
            monopolization_violation=mono,
            governance_depth_ok=True,
            recursive_route_blocked=True,
            violations=violations,
        )

    def check_governance_depth(self, depth: int) -> bool:
        return depth <= self.limits.max_governance_depth

    def block_recursive_route(self, route_name: str) -> bool:
        return route_name not in FORBIDDEN_RECURSIVE_ROUTES

    def compliance_score(self, shares: dict[str, float], *, depth: int = 0) -> float:
        report = self.check_domain_shares(shares)
        depth_ok = self.check_governance_depth(depth)
        if report.monopolization_violation or not depth_ok:
            return 0.5
        headroom = 1.0 - report.max_share_observed / self.limits.max_domain_share
        return clamp01(0.85 + headroom * 0.15)
