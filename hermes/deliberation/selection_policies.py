"""Child selection policies by task class."""

SELECTION_POLICIES: dict[str, list[str]] = {
    "architecture": ["SystemArchitect", "RiskAnalyst", "SecurityReviewer"],
    "coding": ["ImplementationEngineer", "TestEngineer"],
    "debugging": ["ImplementationEngineer", "TestEngineer", "PerformanceEngineer"],
    "provider_policy": ["GovernanceReviewer", "PolicyReviewer", "RiskAnalyst"],
    "security": ["SecurityReviewer", "VerificationSpecialist", "RiskAnalyst"],
    "credential_sensitive": ["SecurityReviewer", "GuardianAdvisor", "VerificationSpecialist"],
    "memory_mutation": ["GovernanceReviewer", "GuardianAdvisor", "VerificationSpecialist"],
    "state_changing": ["GuardianAdvisor", "RiskAnalyst", "GovernanceReviewer"],
    "research_analysis": ["ResearchAnalyst", "VerificationSpecialist", "CostController"],
    "implementation_review": ["ImplementationEngineer", "TestEngineer", "SecurityReviewer"],
}
