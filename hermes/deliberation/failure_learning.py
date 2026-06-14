"""Failure learning for deliberation outcomes."""

from __future__ import annotations

from collections import Counter
from typing import Any


FAILURE_FIXES = {
    "unsupported_claim": "Increase verifier evidence coverage before synthesis.",
    "guardian_required": "Preserve Guardian review and avoid ROI-based bypass.",
    "low_roi": "Prefer lighter strategy or collect more evidence before promotion.",
    "trace_incomplete": "Block promotion until trace integrity is complete.",
}


def learn_failures(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for result in results:
        for mode, metrics in result.get("metrics", {}).items():
            if metrics.get("unsupported_claim_count", 0) > 0:
                counts["unsupported_claim"] += 1
            if metrics.get("guardian_triggered"):
                counts["guardian_required"] += 1
            if result.get("scorecards", {}).get(mode, {}).get("overall_score", 100) < 50:
                counts["low_roi"] += 1
            if metrics.get("decision_trace_completeness", 1) < 0.9:
                counts["trace_incomplete"] += 1
    return [
        {
            "failure_type": failure_type,
            "root_cause": _root_cause(failure_type),
            "recommended_fix": FAILURE_FIXES[failure_type],
            "frequency": frequency,
        }
        for failure_type, frequency in counts.most_common()
    ]


def _root_cause(failure_type: str) -> str:
    return {
        "unsupported_claim": "Claims reached synthesis without enough allowed-tool evidence.",
        "guardian_required": "Task touched a non-optimizable governance boundary.",
        "low_roi": "Extra deliberation cost was not justified by score gain.",
        "trace_incomplete": "Audit fields were missing or malformed.",
    }[failure_type]
