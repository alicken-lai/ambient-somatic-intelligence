"""Dynamic child role registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ChildRole:
    name: str
    capabilities: list[str]
    strengths: list[str]
    weaknesses: list[str]
    recommended_task_classes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "capabilities": self.capabilities,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommended_task_classes": self.recommended_task_classes,
        }


ROLE_REGISTRY: dict[str, ChildRole] = {
    "SystemArchitect": ChildRole("SystemArchitect", ["architecture", "interfaces"], ["system boundaries"], ["low-level test details"], ["architecture", "research_analysis"]),
    "SecurityReviewer": ChildRole("SecurityReviewer", ["security", "credential_review"], ["threat modeling"], ["product tradeoffs"], ["credential_sensitive", "state_changing", "implementation_review"]),
    "RiskAnalyst": ChildRole("RiskAnalyst", ["risk", "failure_modes"], ["downside discovery"], ["implementation speed"], ["architecture", "provider_policy", "state_changing"]),
    "PerformanceEngineer": ChildRole("PerformanceEngineer", ["latency", "resource_cost"], ["bottleneck analysis"], ["policy nuance"], ["debugging", "implementation_review"]),
    "ImplementationEngineer": ChildRole("ImplementationEngineer", ["coding", "interfaces"], ["practical implementation"], ["governance depth"], ["debugging", "implementation_review"]),
    "TestEngineer": ChildRole("TestEngineer", ["testing", "regression"], ["test design"], ["architecture vision"], ["debugging", "implementation_review"]),
    "GovernanceReviewer": ChildRole("GovernanceReviewer", ["governance", "guardian"], ["policy compliance"], ["performance tuning"], ["provider_policy", "memory_mutation", "state_changing"]),
    "GuardianAdvisor": ChildRole("GuardianAdvisor", ["guardian", "approval_flow"], ["safety escalation"], ["feature velocity"], ["memory_mutation", "credential_sensitive", "state_changing"]),
    "VerificationSpecialist": ChildRole("VerificationSpecialist", ["verification", "evidence"], ["claim checking"], ["open-ended ideation"], ["research_analysis", "credential_sensitive", "implementation_review"]),
    "CostController": ChildRole("CostController", ["cost", "roi"], ["allocation efficiency"], ["deep security"], ["provider_policy", "research_analysis"]),
    "ResearchAnalyst": ChildRole("ResearchAnalyst", ["research", "analysis"], ["evidence synthesis"], ["code patching"], ["research_analysis", "architecture"]),
    "PolicyReviewer": ChildRole("PolicyReviewer", ["policy", "provider_governance"], ["rules interpretation"], ["latency tuning"], ["provider_policy", "credential_sensitive"]),
}


def get_role_registry() -> dict[str, ChildRole]:
    return dict(ROLE_REGISTRY)
