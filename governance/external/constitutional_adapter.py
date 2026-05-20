"""Adapt external doctrine to constitutional context — advisory compatibility only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.constitution.constitutional_guard import ConstitutionalContext, ConstitutionalGuard
from governance.external.doctrine_filter import DoctrineFilter, DoctrineFilterResult


@dataclass
class ConstitutionalAdaptation:
    compatible: bool
    compliance_score: float
    filter_result: DoctrineFilterResult
    constitutional_compliant: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "compatible": self.compatible,
            "compliance_score": round(self.compliance_score, 4),
            "filter": self.filter_result.to_dict(),
            "constitutional_compliant": self.constitutional_compliant,
            "notes": list(self.notes),
        }


class ConstitutionalAdapter:
    """Maps filtered external text to constitutional checks — never mutates constitution."""

    def __init__(self) -> None:
        self.filter = DoctrineFilter()
        self.guard = ConstitutionalGuard()

    def adapt(
        self,
        text: str,
        *,
        route_name: str = "external_skill_mount",
        metadata: dict[str, Any] | None = None,
    ) -> ConstitutionalAdaptation:
        meta = dict(metadata or {})
        filtered = self.filter.filter(text)
        notes: list[str] = []
        if filtered.violations:
            notes.append("doctrine_violations_detected")

        weaken = any(v in filtered.violations for v in ("guardian_bypass", "constitutional_override"))
        ctx = ConstitutionalContext(
            route_name=route_name,
            raw_confidence=0.5,
            uncertainty=0.5,
            weaken_guardian=weaken,
            guardian_bypass_attempt=weaken,
            metadata=meta,
        )
        verdict = self.guard.evaluate(ctx)
        constitutional_ok = verdict.compliant and filtered.safe

        score = 1.0
        if filtered.violations:
            score -= 0.15 * len(filtered.violations)
        if not verdict.compliant:
            score -= 0.35
        score = max(0.0, min(1.0, score))

        compatible = constitutional_ok and score >= 0.7
        if "sovereign_claim" in filtered.violations:
            compatible = False
            notes.append("sovereign_truth_rejected")

        return ConstitutionalAdaptation(
            compatible=compatible,
            compliance_score=score,
            filter_result=filtered,
            constitutional_compliant=constitutional_ok,
            notes=notes,
        )
