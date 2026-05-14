"""
Context Injection Logger — Audit trail for memory-to-agent context injection.

Tracks every context injection event so we can answer:
  - What memories were injected into agent X's context at time T?
  - How many tokens did agent Y consume from memory over the past hour?
  - Which memories are most frequently injected across all agents?

Integration points:
  - ContextAssembler calls log_injection() after building a context block
  - IntegrationBus wires injection events to the observability tracer
  - InjectionLogger is available via AmbientKernel.context.injection_logger
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
INJECTION_LOG_DIR = AMBIENT_ROOT / "observability" / "injection_logs"


@dataclass
class InjectionEvent:
    """A single context injection record."""
    agent_id: str
    query: str
    memories_injected: list[dict[str, Any]]
    tokens_used: int
    timestamp: float = field(default_factory=time.time)
    retrieval_stats: dict[str, Any] = field(default_factory=dict)
    compression_applied: bool = False
    event_id: str = ""

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"inj_{int(self.timestamp * 1000)}"

    @property
    def memory_count(self) -> int:
        return len(self.memories_injected)

    @property
    def layers_used(self) -> list[str]:
        return list({m.get("layer", "unknown") for m in self.memories_injected})

    @property
    def top_score(self) -> float:
        scores = [m.get("score", 0) for m in self.memories_injected]
        return max(scores) if scores else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "query": self.query,
            "memory_count": self.memory_count,
            "tokens_used": self.tokens_used,
            "layers_used": self.layers_used,
            "top_score": round(self.top_score, 4),
            "compression_applied": self.compression_applied,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
            "retrieval_stats": self.retrieval_stats,
            "memories": [
                {
                    "layer": m.get("layer", ""),
                    "score": round(m.get("score", 0), 4),
                    "content_preview": str(m.get("content", ""))[:120],
                    "tags": m.get("tags", []),
                }
                for m in self.memories_injected
            ],
        }


class InjectionLogger:
    """
    Records and queries context injection events for observability.

    Usage:
        logger = InjectionLogger()

        logger.log_injection(
            agent_id="frontend-agent",
            query="how to fix login bug",
            memories=[{"content": "...", "layer": "procedural", "score": 0.9}],
            tokens_used=1200,
        )

        events = logger.query_by_agent("frontend-agent", limit=10)
        stats = logger.stats(hours=1)
    """

    def __init__(self, persist: bool = True, max_events: int = 500):
        self._events: list[InjectionEvent] = []
        self._max_events = max_events
        self._persist = persist
        self._listeners: list[Callable[[InjectionEvent], None]] = []

        if persist:
            INJECTION_LOG_DIR.mkdir(parents=True, exist_ok=True)

    def log_injection(
        self,
        agent_id: str,
        query: str,
        memories: list[dict[str, Any]],
        tokens_used: int,
        retrieval_stats: dict[str, Any] | None = None,
        compression_applied: bool = False,
    ) -> InjectionEvent:
        """Record a context injection event."""
        event = InjectionEvent(
            agent_id=agent_id,
            query=query,
            memories_injected=memories,
            tokens_used=tokens_used,
            retrieval_stats=retrieval_stats or {},
            compression_applied=compression_applied,
        )

        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                pass

        if self._persist:
            self._persist_event(event)

        return event

    def on_injection(self, callback: Callable[[InjectionEvent], None]) -> None:
        """Register a listener for injection events (used by IntegrationBus)."""
        self._listeners.append(callback)

    def query_by_agent(
        self,
        agent_id: str,
        limit: int = 20,
        since: float | None = None,
    ) -> list[dict[str, Any]]:
        """Get injection events for a specific agent."""
        filtered = [
            e for e in self._events
            if e.agent_id == agent_id
            and (since is None or e.timestamp >= since)
        ]
        filtered.sort(key=lambda e: e.timestamp, reverse=True)
        return [e.to_dict() for e in filtered[:limit]]

    def query_by_time(
        self,
        since: float,
        until: float | None = None,
        agent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get injection events within a time window."""
        until = until or time.time()
        filtered = [
            e for e in self._events
            if since <= e.timestamp <= until
            and (agent_id is None or e.agent_id == agent_id)
        ]
        filtered.sort(key=lambda e: e.timestamp, reverse=True)
        return [e.to_dict() for e in filtered]

    def stats(self, hours: float = 1.0) -> dict[str, Any]:
        """Aggregate injection statistics over a time window."""
        cutoff = time.time() - (hours * 3600)
        recent = [e for e in self._events if e.timestamp >= cutoff]

        if not recent:
            return {
                "window_hours": hours,
                "total_injections": 0,
                "total_tokens": 0,
                "total_memories": 0,
                "unique_agents": 0,
                "by_agent": {},
                "by_layer": {},
            }

        by_agent: dict[str, dict[str, int]] = defaultdict(
            lambda: {"injections": 0, "tokens": 0, "memories": 0}
        )
        by_layer: dict[str, int] = defaultdict(int)

        total_tokens = 0
        total_memories = 0

        for e in recent:
            by_agent[e.agent_id]["injections"] += 1
            by_agent[e.agent_id]["tokens"] += e.tokens_used
            by_agent[e.agent_id]["memories"] += e.memory_count
            total_tokens += e.tokens_used
            total_memories += e.memory_count
            for layer in e.layers_used:
                by_layer[layer] += 1

        return {
            "window_hours": hours,
            "total_injections": len(recent),
            "total_tokens": total_tokens,
            "total_memories": total_memories,
            "unique_agents": len(by_agent),
            "by_agent": dict(by_agent),
            "by_layer": dict(by_layer),
            "avg_tokens_per_injection": round(total_tokens / len(recent)),
            "avg_memories_per_injection": round(total_memories / len(recent), 1),
        }

    def recent_events(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get the most recent injection events."""
        return [e.to_dict() for e in self._events[-limit:]]

    def _persist_event(self, event: InjectionEvent) -> None:
        """Append event to disk as JSONL."""
        try:
            date_str = datetime.fromtimestamp(
                event.timestamp, tz=timezone.utc
            ).strftime("%Y-%m-%d")
            filepath = INJECTION_LOG_DIR / f"injections_{date_str}.jsonl"
            with filepath.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            pass
