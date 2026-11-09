"""Synthesize deliberation stages into a final result."""

from __future__ import annotations

from typing import Any


def synthesize(
    *,
    task: str,
    mode: str,
    children: list[dict[str, Any]],
    judge: dict[str, Any],
    verification: list[dict[str, str]],
    trace_id: str,
    guardian_required: bool,
) -> dict[str, Any]:
    final_answer = (
        "ASI Deliberation Layer completed as a governed structured deliberation flow: "
        "triage, independent children, judge, verifier, synthesizer, and trace persistence."
    )
    next_actions = ["Run focused tests", "Review trace output for redaction"]
    risks = sorted({risk for child in children for risk in child.get("risks", [])})
    if guardian_required:
        risks.append("Guardian review required before state-changing execution")
        next_actions.insert(0, "Obtain Guardian approval before mutation or provider invocation")
    return {
        "final_answer": final_answer,
        "confidence": "medium",
        "mode": mode,
        "children_used": [child.get("role", "unknown") for child in children],
        "consensus": judge.get("consensus", []),
        "disagreements": judge.get("disagreements", []),
        "verification_summary": verification,
        "risks": risks,
        "next_actions": next_actions,
        "guardian_warnings": ["Guardian required"] if guardian_required else [],
        "trace_id": trace_id,
    }
