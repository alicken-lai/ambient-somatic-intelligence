from pathlib import Path

from hermes.deliberation.knowledge_graph import DeliberationKnowledgeGraph
from hermes.identity.belief_classification import classify_belief, classify_beliefs
from hermes.identity.coherence_score import compute_coherence_score
from hermes.identity.continuity_engine import analyze_continuity
from hermes.identity.identity_drift import detect_identity_drift
from hermes.identity.identity_evolution import validate_identity_change
from hermes.identity.identity_health import compute_identity_health
from hermes.identity.identity_models import IdentityChange, NarrativeEvent
from hermes.identity.identity_registry import IdentityRegistry, default_identity
from hermes.identity.life_history import build_life_history
from hermes.identity.reports import generate_continuity_report, generate_identity_report, generate_life_history_report


def test_identity_registry_makes_identity_first_class(tmp_path: Path) -> None:
    registry = IdentityRegistry(tmp_path / "identity.json")
    identity = registry.save(default_identity())
    loaded = registry.load()
    assert loaded.identity_id == identity.identity_id
    assert "do not bypass Guardian" in loaded.governance_commitments
    assert loaded.non_negotiable_constraints


def test_belief_classification_separates_identity_from_tactics() -> None:
    core = classify_belief({"belief_id": "b1", "statement": "Guardian governance remains authoritative", "confidence": 0.9, "reality_score": 80})
    experimental = classify_belief({"belief_id": "b2", "statement": "Try a new routing tactic", "confidence": 0.4, "reality_score": 40})
    retired = classify_belief({"belief_id": "b3", "statement": "Old tactic", "status": "retire_recommended"})
    assert core["classification"] == "Core Belief"
    assert experimental["classification"] == "Experimental Belief"
    assert retired["classification"] == "Retired Belief"


def test_continuity_drift_coherence_and_health() -> None:
    identity = default_identity()
    beliefs = {
        "b1": {"belief_id": "b1", "statement": "Guardian governance remains authoritative", "confidence": 0.9, "reality_score": 80},
        "b2": {"belief_id": "b2", "statement": "Temporary tactic", "confidence": 0.5, "reality_score": 50},
    }
    classifications = classify_beliefs(beliefs)
    events = [NarrativeEvent("e1", "beliefs", "Beliefs became tracked objects.", ["reports/belief_registry.json"], "major")]
    continuity = analyze_continuity(identity, events, classifications)
    drift = detect_identity_drift(identity, [*identity.governance_commitments, "Guardian governance remains authoritative"])
    coherence = compute_coherence_score(identity, classifications, continuity, drift)
    health = compute_identity_health(coherence=coherence, continuity=continuity, drift=drift, classifications=classifications)
    assert continuity["stable"]
    assert drift["drift_detected"] is False
    assert coherence["coherence_score"] > 70
    assert health["identity_health"] > 60


def test_identity_drift_detects_forbidden_change() -> None:
    drift = detect_identity_drift(default_identity(), ["We should override Guardian for speed."])
    assert drift["drift_detected"] is True
    assert drift["severity"] == "high"


def test_identity_evolution_requires_justification_and_evidence() -> None:
    rejected = validate_identity_change(IdentityChange("c1", "principle", "old", "new", "", []))
    accepted = validate_identity_change(IdentityChange("c2", "principle", "old", "new", "reality score changed", ["reports/reality_alignment_report.json"]))
    assert rejected["accepted_for_review"] is False
    assert accepted["accepted_for_review"] is True


def test_life_history_and_reports_generate(tmp_path: Path) -> None:
    identity = default_identity()
    events = [
        NarrativeEvent("phase-8", "reality", "Reality alignment challenged trusted beliefs.", ["reports/reality_alignment_report.json"], "major"),
        NarrativeEvent("phase-9", "beliefs", "Identity became a tracked object.", ["reports/identity_registry.json"], "major"),
    ]
    life = build_life_history(identity, events)
    assert "Guardian-governed" in life["biography"]
    assert life["event_count"] == 2
    identity_report = generate_identity_report(tmp_path / "identity.md")
    continuity_report = generate_continuity_report(tmp_path / "continuity.md")
    life_report = generate_life_history_report(tmp_path / "life.md")
    assert Path(identity_report["report_path"]).is_file()
    assert Path(continuity_report["report_path"]).is_file()
    assert Path(life_report["report_path"]).is_file()


def test_identity_graph_integration() -> None:
    identity = default_identity().to_dict()
    event = NarrativeEvent("phase-9", "identity", "Identity became first class.").to_dict()
    life = {"event_count": 1}
    graph = DeliberationKnowledgeGraph().add_identity_assets(
        identity=identity,
        narrative_events=[event],
        continuity={"stable": identity["governance_commitments"]},
        life_history=life,
    )
    assert graph.query("Identity", "contains")
    assert graph.query("NarrativeEvents", "contains")
