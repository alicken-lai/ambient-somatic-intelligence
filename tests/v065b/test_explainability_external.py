"""Area 6: External doctrine explainability."""

from attention.explainability.compatibility_explainer import CompatibilityExplainer
from attention.explainability.contamination_breakdown import ContaminationBreakdown
from attention.explainability.external_doctrine_reasoning import ExternalDoctrineReasoning
from governance.cognition.cognitive_governor import GovernanceDecision
from governance.cognition.arbitration_engine import ArbitrationResult
from hermes.skills.external.external_skill_registry import ExternalSkillRegistry


def test_external_doctrine_reasoning() -> None:
    d = GovernanceDecision(
        accepted=True,
        governed_salience=0.5,
        arbitration=ArbitrationResult(
            final_salience=0.5,
            arbitration_fairness=0.9,
            sovereignty_compliant=True,
            uncertainty_applied=False,
            replay_bounded=True,
            somatic_bounded=True,
            governance_depth=1,
        ),
    )
    out = ExternalDoctrineReasoning().explain_decision(
        d, external_advisory={"hints": ["karpathy-guidelines:advisory_ok"]}
    )
    assert "advisory" in out["summary"].lower()


def test_compatibility_explainer(external_registry) -> None:
    rec = external_registry.get("karpathy_guidelines")
    assert rec is not None
    exp = CompatibilityExplainer().explain_record(rec)
    assert "skill_id" in exp
