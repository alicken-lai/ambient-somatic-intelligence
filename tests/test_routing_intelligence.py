from __future__ import annotations

import json
import subprocess
import sys

from hermes.deliberation.child_selector import ChildSelector
from hermes.deliberation.evaluation.golden_traces import load_golden_traces
from hermes.deliberation.evaluation.learning_report import generate_learning_report
from hermes.deliberation.memory import DeliberationEffectivenessMemory, EffectivenessRecord
from hermes.deliberation.observability import DeliberationMetricsCollector, build_dashboard_data
from hermes.deliberation.roi import ROICalculator, calculate_roi_from_scores
from hermes.deliberation.router import AdaptiveRoutingLearner, RoutingIntelligenceEngine
from hermes.deliberation.router.routing_policies import IMMUTABLE_GOVERNANCE_RULES
from hermes.deliberation.strategy_engine import DeliberationStrategyEngine


def test_roi_calculator_measures_quality_gain_against_cost() -> None:
    record = calculate_roi_from_scores(
        task_type="architecture",
        mode="light",
        quality_gain=10,
        latency_cost=2,
        resource_cost=2,
        verification_gain=0.5,
    )
    assert record.task_type == "architecture"
    assert record.mode == "light"
    assert record.overall_roi > 0
    assert record.quality_gain == 10


def test_effectiveness_memory_learns_from_ab_results(tmp_path) -> None:
    memory = DeliberationEffectivenessMemory(tmp_path / "memory.json")
    records = memory.update_from_ab_results(
        [
            {
                "category": "architecture",
                "scorecards": {
                    "single": {"overall_score": 60},
                    "light": {"overall_score": 72},
                    "full": {"overall_score": 70},
                },
            },
            {
                "category": "architecture",
                "scorecards": {
                    "single": {"overall_score": 62},
                    "light": {"overall_score": 74},
                    "full": {"overall_score": 71},
                },
            },
        ]
    )
    assert records["architecture"].best_mode == "light"
    assert memory.get("architecture") == records["architecture"]


def test_routing_intelligence_recommends_from_history() -> None:
    historical = EffectivenessRecord(
        task_class="architecture",
        sample_count=10,
        best_mode="light",
        avg_single_score=60,
        avg_light_score=75,
        avg_full_score=72,
        avg_roi=5,
    )
    decision = RoutingIntelligenceEngine().recommend(
        task="Design a subsystem",
        task_class="architecture",
        historical=historical,
    )
    assert decision.recommended_mode == "light"
    assert decision.confidence >= 0.6
    assert decision.why_not_single
    assert decision.why_not_full


def test_routing_intelligence_never_optimizes_away_guardian() -> None:
    historical = EffectivenessRecord("state_changing", 50, "single", 90, 60, 50, 1)
    decision = RoutingIntelligenceEngine().recommend(
        task="Delete logs and deploy dashboard",
        task_class="state_changing",
        historical=historical,
        risk_level="high",
    )
    assert decision.recommended_mode == "guardian_required"
    assert decision.confidence == 1.0


def test_adaptive_routing_learns_default_with_rollback_protection() -> None:
    records = {
        "architecture": EffectivenessRecord(
            task_class="architecture",
            sample_count=8,
            best_mode="light",
            avg_single_score=60,
            avg_light_score=75,
            avg_full_score=73,
            avg_roi=8,
        )
    }
    recommendations = AdaptiveRoutingLearner().learn_defaults(records)
    assert recommendations["architecture"]["default_mode"] == "light"
    assert recommendations["architecture"]["rollback_protection"]["immutable_governance"] is True


def test_child_selector_uses_dynamic_roles() -> None:
    roles = ChildSelector().select("provider_policy", max_children=3)
    assert [role.name for role in roles] == ["GovernanceReviewer", "PolicyReviewer", "RiskAnalyst"]


def test_strategy_engine_outputs_explainable_decision() -> None:
    historical = EffectivenessRecord("provider_policy", 6, "full", 55, 68, 74, 4)
    plan = DeliberationStrategyEngine().plan(
        task="Review provider routing policy",
        task_class="provider_policy",
        historical=historical,
    )
    assert plan["routing_decision"]["selected_mode"] == "full"
    assert "why_not_single" in plan["routing_decision"]
    assert plan["selected_children"]
    assert plan["expected_roi"] == 4


def test_governance_rules_are_immutable() -> None:
    assert {
        "guardian_rules",
        "provider_permissions",
        "credential_access_policies",
        "memory_write_policies",
        "human_approval_requirements",
    }.issubset(IMMUTABLE_GOVERNANCE_RULES)


def test_learning_report_generation(tmp_path) -> None:
    output = tmp_path / "learning.md"
    payload = generate_learning_report(output_path=output)
    assert payload["benchmark_count"] >= 25
    assert output.is_file()
    assert "Safety Boundary" in output.read_text(encoding="utf-8")


def test_strategy_report_cli_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/hermes.py",
            "strategy-report",
            "Review provider routing policy",
            "--task-class",
            "provider_policy",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert "routing_decision" in payload
    assert "selected_children" in payload


def test_golden_traces_available_for_routing_benchmarks() -> None:
    assert len(load_golden_traces()) >= 25


def test_observability_tracks_adaptive_routing_metrics(tmp_path) -> None:
    path = tmp_path / "metrics.jsonl"
    collector = DeliberationMetricsCollector(path)
    collector.record(
        {
            "trace_id": "trace-1",
            "mode": "light",
            "task_type": "architecture",
            "roi": 5.5,
            "routing_confidence": 0.8,
            "strategy_success": True,
            "selected_roles": ["SystemArchitect", "RiskAnalyst"],
            "verification_summary": [{"status": "verified"}],
        },
        latency_ms=100,
    )
    dashboard = build_dashboard_data(path)
    adaptive = dashboard["adaptive_routing"]
    assert adaptive["roi_by_task_type"]["architecture"] == 5.5
    assert adaptive["mode_effectiveness"]["light"] == 5.5
    assert adaptive["role_effectiveness"]["SystemArchitect"] == 5.5
    assert adaptive["routing_confidence"] == 0.8
    assert adaptive["strategy_success_rate"] == 1.0
