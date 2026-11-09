"""Dashboard data projection for deliberation observability."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hermes.deliberation.observability.metrics_collector import DeliberationMetricsCollector


def build_dashboard_data(path: str | Path = "logs/deliberation_metrics.jsonl") -> dict[str, Any]:
    summary = DeliberationMetricsCollector(path).summarize()
    return {
        "latency": {
            "average": summary["average_latency_ms"],
            "judge": summary["judge_latency_ms"],
            "verifier": summary["verifier_latency_ms"],
            "synthesizer": summary["synthesizer_latency_ms"],
        },
        "frequencies": {
            "guardian": summary["guardian_frequency"],
            "mode": summary["mode_frequency"],
            "verification": summary["verification_frequency"],
        },
        "provider_usage": summary["provider_usage"],
        "adaptive_routing": {
            "roi_by_task_type": summary.get("roi_by_task_type", {}),
            "mode_effectiveness": summary.get("mode_effectiveness", {}),
            "role_effectiveness": summary.get("role_effectiveness", {}),
            "routing_confidence": summary.get("routing_confidence", 0),
            "strategy_success_rate": summary.get("strategy_success_rate", 0),
            "verification_efficiency": summary.get("verification_efficiency", 0),
        },
        "knowledge_formation": {
            "skill_usage": summary.get("skill_usage", {}),
            "playbook_usage": summary.get("playbook_usage", {}),
            "skill_success_rate": summary.get("skill_success_rate", 0),
            "playbook_success_rate": summary.get("playbook_success_rate", 0),
            "promotion_rate": summary.get("promotion_rate", 0),
            "retirement_rate": summary.get("retirement_rate", 0),
            "failure_recurrence": summary.get("failure_recurrence", {}),
            "strategy_stability": summary.get("strategy_stability", 0),
        },
        "verification_kernel": {
            "claim_volume": summary.get("claim_volume", 0),
            "verification_rate": summary.get("verification_rate", 0),
            "unsupported_claim_rate": summary.get("unsupported_claim_rate", 0),
            "evidence_score": summary.get("evidence_score", 0),
            "contradiction_frequency": summary.get("contradiction_frequency", 0),
            "verification_latency_ms": summary.get("verification_latency_ms", 0),
            "playbook_evidence_quality": summary.get("playbook_evidence_quality", 0),
        },
        "evidence_acquisition": {
            "evidence_acquisition_rate": summary.get("evidence_acquisition_rate", 0),
            "evidence_reuse_rate": summary.get("evidence_reuse_rate", 0),
            "linking_accuracy": summary.get("linking_accuracy", 0),
            "confidence_distribution": summary.get("confidence_distribution", {}),
            "source_coverage": summary.get("source_coverage", 0),
            "source_trust_distribution": summary.get("source_trust_distribution", {}),
            "evidence_freshness": summary.get("evidence_freshness", 0),
            "verification_improvement": summary.get("verification_improvement", 0),
        },
        "knowledge_calibration": {
            "trust_distribution": summary.get("trust_distribution", {}),
            "confidence_distribution": summary.get("calibrated_confidence_distribution", {}),
            "drift_frequency": summary.get("drift_frequency", 0),
            "inflation_frequency": summary.get("inflation_frequency", 0),
            "knowledge_health_trends": summary.get("knowledge_health_trends", 0),
            "source_reliability": summary.get("source_reliability", 0),
            "verification_weighted_confidence": summary.get("verification_weighted_confidence", 0),
        },
    }
