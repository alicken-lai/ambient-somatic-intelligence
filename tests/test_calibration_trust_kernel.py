from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from hermes.acquisition.reports import build_acquisition_assets
from hermes.acquisition.sources import EvidenceSource, SourceRegistry
from hermes.calibration.calibration_memory import CalibrationMemory
from hermes.calibration.confidence_model import confidence_from_assets, calibrated_confidence
from hermes.calibration.drift_detector import detect_drift
from hermes.calibration.inflation_detector import detect_inflation
from hermes.calibration.knowledge_health import compute_knowledge_health
from hermes.calibration.reports import generate_drift_report, generate_knowledge_health_report, generate_trust_report
from hermes.calibration.self_reference_detector import detect_self_reference
from hermes.calibration.source_trust import baseline_source_trust
from hermes.calibration.trust import TrustRegistry
from hermes.calibration.trust_evolution import evolve_trust
from hermes.calibration.trust_verification import trust_weighted_verification
from hermes.deliberation.knowledge_graph import DeliberationKnowledgeGraph
from hermes.deliberation.observability import DeliberationMetricsCollector, build_dashboard_data
from hermes.verification.evidence import Evidence


def test_trust_registry_and_source_baselines(tmp_path) -> None:
    sources = SourceRegistry().load()
    records = [baseline_source_trust(source) for source in sources.values()]
    registry = TrustRegistry(tmp_path / "trust.json")
    saved = registry.upsert_many(records)
    assert saved
    assert saved["trust-source-guardian_logs"].trust_score == 1.0
    assert saved["trust-source-tests"].trust_score == 0.95


def test_calibrated_confidence_components() -> None:
    confidence = calibrated_confidence(coverage=1, trust=0.7, freshness=0.8, consistency=0.9, verification=0.6)
    assert confidence["overall"] < 100
    assert confidence["trust"] == 70
    assert confidence["coverage"] == 100


def test_confidence_from_assets_is_calibrated_below_raw_score() -> None:
    assets = build_acquisition_assets()
    confidence = confidence_from_assets(assets)
    assert 0 <= confidence["overall"] <= 100
    assert confidence["overall"] < assets["improved_score"]


def test_trust_weighted_verification_uses_source_trust() -> None:
    evidence = [Evidence("e1", "Tests", "passed tests", 0.9, [])]
    weighted = trust_weighted_verification(evidence, SourceRegistry().load(), historical_reliability=0.5)
    assert 0 < weighted["weighted_confidence"] <= 1
    assert weighted["evidence_weight"] > 0


def test_inflation_detector_flags_repeated_sources() -> None:
    evidence = [Evidence(f"e{i}", "Reports", "same-report", 0.8, []) for i in range(6)]
    result = detect_inflation(evidence, links=[object()] * 12)
    assert result["inflation_risk"] > 0.3


def test_self_reference_detector_flags_cycles() -> None:
    result = detect_self_reference({"claim-a": [{"relation": "supports", "target": "claim-b"}], "claim-b": [{"relation": "supports", "target": "claim-a"}]})
    assert result["self_reference"] is True
    assert result["trust_reduction_event"] is True


def test_drift_detector_finds_stale_sources() -> None:
    old = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    source = EvidenceSource("old", "Reports", 0.8, last_updated=old)
    result = detect_drift([source], stale_days=30)
    assert result["drift_detected"] is True
    assert result["severity"] in {"medium", "high"}


def test_trust_evolution_promotes_slowly_and_reduces_aggressively() -> None:
    promoted = evolve_trust(0.7, verification_success=5)
    reduced = evolve_trust(0.7, verification_failure=2, contradictions=1)
    assert promoted["trust_score"] > 0.7
    assert reduced["trust_score"] < 0.7
    assert reduced["event"] == "reduction"


def test_calibration_memory_records_events(tmp_path) -> None:
    memory = CalibrationMemory(tmp_path / "calibration.jsonl")
    memory.append({"trust": 0.7, "drift_event": False})
    assert memory.load()[0]["trust"] == 0.7


def test_knowledge_health_penalizes_inflation_and_drift() -> None:
    healthy = compute_knowledge_health(trust=0.8, freshness=0.9, consistency=0.9, verification=0.8, drift=0, inflation=0)
    risky = compute_knowledge_health(trust=0.8, freshness=0.9, consistency=0.9, verification=0.8, drift=1, inflation=1)
    assert healthy["health_score"] > risky["health_score"]
    assert risky["risk_level"] in {"medium", "high"}


def test_knowledge_graph_calibration_nodes() -> None:
    record = baseline_source_trust(SourceRegistry().load()["reports"])
    graph = DeliberationKnowledgeGraph().add_calibration_assets(
        trust_records=[record],
        confidence_nodes={"reports": 0.8},
        drift_events=[{"severity": "medium"}],
        inflation_events=[{"risk": 0.5}],
        reliability_history=[{"reports": 0.8}],
    )
    assert graph.query("reports", "has_trust")
    assert graph.trust_weighted_query("reports", {record.trust_id: 0.9})


def test_calibration_observability_fields(tmp_path) -> None:
    path = tmp_path / "metrics.jsonl"
    collector = DeliberationMetricsCollector(path)
    collector.record(
        {
            "mode": "full",
            "trust_score": 0.8,
            "calibrated_confidence": 75,
            "drift_event": True,
            "inflation_event": True,
            "knowledge_health_score": 62,
            "source_reliability": 0.85,
            "verification_weighted_confidence": 0.7,
        }
    )
    calibration = build_dashboard_data(path)["knowledge_calibration"]
    assert calibration["trust_distribution"]["full"] == 0.8
    assert calibration["drift_frequency"] == 1.0
    assert calibration["knowledge_health_trends"] == 62


def test_calibration_reports_generate(tmp_path) -> None:
    health = generate_knowledge_health_report(tmp_path / "health.md")
    trust = generate_trust_report(tmp_path / "trust.md")
    drift = generate_drift_report(tmp_path / "drift.md")
    assert "health" in health
    assert trust["trust_records"]
    assert "drift_detected" in drift


def test_calibration_cli_reports_json() -> None:
    for command in ("knowledge-health-report", "trust-report", "drift-report"):
        completed = subprocess.run(
            [sys.executable, "scripts/hermes.py", command, "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert "report_path" in payload
