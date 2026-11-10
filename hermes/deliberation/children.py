"""Independent child roles for ASI deliberation."""

from __future__ import annotations

from typing import Any


DEFAULT_ROLES = {
    "engineering_child": "implementation, architecture, interfaces, failure handling",
    "risk_child": "failure modes, security, cost, latency, policy violations",
    "verification_child": "assumptions, unsupported claims, tests, evidence, validation",
}


def run_children(task: str, *, mode: str = "light", max_children: int = 3) -> list[dict[str, Any]]:
    role_names = ["engineering_child", "risk_child"]
    if mode in {"full", "guardian_required"}:
        role_names.append("verification_child")
    role_names = role_names[:max_children]
    return [run_child(role, task) for role in role_names]


def run_child(role: str, task: str) -> dict[str, Any]:
    if role == "engineering_child":
        answer = "Define small provider, deliberation, trace, and CLI modules with typed structured boundaries."
        assumptions = ["Existing Hermes conventions should be preserved.", "Callable providers expose explicit command or endpoint interfaces."]
        risks = ["Provider invocation may become unsafe if arbitrary CLI args are accepted."]
        tests = ["provider discovery", "disabled provider handling", "deliberation result schema"]
    elif role == "risk_child":
        answer = "Keep CLIs disabled until health checked, fail closed on state changes, and redact traces before persistence."
        assumptions = ["Guardian review is required before mutations, shell execution, provider changes, memory writes, and deployments."]
        risks = ["Hidden IDE quota use", "secret leakage in traces", "majority-vote hallucination"]
        tests = ["trace redaction", "Guardian trigger", "timeout handling"]
    else:
        answer = "Separate claims into verified, contradicted, unsupported, and not_checked; avoid fabricating evidence."
        assumptions = ["Verifier only checks facts available through allowed tools."]
        risks = ["Self-verification", "unsupported claims preserved as certainty"]
        tests = ["verifier claim status", "synthesizer preserves uncertainty"]
    return {
        "role": role,
        "answer": answer,
        "assumptions": assumptions,
        "risks": risks,
        "verification_needed": ["Confirm installed CLI availability from PATH", "Confirm tests pass in the current repo"],
        "recommended_tests": tests,
        "confidence": "medium",
    }
