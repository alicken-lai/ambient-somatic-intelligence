"""Quality metrics for deliberation outputs."""

from __future__ import annotations

from typing import Any


CONFIDENCE_SCORE = {"low": 0.33, "medium": 0.66, "high": 1.0}


def calculate_metrics(result: dict[str, Any]) -> dict[str, float | int | bool]:
    verification = list(result.get("verification_summary", []))
    checked = [item for item in verification if item.get("status") in {"verified", "contradicted", "unsupported"}]
    verified = [item for item in verification if item.get("status") == "verified"]
    unsupported = [
        item
        for item in verification
        if item.get("status") in {"unsupported", "not_checked"}
    ]
    consensus = list(result.get("consensus", []))
    disagreements = list(result.get("disagreements", []))
    unique_insights = _unique_insights(result)
    blindspots = _blindspots(result)
    guardian_triggered = bool(result.get("guardian_warnings") or result.get("triage", {}).get("guardian_required"))
    trace_complete = _trace_completeness(result)
    verification_coverage = len(checked) / len(verification) if verification else 0.0
    verification_success_rate = len(verified) / len(checked) if checked else 0.0
    unsupported_ratio = len(unsupported) / max(1, len(verification))
    hallucination_risk = min(1.0, unsupported_ratio * 0.6 + (1.0 - verification_coverage) * 0.4)
    return {
        "blindspot_count": len(blindspots),
        "unsupported_claim_count": len(unsupported),
        "verification_coverage": round(verification_coverage, 4),
        "consensus_count": len(consensus),
        "disagreement_count": len(disagreements),
        "unique_insight_count": len(unique_insights),
        "guardian_triggered": guardian_triggered,
        "verification_success_rate": round(verification_success_rate, 4),
        "final_confidence_score": CONFIDENCE_SCORE.get(str(result.get("confidence", "low")), 0.33),
        "hallucination_risk_score": round(hallucination_risk, 4),
        "decision_trace_completeness": round(trace_complete, 4),
    }


def _unique_insights(result: dict[str, Any]) -> list[Any]:
    judge = result.get("judge_output", {})
    if isinstance(judge, dict):
        return list(judge.get("unique_insights", []))
    return list(result.get("unique_insights", []))


def _blindspots(result: dict[str, Any]) -> list[Any]:
    judge = result.get("judge_output", {})
    if isinstance(judge, dict):
        return list(judge.get("shared_blindspots", []))
    return list(result.get("shared_blindspots", []))


def _trace_completeness(result: dict[str, Any]) -> float:
    required = [
        "trace_id",
        "mode",
        "final_answer",
        "confidence",
        "children_used",
        "consensus",
        "verification_summary",
        "risks",
        "next_actions",
        "triage",
        "provider_discovery",
    ]
    present = sum(1 for key in required if key in result and result[key] not in (None, ""))
    return present / len(required)
