"""Task triage for the ASI Deliberation Layer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TriageResult:
    labels: list[str] = field(default_factory=list)
    route_mode: str = "single"
    reason: str = ""
    guardian_required: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "labels": self.labels,
            "route_mode": self.route_mode,
            "reason": self.reason,
            "guardian_required": self.guardian_required,
        }


ROUTING = {
    "simple": "single",
    "uncertain": "light",
    "architecture": "full",
    "coding": "light",
    "debugging": "light",
    "safety_sensitive": "guardian_required",
    "state_changing": "guardian_required",
    "provider_policy": "full",
    "memory_mutation": "guardian_required",
    "credential_sensitive": "guardian_required",
}


def triage_task(task: str) -> TriageResult:
    text = task.lower()
    labels: list[str] = []
    if any(
        word in text
        for word in [
            "delete",
            "write",
            "modify",
            "edit",
            "commit",
            "push",
            "deploy",
            "install",
            "shell",
            "command",
            "run",
            "network",
            "expose",
            "refactor",
            "rotate",
        ]
    ):
        labels.append("state_changing")
    if any(word in text for word in ["api key", "token", "secret", "credential", "password"]):
        labels.append("credential_sensitive")
    if any(word in text for word in ["memory", "dmn", "append", "promote"]):
        labels.append("memory_mutation")
    if any(word in text for word in ["provider", "cli", "quota", "openrouter", "copilot"]):
        labels.append("provider_policy")
    if any(word in text for word in ["architecture", "design", "layer", "orchestrat"]):
        labels.append("architecture")
    if any(word in text for word in ["implement", "code", "test", "module", "class", "function"]):
        labels.append("coding")
    if any(word in text for word in ["bug", "debug", "failure", "traceback"]):
        labels.append("debugging")
    if any(word in text for word in ["maybe", "uncertain", "compare", "review"]):
        labels.append("uncertain")
    if not labels:
        labels.append("simple")

    for label in ("credential_sensitive", "memory_mutation", "state_changing", "safety_sensitive"):
        if label in labels:
            return TriageResult(labels=labels, route_mode="guardian_required", reason=f"{label} requires Guardian", guardian_required=True)
    if "provider_policy" in labels:
        return TriageResult(labels=labels, route_mode="full", reason="provider governance requires full review")
    if "architecture" in labels:
        return TriageResult(labels=labels, route_mode="full", reason="architecture task benefits from verifier")
    if "coding" in labels or "debugging" in labels or "uncertain" in labels:
        return TriageResult(labels=labels, route_mode="light", reason="non-trivial task needs independent children")
    return TriageResult(labels=labels, route_mode="single", reason="simple task")
