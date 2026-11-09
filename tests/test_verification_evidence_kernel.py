from __future__ import annotations

import json
import subprocess
import sys

from hermes.deliberation.observability import DeliberationMetricsCollector, build_dashboard_data
from hermes.verification.claim_graph import ClaimEvidenceGraph
from hermes.verification.claims import ClaimExtractor, ClaimRegistry
from hermes.verification.contradiction_detector import detect_contradiction
from hermes.verification.evidence import Evidence
from hermes.verification.evidence_scoring import evidence_score
from hermes.verification.reports import (
    generate_claim_report,
    generate_contradiction_report,
    generate_evidence_report,
    generate_verification_report,
    playbook_evidence_quality,
    recommended_verification_rules,
)
from hermes.verification.verification_discipline import verification_requirement
from hermes.verification.verification_pipeline import VerificationPipeline, evidence_for_claim


def test_claim_extraction_structures_claims() -> None:
    claims = ClaimExtractor().extract(
        {"answer": "Provider permissions are immutable. Architecture claims should be verified."},
        source="unit",
    )
    assert claims
    assert {claim.claim_type for claim in claims}.intersection({"policy", "architecture"})
    assert all(claim.claim_id for claim in claims)
    assert any(claim.verification_required for claim in claims)


def test_claim_registry_tracks_status_history(tmp_path) -> None:
    claims = ClaimExtractor().extract("Guardian approval is required for provider changes.", source="registry")
    registry = ClaimRegistry(tmp_path / "claims.json")
    registry.register(claims)
    record = registry.update_status(claims[0].claim_id, "verified", ["evidence-1"], "checked")
    assert record.status == "verified"
    assert record.verification_count == 1
    assert registry.load()[claims[0].claim_id].evidence == ["evidence-1"]


def test_evidence_object_links_to_claim() -> None:
    claim = ClaimExtractor().extract("Tests passed for provider orchestration.", source="evidence")[0]
    evidence = evidence_for_claim(claim, "tests", "pytest passed", 0.9)
    assert evidence.supports_claims == [claim.claim_id]
    assert evidence.confidence == 0.9


def test_claim_graph_queries_unsupported_sources() -> None:
    graph = ClaimEvidenceGraph()
    graph.add_claim("claim-a", "playbook:provider_policy")
    graph.add_claim("claim-b", "playbook:provider_policy")
    graph.link_evidence("claim-a", "evidence-a")
    assert graph.query("claim-a", "supported_by")[0]["target"] == "evidence-a"
    assert graph.unsupported_by_source(["claim-a", "claim-b"])[0]["unsupported_count"] == 2


def test_verification_discipline_requires_high_risk_claims() -> None:
    claim = ClaimExtractor().extract("Credential secrets require Guardian approval.", source="discipline")[0]
    requirement = verification_requirement(claim)
    assert requirement["required"] is True
    assert requirement["level"] == "required"


def test_verification_pipeline_classifies_supported_and_unsupported() -> None:
    artifact = {"answer": "Provider permissions are immutable. Unsupported policy claims require evidence."}
    pipeline = VerificationPipeline()
    claims = ClaimExtractor().extract(artifact, source="pipeline")
    evidence = [evidence_for_claim(claims[0], "reports", claims[0].claim_text, 0.95)]
    result = pipeline.run(artifact, source="pipeline", evidence=evidence)
    assert result["verified"]
    assert result["unsupported"]
    assert 0 <= result["evidence_score"] <= 100


def test_contradiction_detector_finds_guardian_conflict() -> None:
    claim = ClaimExtractor().extract("The system should proceed with provider policy changes.", source="guardian")[0]
    result = detect_contradiction(claim, guardian_status="BLOCK")
    assert result["contradiction"] is True
    assert result["severity"] == "high"


def test_evidence_score_penalizes_unsupported_claims() -> None:
    claims = ClaimExtractor().extract("Provider permissions are immutable. Security claims require evidence.", source="score")
    statuses = {claims[0].claim_id: "verified", claims[1].claim_id: "unsupported"}
    score = evidence_score(claims, [Evidence("e1", "tests", "passed", 0.9, [claims[0].claim_id])], statuses, [])
    assert 0 < score < 100


def test_playbook_evidence_quality_has_ratings() -> None:
    ratings = playbook_evidence_quality()
    assert ratings
    assert {"claim_count", "verified_claims", "unsupported_claims", "evidence_quality_rating"} <= set(ratings[0])


def test_failure_learning_recommends_verification_rules() -> None:
    rules = recommended_verification_rules()
    assert any("High-risk claims" in rule for rule in rules)


def test_verification_observability_fields(tmp_path) -> None:
    path = tmp_path / "metrics.jsonl"
    collector = DeliberationMetricsCollector(path)
    collector.record(
        {
            "claim_count": 10,
            "verification_rate": 0.7,
            "unsupported_claim_rate": 0.2,
            "evidence_score": 75,
            "contradiction_count": 1,
            "verification_latency_ms": 30,
            "playbook_evidence_quality": 60,
        }
    )
    kernel = build_dashboard_data(path)["verification_kernel"]
    assert kernel["claim_volume"] == 10
    assert kernel["verification_rate"] == 0.7
    assert kernel["evidence_score"] == 75


def test_verification_reports_generate(tmp_path) -> None:
    evidence = generate_evidence_report(tmp_path / "evidence.md")
    claim = generate_claim_report(tmp_path / "claim.md")
    verification = generate_verification_report(tmp_path / "verification.md")
    contradiction = generate_contradiction_report(tmp_path / "contradiction.md")
    assert evidence["claim_count"] > 0
    assert claim["claim_count"] > 0
    assert "confidence" in verification
    assert "contradiction_count" in contradiction


def test_verification_report_cli_json() -> None:
    for command in ("evidence-report", "claim-report", "verification-report", "contradiction-report"):
        completed = subprocess.run(
            [sys.executable, "scripts/hermes.py", command, "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert "report_path" in payload
