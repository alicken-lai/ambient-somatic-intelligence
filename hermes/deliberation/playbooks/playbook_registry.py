"""Playbook registry and defaults."""

from __future__ import annotations

from pathlib import Path
import json

from hermes.deliberation.playbooks.playbook_models import Playbook


class PlaybookRegistry:
    def __init__(self, path: str | Path = "reports/deliberation_playbook_registry.json"):
        self.path = Path(path)

    def load(self) -> dict[str, Playbook]:
        if not self.path.is_file():
            return default_playbooks()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {key: Playbook.from_dict(value) for key, value in raw.items()}

    def save(self, playbooks: dict[str, Playbook]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: value.to_dict() for key, value in playbooks.items()}
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def default_playbooks() -> dict[str, Playbook]:
    playbooks = [
        Playbook("architecture_review", "Architecture Review Playbook", ["architecture"], ["SystemArchitect", "RiskAnalyst", "SecurityReviewer"], "deep", [], ["trace complete", "risks identified"], ["missing verification"]),
        Playbook("provider_policy", "Provider Policy Playbook", ["provider_policy"], ["GovernanceReviewer", "PolicyReviewer", "RiskAnalyst"], "deep", ["provider permissions immutable"], ["disabled providers not invoked"], ["hidden quota use"]),
        Playbook("security_audit", "Security Audit Playbook", ["credential_sensitive", "state_changing"], ["SecurityReviewer", "GuardianAdvisor", "VerificationSpecialist"], "deep", ["Guardian required for risky actions"], ["secrets redacted"], ["credential leakage"]),
        Playbook("implementation_review", "Implementation Review Playbook", ["implementation_review", "debugging"], ["ImplementationEngineer", "TestEngineer", "SecurityReviewer"], "standard", [], ["tests pass"], ["regression risk"]),
        Playbook("research_synthesis", "Research Synthesis Playbook", ["research_analysis"], ["ResearchAnalyst", "VerificationSpecialist", "CostController"], "deep", [], ["sources verified"], ["unsupported claims"]),
    ]
    return {playbook.playbook_id: playbook for playbook in playbooks}
