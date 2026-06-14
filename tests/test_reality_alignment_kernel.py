from pathlib import Path

from hermes.deliberation.knowledge_graph import DeliberationKnowledgeGraph
from hermes.reality_alignment import BeliefRegistry, RealityAlignmentEngine, RealityObservation, RealityTarget
from hermes.reality_alignment.belief_evolution import evolve_belief
from hermes.reality_alignment.challenge_engine import RealityChallengeEngine
from hermes.reality_alignment.echo_chamber_detector import detect_echo_chamber
from hermes.reality_alignment.external_validation import ExternalValidationRegistry
from hermes.reality_alignment.knowledge_diversity import measure_knowledge_diversity
from hermes.reality_alignment.reality_models import Belief, ValidationOutcome, ValidationSource
from hermes.reality_alignment.reality_score import compute_reality_score
from hermes.reality_alignment.reports import generate_diversity_report, generate_fitness_report, generate_reality_report


def test_reality_score_uses_external_observations() -> None:
    target = RealityTarget(
        target_id="playbook:architecture_review",
        target_type="playbook",
        statement="Architecture review improves quality.",
        confidence=0.9,
        trust_score=0.85,
        verification_success=0.8,
        historical_quality=0.7,
        outcome_quality=0.75,
        sources=["internal:playbook", "pytest:architecture"],
    )
    observation = RealityObservation(
        observation_id="obs:1",
        target_id=target.target_id,
        source_type="external",
        agreement=0.8,
        outcome_quality=0.75,
        verification_success=True,
    )
    score = compute_reality_score(target, [observation])
    assert score["reality_score"] >= 75
    assert "external_agreement=0.80" in score["reasoning"]


def test_diversity_and_echo_risk_detect_internal_concentration() -> None:
    targets = [
        RealityTarget(
            target_id=f"belief:{idx}",
            target_type="belief",
            statement="Internal claim",
            confidence=0.95,
            trust_score=0.9,
            sources=["reports/trust_registry.json"],
        )
        for idx in range(3)
    ]
    diversity = measure_knowledge_diversity(targets)
    echo = detect_echo_chamber(confidence=0.95, trust=0.9, diversity_score=diversity["diversity_score"], self_reference=diversity["internal_ratio"])
    assert diversity["internal_ratio"] == 1.0
    assert echo["echo_risk"] >= 0.7


def test_challenge_engine_challenges_strong_targets() -> None:
    weak = RealityTarget("weak", "belief", "Weak belief", 0.2, trust_score=0.2)
    strong = RealityTarget("strong", "belief", "Strong belief", 0.95, trust_score=0.95, verification_success=0.9, outcome_quality=0.9)
    results = RealityChallengeEngine().challenge([weak, strong], limit=1)
    assert len(results) == 1
    assert results[0].target_id == "strong"
    assert "high-trust" in results[0].challenged_because


def test_belief_evolution_reduces_failed_beliefs() -> None:
    belief = Belief("belief:strong", "Strong claim", 0.9, 80.0, source_target_id="strong")
    challenge = RealityChallengeEngine().challenge(
        [RealityTarget("strong", "belief", "Strong claim", 0.9, trust_score=0.95, verification_success=0.1, outcome_quality=0.1)],
        limit=1,
    )
    evolved = evolve_belief(belief, challenge)
    assert evolved.challenge_count == 1
    assert evolved.confidence < belief.confidence
    assert evolved.status in {"reverify", "retire_recommended"}


def test_external_validation_registry_is_advisory_only(tmp_path: Path) -> None:
    registry = ExternalValidationRegistry(tmp_path / "external_validation.json")
    payload = registry.register_source(ValidationSource("benchmarks", "Benchmark suite", "benchmark", capabilities=["score"]))
    assert payload["sources"]["benchmarks"]["advisory_only"] is True
    outcome = ValidationOutcome("outcome:1", "benchmarks", "target:1", agreement=0.8, outcome_quality=0.7)
    payload = registry.record_outcome(outcome)
    assert payload["outcomes"][0]["target_id"] == "target:1"


def test_alignment_engine_tracks_beliefs_and_governance(tmp_path: Path) -> None:
    engine = RealityAlignmentEngine(belief_registry=BeliefRegistry(tmp_path / "belief_registry.json"))
    payload = engine.align()
    assert payload["targets"]
    assert payload["beliefs"]
    assert payload["reality_score"] >= 0
    assert payload["governance"]["advisory_only"] is True
    assert payload["governance"]["may_override_guardian"] is False


def test_reality_reports_and_graph_integration(tmp_path: Path) -> None:
    reality = generate_reality_report(tmp_path / "reality.md")
    diversity = generate_diversity_report(tmp_path / "diversity.md")
    fitness = generate_fitness_report(tmp_path / "fitness.md")
    assert Path(reality["report_path"]).is_file()
    assert Path(diversity["report_path"]).is_file()
    assert Path(fitness["report_path"]).is_file()
    graph = DeliberationKnowledgeGraph().add_reality_alignment_assets(
        beliefs=reality["beliefs"],
        reality_scores=reality["scores"],
        fitness_scores=fitness["fitness"],
        challenge_events=reality["challenges"],
        diversity_metrics=diversity["diversity"],
        validation_outcomes=[],
    )
    assert graph.query("Beliefs", "contains")
    assert graph.query("DiversityMetrics", "has_diversity_score")
