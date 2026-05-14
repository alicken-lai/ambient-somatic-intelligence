"""
Memory Injection Tracer — Track which memories were injected into which
agent's context, and whether they influenced the outcome.

Enables effectiveness analysis: which memory layers contribute to task
success, which injections are wasteful, and detection of anomalous
injection patterns.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from observability.cognitive_trace_v2.causal_trace_schema import (
    CausalEventType,
)
from observability.cognitive_trace_v2.execution_lineage import ExecutionLineageTracer

logger = logging.getLogger(__name__)


@dataclass
class InjectionTraceConfig:
    max_records: int = 5000
    track_effectiveness: bool = True


@dataclass
class InjectedMemory:
    memory_hash: str
    layer: str
    relevance_score: float
    tokens: int
    age_hours: float
    tags: list[str]
    content_preview: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_hash": self.memory_hash,
            "layer": self.layer,
            "relevance_score": self.relevance_score,
            "tokens": self.tokens,
            "age_hours": self.age_hours,
            "tags": self.tags,
            "content_preview": self.content_preview,
        }


@dataclass
class InjectionRecord:
    injection_id: str
    event_id: str
    agent_id: str
    task_id: str
    memories_injected: list[InjectedMemory]
    total_tokens: int
    context_budget: int
    compression_applied: str | None
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "injection_id": self.injection_id,
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "memories_injected": [m.to_dict() for m in self.memories_injected],
            "total_tokens": self.total_tokens,
            "context_budget": self.context_budget,
            "compression_applied": self.compression_applied,
            "timestamp": self.timestamp,
        }


@dataclass
class InjectionOutcome:
    injection_id: str
    task_succeeded: bool
    memory_referenced: bool
    usefulness_score: float
    feedback: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "injection_id": self.injection_id,
            "task_succeeded": self.task_succeeded,
            "memory_referenced": self.memory_referenced,
            "usefulness_score": self.usefulness_score,
            "feedback": self.feedback,
        }


@dataclass
class EffectivenessReport:
    agent_id: str
    total_injections: int
    avg_memories_per_injection: float
    avg_tokens_per_injection: float
    avg_usefulness: float
    most_useful_layers: list[str]
    least_useful_layers: list[str]
    waste_ratio: float
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "total_injections": self.total_injections,
            "avg_memories_per_injection": round(self.avg_memories_per_injection, 2),
            "avg_tokens_per_injection": round(self.avg_tokens_per_injection, 2),
            "avg_usefulness": round(self.avg_usefulness, 3),
            "most_useful_layers": self.most_useful_layers,
            "least_useful_layers": self.least_useful_layers,
            "waste_ratio": round(self.waste_ratio, 3),
            "generated_at": self.generated_at,
        }


@dataclass
class InfluenceMap:
    total_memories_tracked: int
    influence_by_layer: dict[str, float]
    top_influential_tags: list[str]
    injection_to_outcome_correlation: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_memories_tracked": self.total_memories_tracked,
            "influence_by_layer": {k: round(v, 3) for k, v in self.influence_by_layer.items()},
            "top_influential_tags": self.top_influential_tags,
            "injection_to_outcome_correlation": round(self.injection_to_outcome_correlation, 3),
        }


@dataclass
class InjectionAnomaly:
    anomaly_type: str
    agent_id: str
    description: str
    severity: str
    injection_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type,
            "agent_id": self.agent_id,
            "description": self.description,
            "severity": self.severity,
            "injection_ids": self.injection_ids,
        }


class MemoryInjectionTracer:

    def __init__(
        self,
        lineage_tracer: ExecutionLineageTracer,
        config: InjectionTraceConfig | None = None,
    ) -> None:
        self._lineage = lineage_tracer
        self._config = config or InjectionTraceConfig()
        self._records: dict[str, InjectionRecord] = {}
        self._outcomes: dict[str, InjectionOutcome] = {}
        self._by_agent: dict[str, list[str]] = defaultdict(list)
        self._record_order: list[str] = []

    def record_injection(self, injection: InjectionRecord) -> str:
        self._records[injection.injection_id] = injection
        self._by_agent[injection.agent_id].append(injection.injection_id)
        self._record_order.append(injection.injection_id)
        self._enforce_limits()

        event = self._lineage.create_child_event(
            parent_id=injection.event_id,
            event_type=CausalEventType.CONTEXT_INJECTION,
            source_subsystem="memory",
            source_component="MemoryInjectionTracer",
            action="inject",
            agent_id=injection.agent_id,
            task_id=injection.task_id,
            payload={
                "injection_id": injection.injection_id,
                "memory_count": len(injection.memories_injected),
                "total_tokens": injection.total_tokens,
                "compression": injection.compression_applied,
            },
        )
        self._lineage.record_event(event)

        logger.debug(
            "Recorded injection %s for agent=%s memories=%d tokens=%d",
            injection.injection_id, injection.agent_id,
            len(injection.memories_injected), injection.total_tokens,
        )
        return injection.injection_id

    def record_outcome(self, injection_id: str, outcome: InjectionOutcome) -> None:
        if injection_id not in self._records:
            raise ValueError(f"Injection {injection_id} not found")

        self._outcomes[injection_id] = outcome
        logger.debug(
            "Recorded outcome for injection %s success=%s usefulness=%.2f",
            injection_id, outcome.task_succeeded, outcome.usefulness_score,
        )

    def get_injection_history(self, agent_id: str) -> list[InjectionRecord]:
        ids = self._by_agent.get(agent_id, [])
        return [self._records[rid] for rid in ids if rid in self._records]

    def get_injection_effectiveness(self, agent_id: str) -> EffectivenessReport:
        records = self.get_injection_history(agent_id)
        if not records:
            return EffectivenessReport(
                agent_id=agent_id,
                total_injections=0,
                avg_memories_per_injection=0.0,
                avg_tokens_per_injection=0.0,
                avg_usefulness=0.0,
                most_useful_layers=[],
                least_useful_layers=[],
                waste_ratio=0.0,
                generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )

        total_memories = sum(len(r.memories_injected) for r in records)
        total_tokens = sum(r.total_tokens for r in records)

        outcomes = [self._outcomes[r.injection_id] for r in records if r.injection_id in self._outcomes]
        avg_usefulness = 0.0
        if outcomes:
            avg_usefulness = sum(o.usefulness_score for o in outcomes) / len(outcomes)

        layer_scores: dict[str, list[float]] = defaultdict(list)
        for record in records:
            outcome = self._outcomes.get(record.injection_id)
            score = outcome.usefulness_score if outcome else 0.0
            for mem in record.memories_injected:
                layer_scores[mem.layer].append(score)

        layer_avg: dict[str, float] = {}
        for layer, scores in layer_scores.items():
            layer_avg[layer] = sum(scores) / len(scores) if scores else 0.0

        sorted_layers = sorted(layer_avg.items(), key=lambda x: x[1], reverse=True)
        most_useful = [l for l, _ in sorted_layers[:3]]
        least_useful = [l for l, _ in sorted_layers[-3:]] if len(sorted_layers) > 3 else []

        useful_tokens = 0
        total_tracked = 0
        for record in records:
            outcome = self._outcomes.get(record.injection_id)
            if outcome:
                total_tracked += record.total_tokens
                useful_tokens += int(record.total_tokens * outcome.usefulness_score)

        waste_ratio = 1.0 - (useful_tokens / total_tracked) if total_tracked > 0 else 0.0

        return EffectivenessReport(
            agent_id=agent_id,
            total_injections=len(records),
            avg_memories_per_injection=total_memories / len(records),
            avg_tokens_per_injection=total_tokens / len(records),
            avg_usefulness=avg_usefulness,
            most_useful_layers=most_useful,
            least_useful_layers=least_useful,
            waste_ratio=waste_ratio,
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

    def get_memory_influence_map(self) -> InfluenceMap:
        layer_influence: dict[str, list[float]] = defaultdict(list)
        tag_influence: dict[str, list[float]] = defaultdict(list)
        total_memories = 0

        for record in self._records.values():
            outcome = self._outcomes.get(record.injection_id)
            score = outcome.usefulness_score if outcome else 0.0

            for mem in record.memories_injected:
                total_memories += 1
                layer_influence[mem.layer].append(score)
                for tag in mem.tags:
                    tag_influence[tag].append(score)

        influence_by_layer: dict[str, float] = {}
        for layer, scores in layer_influence.items():
            influence_by_layer[layer] = sum(scores) / len(scores) if scores else 0.0

        tag_avg: dict[str, float] = {}
        for tag, scores in tag_influence.items():
            tag_avg[tag] = sum(scores) / len(scores) if scores else 0.0
        top_tags = [t for t, _ in sorted(tag_avg.items(), key=lambda x: x[1], reverse=True)[:10]]

        outcomes_with_score = [o for o in self._outcomes.values()]
        correlation = 0.0
        if outcomes_with_score:
            successes = [1.0 if o.task_succeeded else 0.0 for o in outcomes_with_score]
            scores = [o.usefulness_score for o in outcomes_with_score]
            if len(successes) > 1:
                correlation = _simple_correlation(successes, scores)

        return InfluenceMap(
            total_memories_tracked=total_memories,
            influence_by_layer=influence_by_layer,
            top_influential_tags=top_tags,
            injection_to_outcome_correlation=correlation,
        )

    def detect_injection_anomalies(self) -> list[InjectionAnomaly]:
        anomalies: list[InjectionAnomaly] = []

        for agent_id, ids in self._by_agent.items():
            records = [self._records[rid] for rid in ids if rid in self._records]
            if not records:
                continue

            for record in records:
                if record.total_tokens > record.context_budget:
                    anomalies.append(InjectionAnomaly(
                        anomaly_type="budget_exceeded",
                        agent_id=agent_id,
                        description=f"Injection used {record.total_tokens} tokens vs budget {record.context_budget}",
                        severity="high",
                        injection_ids=[record.injection_id],
                    ))

            zero_relevance_ids: list[str] = []
            for record in records:
                if all(m.relevance_score <= 0.0 for m in record.memories_injected):
                    zero_relevance_ids.append(record.injection_id)
            if zero_relevance_ids:
                anomalies.append(InjectionAnomaly(
                    anomaly_type="zero_relevance",
                    agent_id=agent_id,
                    description=f"{len(zero_relevance_ids)} injections had zero relevance across all memories",
                    severity="medium",
                    injection_ids=zero_relevance_ids,
                ))

            avg_count = sum(len(r.memories_injected) for r in records) / len(records)
            excessive_ids = [
                r.injection_id for r in records
                if len(r.memories_injected) > max(avg_count * 3, 20)
            ]
            if excessive_ids:
                anomalies.append(InjectionAnomaly(
                    anomaly_type="excessive_injection",
                    agent_id=agent_id,
                    description=f"{len(excessive_ids)} injections had excessive memory count (>3x average)",
                    severity="medium",
                    injection_ids=excessive_ids,
                ))

            memory_counts: dict[str, int] = defaultdict(int)
            memory_injection_ids: dict[str, list[str]] = defaultdict(list)
            for record in records:
                for mem in record.memories_injected:
                    memory_counts[mem.memory_hash] += 1
                    memory_injection_ids[mem.memory_hash].append(record.injection_id)
            for mem_hash, count in memory_counts.items():
                if count > max(len(records) * 0.5, 5):
                    anomalies.append(InjectionAnomaly(
                        anomaly_type="repeated_memory",
                        agent_id=agent_id,
                        description=f"Memory {mem_hash[:12]}... injected {count} times across {len(records)} injections",
                        severity="low",
                        injection_ids=list(set(memory_injection_ids[mem_hash]))[:10],
                    ))

        return anomalies

    def record_count(self) -> int:
        return len(self._records)

    def _enforce_limits(self) -> None:
        while len(self._records) > self._config.max_records and self._record_order:
            oldest_id = self._record_order.pop(0)
            record = self._records.pop(oldest_id, None)
            self._outcomes.pop(oldest_id, None)
            if record:
                agent_ids = self._by_agent.get(record.agent_id, [])
                if oldest_id in agent_ids:
                    agent_ids.remove(oldest_id)


def _simple_correlation(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / n
    std_x = (sum((x - mean_x) ** 2 for x in xs) / n) ** 0.5
    std_y = (sum((y - mean_y) ** 2 for y in ys) / n) ** 0.5
    if std_x == 0 or std_y == 0:
        return 0.0
    return cov / (std_x * std_y)
