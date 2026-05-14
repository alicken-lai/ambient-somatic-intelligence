"""Optimize context assembly by detecting reusable context blocks across tasks."""
from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ReuseConfig:
    max_cached_contexts: int = 50
    context_ttl_seconds: float = 600.0
    min_overlap_for_reuse: float = 0.6
    reusable_block_types: list[str] = field(
        default_factory=lambda: ["system_context", "memory_context"]
    )


@dataclass
class ReusableBlock:
    block_type: str
    content_hash: str
    tokens: int
    age_seconds: float
    reuse_count: int
    freshness: float


@dataclass
class ReuseCheckResult:
    can_reuse: bool
    reusable_blocks: list[ReusableBlock]
    estimated_token_savings: int
    estimated_time_savings_ms: float
    reason: str


@dataclass
class ReuseStats:
    total_checks: int
    reuse_hits: int
    reuse_rate: float
    total_tokens_saved: int
    total_time_saved_ms: float
    avg_overlap: float
    most_reused_block_type: str


@dataclass
class _StoredContext:
    task_type: str
    agent_id: str
    query_hash: str
    blocks: list[dict]
    tokens: int
    created_at: float
    last_accessed: float
    access_count: int


class ContextReuseOptimizer:
    def __init__(self, config: ReuseConfig | None = None) -> None:
        self._config = config or ReuseConfig()
        self._contexts: OrderedDict[str, _StoredContext] = OrderedDict()
        self._transitions: list[tuple[str, str, float]] = []
        self._total_checks = 0
        self._reuse_hits = 0
        self._total_tokens_saved = 0
        self._total_time_saved_ms = 0.0
        self._overlap_samples: list[float] = []
        self._block_type_reuse_counts: dict[str, int] = {}

    def check_reusable(
        self, task_type: str, agent_id: str, query_hash: str
    ) -> ReuseCheckResult:
        self._total_checks += 1
        ctx_key = f"{task_type}:{agent_id}"
        stored = self._contexts.get(ctx_key)

        if not stored:
            return ReuseCheckResult(
                can_reuse=False,
                reusable_blocks=[],
                estimated_token_savings=0,
                estimated_time_savings_ms=0.0,
                reason="no previous context for this agent/task combination",
            )

        age = time.time() - stored.created_at
        if age > self._config.context_ttl_seconds:
            self._contexts.pop(ctx_key, None)
            return ReuseCheckResult(
                can_reuse=False,
                reusable_blocks=[],
                estimated_token_savings=0,
                estimated_time_savings_ms=0.0,
                reason=f"cached context expired ({age:.0f}s > {self._config.context_ttl_seconds:.0f}s TTL)",
            )

        freshness = max(0.0, 1.0 - (age / self._config.context_ttl_seconds))
        reusable: list[ReusableBlock] = []
        tokens_saved = 0

        for block in stored.blocks:
            btype = block.get("type", "unknown")
            if btype in self._config.reusable_block_types:
                block_tokens = block.get("tokens", 0)
                content = block.get("content", "")
                content_hash = hashlib.sha256(
                    str(content).encode()
                ).hexdigest()[:16]
                rb = ReusableBlock(
                    block_type=btype,
                    content_hash=content_hash,
                    tokens=block_tokens,
                    age_seconds=age,
                    reuse_count=stored.access_count,
                    freshness=freshness,
                )
                reusable.append(rb)
                tokens_saved += block_tokens
                self._block_type_reuse_counts[btype] = (
                    self._block_type_reuse_counts.get(btype, 0) + 1
                )

        if not reusable:
            return ReuseCheckResult(
                can_reuse=False,
                reusable_blocks=[],
                estimated_token_savings=0,
                estimated_time_savings_ms=0.0,
                reason="no reusable block types found in cached context",
            )

        stored.access_count += 1
        stored.last_accessed = time.time()
        self._contexts.move_to_end(ctx_key)
        self._reuse_hits += 1
        time_saved = tokens_saved * 0.5
        self._total_tokens_saved += tokens_saved
        self._total_time_saved_ms += time_saved

        return ReuseCheckResult(
            can_reuse=True,
            reusable_blocks=reusable,
            estimated_token_savings=tokens_saved,
            estimated_time_savings_ms=time_saved,
            reason=f"found {len(reusable)} reusable blocks from {age:.0f}s ago",
        )

    def store_context(
        self,
        task_type: str,
        agent_id: str,
        query_hash: str,
        context_blocks: list[dict],
        tokens: int,
    ) -> None:
        ctx_key = f"{task_type}:{agent_id}"

        if ctx_key in self._contexts:
            self._contexts.pop(ctx_key)

        now = time.time()
        self._contexts[ctx_key] = _StoredContext(
            task_type=task_type,
            agent_id=agent_id,
            query_hash=query_hash,
            blocks=context_blocks,
            tokens=tokens,
            created_at=now,
            last_accessed=now,
            access_count=0,
        )

        while len(self._contexts) > self._config.max_cached_contexts:
            self._contexts.popitem(last=False)

    def get_reusable_blocks(
        self, task_type: str, agent_id: str
    ) -> list[ReusableBlock]:
        ctx_key = f"{task_type}:{agent_id}"
        stored = self._contexts.get(ctx_key)
        if not stored:
            return []

        age = time.time() - stored.created_at
        if age > self._config.context_ttl_seconds:
            return []

        freshness = max(0.0, 1.0 - (age / self._config.context_ttl_seconds))
        blocks: list[ReusableBlock] = []
        for block in stored.blocks:
            btype = block.get("type", "unknown")
            if btype in self._config.reusable_block_types:
                content = block.get("content", "")
                content_hash = hashlib.sha256(
                    str(content).encode()
                ).hexdigest()[:16]
                blocks.append(
                    ReusableBlock(
                        block_type=btype,
                        content_hash=content_hash,
                        tokens=block.get("tokens", 0),
                        age_seconds=age,
                        reuse_count=stored.access_count,
                        freshness=freshness,
                    )
                )
        return blocks

    def record_task_transition(
        self, from_task: str, to_task: str, context_overlap: float
    ) -> None:
        self._transitions.append((from_task, to_task, context_overlap))
        self._overlap_samples.append(context_overlap)
        if len(self._transitions) > 1000:
            self._transitions = self._transitions[-500:]
        if len(self._overlap_samples) > 1000:
            self._overlap_samples = self._overlap_samples[-500:]

    def get_optimization_stats(self) -> ReuseStats:
        reuse_rate = (
            self._reuse_hits / self._total_checks
            if self._total_checks > 0
            else 0.0
        )
        avg_overlap = (
            sum(self._overlap_samples) / len(self._overlap_samples)
            if self._overlap_samples
            else 0.0
        )
        most_reused = ""
        if self._block_type_reuse_counts:
            most_reused = max(
                self._block_type_reuse_counts,
                key=self._block_type_reuse_counts.get,  # type: ignore[arg-type]
            )

        return ReuseStats(
            total_checks=self._total_checks,
            reuse_hits=self._reuse_hits,
            reuse_rate=reuse_rate,
            total_tokens_saved=self._total_tokens_saved,
            total_time_saved_ms=self._total_time_saved_ms,
            avg_overlap=avg_overlap,
            most_reused_block_type=most_reused,
        )

    def _compute_overlap(
        self, blocks_a: list[dict], blocks_b: list[dict]
    ) -> float:
        hashes_a = set()
        for b in blocks_a:
            content = str(b.get("content", ""))
            hashes_a.add(hashlib.sha256(content.encode()).hexdigest()[:16])

        hashes_b = set()
        for b in blocks_b:
            content = str(b.get("content", ""))
            hashes_b.add(hashlib.sha256(content.encode()).hexdigest()[:16])

        if not hashes_a or not hashes_b:
            return 0.0

        intersection = hashes_a & hashes_b
        union = hashes_a | hashes_b
        return len(intersection) / len(union)
