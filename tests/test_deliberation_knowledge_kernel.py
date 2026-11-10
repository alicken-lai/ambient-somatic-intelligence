from __future__ import annotations

import json
import subprocess
import sys
from functools import lru_cache

from hermes.deliberation.evaluation.ab_test import run_ab_test
from hermes.deliberation.evaluation.golden_traces import load_golden_traces
from hermes.deliberation.evaluation.knowledge_reports import generate_failure_report, generate_playbook_report, generate_skill_report
from hermes.deliberation.failure_learning import learn_failures
from hermes.deliberation.knowledge_graph import DeliberationKnowledgeGraph
from hermes.deliberation.observability import DeliberationMetricsCollector, build_dashboard_data
from hermes.deliberation.pattern_mining import mine_patterns
from hermes.deliberation.playbooks import PlaybookRegistry, PlaybookSelector
from hermes.deliberation.recommendation_engine import DeliberationRecommendationEngine
from hermes.deliberation.skills import SkillExtractor, SkillRegistry
from hermes.deliberation.skill_evolution import evaluate_skill_evolution
from hermes.deliberation.strategy_memory import StrategyMemory


@lru_cache(maxsize=1)
def _sample_results():
    traces = load_golden_traces()[:3]
    return tuple(run_ab_test(trace) for trace in traces)


def test_skill_extractor_and_registry(tmp_path) -> None:
    skills = SkillExtractor().extract_from_ab_results(_sample_results())
    assert skills
    assert all(skill.skill_id and skill.steps for skill in skills)
    registry = SkillRegistry(tmp_path / "skills.json")
    saved = registry.upsert_many(skills)
    assert set(saved) == {skill.skill_id for skill in skills}


def test_playbook_selector_explains_choice() -> None:
    selection = PlaybookSelector().select(task="Review provider policy", task_class="provider_policy")
    assert selection["selected_playbook"] == "provider_policy"
    assert selection["confidence"] > 0
    assert "reason" in selection


def test_pattern_mining_ranks_patterns() -> None:
    patterns = mine_patterns(_sample_results())
    assert patterns["child_combinations"]
    assert patterns["routing_paths"]
    assert patterns["verification_sequences"][0]["pattern"] == "claim_status_verifier"


def test_skill_evolution_promotes_and_observes() -> None:
    skills = SkillExtractor().extract_from_ab_results(_sample_results())
    decisions = evaluate_skill_evolution(skills)
    assert decisions
    assert all(decision["status"] in {"promoted", "retired", "observed"} for decision in decisions)


def test_failure_learning_extracts_lessons() -> None:
    failures = learn_failures(_sample_results())
    assert failures
    assert {"failure_type", "root_cause", "recommended_fix", "frequency"} <= set(failures[0])


def test_knowledge_graph_answers_playbook_query() -> None:
    skills = SkillExtractor().extract_from_ab_results(_sample_results())
    playbooks = list(PlaybookRegistry().load().values())
    graph = DeliberationKnowledgeGraph().build(skills=skills, playbooks=playbooks, failures=[])
    assert graph.best_playbook_for("provider_policy") == "provider_policy"
    assert graph.query("provider_policy", "uses_playbook")


def test_strategy_memory_persists_advisory_outcomes(tmp_path) -> None:
    memory = StrategyMemory(tmp_path / "strategy.jsonl")
    memory.append(
        {
            "selected_strategy": "light_adaptive_strategy",
            "outcome": "success",
            "roi": 5.5,
            "quality_score": 70,
            "verification_score": 60,
            "guardian_result": "NOT_REQUIRED",
        }
    )
    assert memory.load()[0]["selected_strategy"] == "light_adaptive_strategy"


def test_recommendation_engine_returns_advisory_strategy() -> None:
    recommendation = DeliberationRecommendationEngine().recommend(
        task="Review provider policy",
        task_class="provider_policy",
    )
    assert recommendation["selected_playbook"] == "provider_policy"
    assert recommendation["advisory_only"] is True
    assert recommendation["best_known_strategy"]


def test_knowledge_observability_fields(tmp_path) -> None:
    path = tmp_path / "metrics.jsonl"
    collector = DeliberationMetricsCollector(path)
    collector.record(
        {
            "trace_id": "trace-k",
            "mode": "full",
            "skill_id": "provider_policy_deliberation",
            "playbook_id": "provider_policy",
            "skill_success": True,
            "playbook_success": True,
            "promotion_event": "promoted",
            "failure_type": "unsupported_claim",
            "strategy_id": "full_adaptive_strategy",
        }
    )
    knowledge = build_dashboard_data(path)["knowledge_formation"]
    assert knowledge["skill_usage"]["provider_policy_deliberation"] == 1
    assert knowledge["playbook_usage"]["provider_policy"] == 1
    assert knowledge["skill_success_rate"] == 1.0
    assert knowledge["promotion_rate"] == 1.0
    assert knowledge["failure_recurrence"]["unsupported_claim"] == 1


def test_reports_generate_markdown(tmp_path) -> None:
    playbook = generate_playbook_report(output_path=tmp_path / "playbook.md")
    skill = generate_skill_report(output_path=tmp_path / "skill.md")
    failure = generate_failure_report(output_path=tmp_path / "failure.md")
    assert playbook["playbook_count"] >= 5
    assert skill["skill_count"] > 0
    assert failure["failure_mode_count"] > 0


def test_playbook_skill_failure_cli_json() -> None:
    for command in ("playbook-report", "skill-report", "failure-report"):
        completed = subprocess.run(
            [sys.executable, "scripts/hermes.py", command, "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert "report_path" in payload
