# Playbook Report

## Top Playbooks

| Playbook | Task Types | Children | Verification | Guardian Requirements |
| --- | --- | --- | --- | --- |
| Architecture Review Playbook | architecture | SystemArchitect, RiskAnalyst, SecurityReviewer | deep | none |
| Provider Policy Playbook | provider_policy | GovernanceReviewer, PolicyReviewer, RiskAnalyst | deep | provider permissions immutable |
| Security Audit Playbook | credential_sensitive, state_changing | SecurityReviewer, GuardianAdvisor, VerificationSpecialist | deep | Guardian required for risky actions |
| Implementation Review Playbook | implementation_review, debugging | ImplementationEngineer, TestEngineer, SecurityReviewer | standard | none |
| Research Synthesis Playbook | research_analysis | ResearchAnalyst, VerificationSpecialist, CostController | deep | none |

## Promotion Candidates

- Architecture Deliberation Skill: consistent ROI improvement
- Debugging Deliberation Skill: consistent ROI improvement
- Provider Policy Deliberation Skill: consistent ROI improvement
- Research Analysis Deliberation Skill: consistent ROI improvement

## Retirement Candidates

- Memory Mutation Deliberation Skill: weak success and ROI trend
- State Changing Deliberation Skill: weak success and ROI trend
