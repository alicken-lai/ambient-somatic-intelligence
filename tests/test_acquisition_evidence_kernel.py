from __future__ import annotations

import json
import subprocess
import sys

from hermes.acquisition.acquisition_pipeline import AcquisitionPipeline
from hermes.acquisition.confidence_model import calculate_confidence
from hermes.acquisition.evidence_collector import EvidenceCollector
from hermes.acquisition.evidence_linker import EvidenceLinker
from hermes.acquisition.evidence_quality import evidence_quality_rating
from hermes.acquisition.knowledge_index import KnowledgeIndex
from hermes.acquisition.knowledge_reuse import KnowledgeReuseEngine
from hermes.acquisition.reports import (
    build_acquisition_assets,
    generate_acquisition_report,
    generate_evidence_quality_report,
    generate_knowledge_index_report,
)
from hermes.acquisition.sources import SourceRegistry
from hermes.deliberation.knowledge_graph import DeliberationKnowledgeGraph
from hermes.deliberation.observability import DeliberationMetricsCollector, build_dashboard_data
from hermes.verification.claims import ClaimExtractor
from hermes.verification.evidence import Evidence


def test_source_registry_has_required_internal_sources() -> None:
    sources = SourceRegistry().load()
    for source_id in ["dmn", "reports", "benchmarks", "tests", "guardian_logs", "playbooks", "skills", "failure_reports", "verification_reports"]:
        assert source_id in sources
        assert sources[source_id].enabled is True
        assert sources[source_id].trust_level > 0


def test_knowledge_index_searches_internal_artifacts() -> None:
    index = KnowledgeIndex().build()
    assert index.items
    results = index.semantic_search("unsupported claim verification evidence", limit=5)
    assert results
    assert results[0][1] > 0


def test_evidence_collector_and_linker_connect_claims() -> None:
    claim = ClaimExtractor().extract("Unsupported claim evidence appears in verification reports.", source="acq")[0]
    candidates = EvidenceCollector().collect(claim=claim, task="verification evidence", limit=5)
    links = EvidenceLinker().link(claim, candidates)
    assert candidates
    assert links
    assert links[0].claim_id == claim.claim_id


def test_confidence_model_uses_support_diversity_trust_and_freshness() -> None:
    claim = ClaimExtractor().extract("Verification reports support evidence scoring.", source="confidence")[0]
    candidates = EvidenceCollector().collect(claim=claim, limit=3)
    links = EvidenceLinker().link(claim, candidates)
    confidence = calculate_confidence(
        evidence=[candidate.evidence for candidate in candidates],
        links=links,
        sources=SourceRegistry().load(),
        verification_success_history=0.5,
    )
    assert 0 <= confidence["confidence"] <= 1
    assert confidence["reasoning"]


def test_knowledge_reuse_finds_similar_existing_evidence() -> None:
    claim = ClaimExtractor().extract("Provider policy evidence should be reused.", source="reuse")[0]
    evidence = [Evidence("e1", "Reports", "provider policy evidence should be reused by future claims", 0.8, [])]
    result = KnowledgeReuseEngine().reuse(claim, evidence)
    assert result.reuse_success is True
    assert result.reuse_frequency == 1


def test_acquisition_pipeline_improves_evidence_score() -> None:
    assets = build_acquisition_assets()
    assert assets["improved_score"] > assets["baseline_score"]
    assert assets["score_delta"] > 0
    assert assets["acquisition"]["links"]
    assert assets["acquisition"]["acquisition_trace"]


def test_evidence_quality_rating_grades_acquired_evidence() -> None:
    claim = ClaimExtractor().extract("Verification report evidence supports claims.", source="quality")[0]
    candidates = EvidenceCollector().collect(claim=claim, limit=3)
    links = EvidenceLinker().link(claim, candidates)
    rating = evidence_quality_rating(
        evidence=[candidate.evidence for candidate in candidates],
        links=links,
        sources=SourceRegistry().load(),
    )
    assert rating["rating"] in {"A", "B", "C", "D", "F"}
    assert rating["score"] >= 0


def test_knowledge_graph_accepts_acquisition_assets() -> None:
    sources = list(SourceRegistry().load().values())
    graph = DeliberationKnowledgeGraph().add_acquisition_assets(
        evidence_sources=sources,
        knowledge_assets=[{"item_id": "asset-1"}],
        confidence_scores={"asset-1": 0.8},
        reuse_events=[{"claim_id": "claim-1", "reuse_frequency": 2}],
    )
    assert graph.query("EvidenceSources", "contains")
    assert graph.query("asset-1", "has_confidence")
    assert graph.query("claim-1", "has_reuse_event")


def test_acquisition_observability_fields(tmp_path) -> None:
    path = tmp_path / "metrics.jsonl"
    collector = DeliberationMetricsCollector(path)
    collector.record(
        {
            "mode": "full",
            "evidence_acquisition_count": 5,
            "evidence_reuse_rate": 0.4,
            "linking_accuracy": 0.8,
            "confidence": 0.7,
            "source_coverage": 3,
            "source_trust": 0.85,
            "evidence_freshness": 1.0,
            "verification_improvement": 20,
        }
    )
    acquisition = build_dashboard_data(path)["evidence_acquisition"]
    assert acquisition["evidence_acquisition_rate"] == 5
    assert acquisition["evidence_reuse_rate"] == 0.4
    assert acquisition["verification_improvement"] == 20


def test_acquisition_reports_generate(tmp_path) -> None:
    acquisition = generate_acquisition_report(tmp_path / "acquisition.md")
    quality = generate_evidence_quality_report(tmp_path / "quality.md")
    index = generate_knowledge_index_report(tmp_path / "index.md")
    assert acquisition["score_delta"] > 0
    assert "quality" in quality
    assert index["indexed_items"] > 0


def test_acquisition_cli_reports_json() -> None:
    for command in ("acquisition-report", "evidence-quality-report", "knowledge-index-report"):
        completed = subprocess.run(
            [sys.executable, "scripts/hermes.py", command, "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert "report_path" in payload


def test_evidence_report_includes_acquired_score() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/hermes.py", "evidence-report", "--json"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["acquired_evidence_score"] > payload["evidence_score"]
    assert payload["score_delta"] > 0
