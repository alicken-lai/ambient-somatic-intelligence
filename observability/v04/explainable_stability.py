"""Human-readable stability explanations — dominant failure and contributions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.entropy.entropy_controller import EntropyReport
from observability.v04.stability_breakdown import build_stability_breakdown
from observability.v04.stability_score import GATE_THRESHOLD, compute_stability


@dataclass
class DimensionContribution:
    name: str
    dimension_value: float
    weight: float
    contribution: float
    pressure: float
    gap_to_perfect: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "dimension_value": round(self.dimension_value, 4),
            "weight": self.weight,
            "contribution": round(self.contribution, 6),
            "pressure": round(self.pressure, 4),
            "gap_to_perfect": round(self.gap_to_perfect, 6),
        }


@dataclass
class StabilityExplanation:
    score: float
    gate_pass: bool
    gate_threshold: float
    dominant_failure: str | None
    summary: str
    contributions: list[DimensionContribution] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "gate_pass": self.gate_pass,
            "gate_threshold": self.gate_threshold,
            "dominant_failure": self.dominant_failure,
            "summary": self.summary,
            "contributions": [c.to_dict() for c in self.contributions],
            "evidence": self.evidence,
        }


def explain_stability(
    entropy_report: EntropyReport,
    *,
    runtime_reproducibility: float | None = None,
) -> StabilityExplanation:
    """Rank dimensions by weighted gap to 1.0; surface dominant drag."""
    report = compute_stability(entropy_report, runtime_reproducibility=runtime_reproducibility)
    breakdown = build_stability_breakdown(
        entropy_report, runtime_reproducibility=runtime_reproducibility
    )

    contributions: list[DimensionContribution] = []
    for child in breakdown.root.children:
        dim_val = child.value
        gap = (1.0 - dim_val) * child.weight
        contributions.append(
            DimensionContribution(
                name=child.name,
                dimension_value=dim_val,
                weight=child.weight,
                contribution=child.contribution,
                pressure=breakdown.pressures.get(child.name, 1.0 - dim_val),
                gap_to_perfect=gap,
            )
        )

    contributions.sort(key=lambda c: c.gap_to_perfect, reverse=True)
    dominant = contributions[0].name if contributions and contributions[0].gap_to_perfect > 0 else None

    if report.gate_pass:
        summary = f"Stability gate PASS at {report.score:.4f} (≥ {GATE_THRESHOLD})."
    elif dominant:
        summary = (
            f"Stability gate FAIL at {report.score:.4f}; "
            f"largest drag: {dominant} (weighted gap {contributions[0].gap_to_perfect:.4f})."
        )
    else:
        summary = f"Stability gate FAIL at {report.score:.4f}."

    return StabilityExplanation(
        score=report.score,
        gate_pass=report.gate_pass,
        gate_threshold=GATE_THRESHOLD,
        dominant_failure=dominant if not report.gate_pass else None,
        summary=summary,
        contributions=contributions,
        evidence=dict(report.evidence),
    )
