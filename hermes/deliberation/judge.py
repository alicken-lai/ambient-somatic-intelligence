"""Judge stage for deliberation outputs."""

from __future__ import annotations

from typing import Any


def judge_children(children: list[dict[str, Any]], *, guardian_required: bool = False) -> dict[str, Any]:
    roles = [child.get("role", "unknown") for child in children]
    risks = sorted({risk for child in children for risk in child.get("risks", [])})
    verification = sorted({item for child in children for item in child.get("verification_needed", [])})
    recommended_next_step = "guardian_review" if guardian_required else ("verify" if verification else "single_answer")
    return {
        "consensus": [
            "Use structured JSON boundaries between children, judge, verifier, and synthesizer.",
            "Configured CLI providers must be discovered and health checked before use.",
        ],
        "disagreements": [],
        "unique_insights": [f"{role} contributed independent role-specific analysis" for role in roles],
        "unsupported_claims": verification,
        "shared_blindspots": ["No live provider output should be treated as verified without allowed-tool evidence."],
        "missing_questions": [],
        "task_reframe_needed": False,
        "unsafe_or_state_changing_actions": risks if guardian_required else [],
        "recommended_next_step": recommended_next_step,
    }
