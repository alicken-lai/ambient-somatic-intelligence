"""Historical metrics collector for deliberation observability."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from statistics import mean
from typing import Any


class DeliberationMetricsCollector:
    def __init__(self, path: str | Path = "logs/deliberation_metrics.jsonl"):
        self.path = Path(path)

    def record(self, result: dict[str, Any], *, latency_ms: int | None = None) -> dict[str, Any]:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": result.get("trace_id"),
            "mode": result.get("mode"),
            "latency_ms": latency_ms if latency_ms is not None else result.get("latency_ms", 0),
            "judge_latency_ms": result.get("judge_latency_ms", 0),
            "verifier_latency_ms": result.get("verifier_latency_ms", 0),
            "synthesizer_latency_ms": result.get("synthesizer_latency_ms", 0),
            "guardian_triggered": bool(result.get("guardian_warnings") or result.get("triage", {}).get("guardian_required")),
            "verification_count": len(result.get("verification_summary", [])),
            "providers_used": list(result.get("providers_used", [])),
            "task_type": result.get("task_type") or result.get("triage", {}).get("labels", ["unknown"])[0],
            "roi": result.get("roi", 0),
            "routing_confidence": result.get("routing_confidence", 0),
            "strategy_success": bool(result.get("strategy_success", False)),
            "selected_roles": list(result.get("selected_roles", [])),
            "skill_id": result.get("skill_id"),
            "playbook_id": result.get("playbook_id"),
            "skill_success": bool(result.get("skill_success", False)),
            "playbook_success": bool(result.get("playbook_success", False)),
            "promotion_event": result.get("promotion_event"),
            "retirement_event": result.get("retirement_event"),
            "failure_type": result.get("failure_type"),
            "strategy_id": result.get("strategy_id"),
            "claim_count": result.get("claim_count", 0),
            "verification_rate": result.get("verification_rate", 0),
            "unsupported_claim_rate": result.get("unsupported_claim_rate", 0),
            "evidence_score": result.get("evidence_score", 0),
            "contradiction_count": result.get("contradiction_count", 0),
            "verification_latency_ms": result.get("verification_latency_ms", 0),
            "playbook_evidence_quality": result.get("playbook_evidence_quality", 0),
            "evidence_acquisition_count": result.get("evidence_acquisition_count", 0),
            "evidence_reuse_rate": result.get("evidence_reuse_rate", 0),
            "linking_accuracy": result.get("linking_accuracy", 0),
            "confidence": result.get("confidence", 0),
            "source_coverage": result.get("source_coverage", 0),
            "source_trust": result.get("source_trust", 0),
            "evidence_freshness": result.get("evidence_freshness", 0),
            "verification_improvement": result.get("verification_improvement", 0),
            "trust_score": result.get("trust_score", 0),
            "calibrated_confidence": result.get("calibrated_confidence", 0),
            "drift_event": result.get("drift_event", False),
            "inflation_event": result.get("inflation_event", False),
            "knowledge_health_score": result.get("knowledge_health_score", 0),
            "source_reliability": result.get("source_reliability", 0),
            "verification_weighted_confidence": result.get("verification_weighted_confidence", 0),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def summarize(self) -> dict[str, Any]:
        events = self._read_events()
        if not events:
            return {
                "average_latency_ms": 0,
                "judge_latency_ms": 0,
                "verifier_latency_ms": 0,
                "synthesizer_latency_ms": 0,
                "guardian_frequency": 0,
                "mode_frequency": {},
                "verification_frequency": 0,
                "provider_usage": {},
            }
        return {
            "average_latency_ms": _avg(events, "latency_ms"),
            "judge_latency_ms": _avg(events, "judge_latency_ms"),
            "verifier_latency_ms": _avg(events, "verifier_latency_ms"),
            "synthesizer_latency_ms": _avg(events, "synthesizer_latency_ms"),
            "guardian_frequency": sum(1 for event in events if event.get("guardian_triggered")) / len(events),
            "mode_frequency": _frequency(event.get("mode") for event in events),
            "verification_frequency": _avg(events, "verification_count"),
            "provider_usage": _provider_usage(events),
            "roi_by_task_type": _average_by(events, "task_type", "roi"),
            "mode_effectiveness": _average_by(events, "mode", "roi"),
            "role_effectiveness": _role_effectiveness(events),
            "routing_confidence": _avg(events, "routing_confidence"),
            "strategy_success_rate": sum(1 for event in events if event.get("strategy_success")) / len(events),
            "verification_efficiency": _verification_efficiency(events),
            "skill_usage": _frequency(event.get("skill_id") for event in events),
            "playbook_usage": _frequency(event.get("playbook_id") for event in events),
            "skill_success_rate": _rate(events, "skill_success"),
            "playbook_success_rate": _rate(events, "playbook_success"),
            "promotion_rate": _event_rate(events, "promotion_event"),
            "retirement_rate": _event_rate(events, "retirement_event"),
            "failure_recurrence": _frequency(event.get("failure_type") for event in events),
            "strategy_stability": _strategy_stability(events),
            "claim_volume": sum(int(event.get("claim_count", 0) or 0) for event in events),
            "verification_rate": _avg(events, "verification_rate"),
            "unsupported_claim_rate": _avg(events, "unsupported_claim_rate"),
            "evidence_score": _avg(events, "evidence_score"),
            "contradiction_frequency": _avg(events, "contradiction_count"),
            "verification_latency_ms": _avg(events, "verification_latency_ms"),
            "playbook_evidence_quality": _avg(events, "playbook_evidence_quality"),
            "evidence_acquisition_rate": _avg(events, "evidence_acquisition_count"),
            "evidence_reuse_rate": _avg(events, "evidence_reuse_rate"),
            "linking_accuracy": _avg(events, "linking_accuracy"),
            "confidence_distribution": _average_by(events, "mode", "confidence"),
            "source_coverage": _avg(events, "source_coverage"),
            "source_trust_distribution": _average_by(events, "mode", "source_trust"),
            "evidence_freshness": _avg(events, "evidence_freshness"),
            "verification_improvement": _avg(events, "verification_improvement"),
            "trust_distribution": _average_by(events, "mode", "trust_score"),
            "calibrated_confidence_distribution": _average_by(events, "mode", "calibrated_confidence"),
            "drift_frequency": _event_rate(events, "drift_event"),
            "inflation_frequency": _event_rate(events, "inflation_event"),
            "knowledge_health_trends": _avg(events, "knowledge_health_score"),
            "source_reliability": _avg(events, "source_reliability"),
            "verification_weighted_confidence": _avg(events, "verification_weighted_confidence"),
        }

    def _read_events(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _avg(events: list[dict[str, Any]], key: str) -> float:
    return round(mean(float(event.get(key, 0) or 0) for event in events), 2)


def _frequency(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        if value is None:
            continue
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def _provider_usage(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        for provider in event.get("providers_used", []):
            counts[str(provider)] = counts.get(str(provider), 0) + 1
    return counts


def _average_by(events: list[dict[str, Any]], group_key: str, value_key: str) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    for event in events:
        group = event.get(group_key)
        if group is None:
            continue
        grouped.setdefault(str(group), []).append(float(event.get(value_key, 0) or 0))
    return {key: round(mean(values), 2) for key, values in grouped.items() if values}


def _role_effectiveness(events: list[dict[str, Any]]) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    for event in events:
        for role in event.get("selected_roles", []):
            grouped.setdefault(str(role), []).append(float(event.get("roi", 0) or 0))
    return {key: round(mean(values), 2) for key, values in grouped.items() if values}


def _verification_efficiency(events: list[dict[str, Any]]) -> float:
    total_verifications = sum(float(event.get("verification_count", 0) or 0) for event in events)
    total_latency = sum(float(event.get("latency_ms", 0) or 0) for event in events)
    if total_latency <= 0:
        return 0.0
    return round(total_verifications / total_latency, 4)


def _rate(events: list[dict[str, Any]], key: str) -> float:
    if not events:
        return 0.0
    return round(sum(1 for event in events if event.get(key)) / len(events), 4)


def _event_rate(events: list[dict[str, Any]], key: str) -> float:
    return _rate(events, key)


def _strategy_stability(events: list[dict[str, Any]]) -> float:
    strategies = [event.get("strategy_id") for event in events if event.get("strategy_id")]
    if not strategies:
        return 0.0
    most_common = max(_frequency(strategies).values())
    return round(most_common / len(strategies), 4)
