"""
Execution Lineage — Track complete execution lineage from user request
through task dispatch, agent execution, memory access, governance checks,
to completion.

Every event is linked to its causal parent, forming a directed acyclic graph
that can be traversed upward (get_lineage) or downward (get_descendants).
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from observability.cognitive_trace_v2.causal_trace_schema import (
    CausalChain,
    CausalEvent,
    CausalEventType,
)

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
LINEAGE_DIR = AMBIENT_ROOT / "observability" / "cognitive_trace_v2" / "lineage_data"


@dataclass
class LineageConfig:
    max_events: int = 10000
    max_active_traces: int = 100
    persist_dir: str | None = None
    auto_persist: bool = True


class ExecutionLineageTracer:

    def __init__(self, config: LineageConfig | None = None) -> None:
        self._config = config or LineageConfig()
        self._events: dict[str, CausalEvent] = {}
        self._children: dict[str, list[str]] = defaultdict(list)
        self._active_traces: dict[str, CausalEvent] = {}
        self._completed_chains: list[CausalChain] = []
        self._event_order: list[str] = []

        self._persist_dir = Path(self._config.persist_dir) if self._config.persist_dir else LINEAGE_DIR
        if self._config.auto_persist:
            self._persist_dir.mkdir(parents=True, exist_ok=True)

    def begin_trace(self, trigger: str, metadata: dict[str, Any] | None = None) -> str:
        if len(self._active_traces) >= self._config.max_active_traces:
            oldest_id = next(iter(self._active_traces))
            logger.warning("Evicting oldest active trace %s to make room", oldest_id)
            self.complete_trace(oldest_id, "evicted")

        event = CausalEvent(
            event_id=uuid.uuid4().hex,
            event_type=CausalEventType.TASK_DISPATCH,
            timestamp=time.time(),
            source_subsystem="lineage",
            source_component="ExecutionLineageTracer",
            action=trigger,
            parent_event_id=None,
            root_event_id=None,
            generation=0,
            agent_id=None,
            task_id=None,
            payload=metadata or {},
            outcome=None,
            duration_ms=None,
            metadata={"trigger": trigger},
        )
        event.root_event_id = event.event_id

        self._store_event(event)
        self._active_traces[event.event_id] = event

        logger.debug("Began trace %s trigger=%s", event.event_id, trigger)
        return event.event_id

    def record_event(self, event: CausalEvent) -> None:
        self._store_event(event)

        if event.parent_event_id:
            self._children[event.parent_event_id].append(event.event_id)

        if self._config.auto_persist:
            self._persist_event(event)

        logger.debug(
            "Recorded event %s type=%s parent=%s",
            event.event_id, event.event_type.value, event.parent_event_id,
        )

    def create_child_event(
        self,
        parent_id: str,
        event_type: CausalEventType,
        source_subsystem: str,
        source_component: str,
        action: str,
        **kwargs: Any,
    ) -> CausalEvent:
        parent = self._events.get(parent_id)
        if parent is None:
            raise ValueError(f"Parent event {parent_id} not found")

        root_id = parent.root_event_id or parent.event_id
        generation = parent.generation + 1

        event = CausalEvent(
            event_id=uuid.uuid4().hex,
            event_type=event_type,
            timestamp=time.time(),
            source_subsystem=source_subsystem,
            source_component=source_component,
            action=action,
            parent_event_id=parent_id,
            root_event_id=root_id,
            generation=generation,
            agent_id=kwargs.get("agent_id"),
            task_id=kwargs.get("task_id"),
            payload=kwargs.get("payload", {}),
            outcome=kwargs.get("outcome"),
            duration_ms=kwargs.get("duration_ms"),
            metadata=kwargs.get("metadata", {}),
        )
        return event

    def complete_trace(self, trace_id: str, outcome: str) -> CausalChain:
        root_event = self._active_traces.pop(trace_id, None)
        if root_event is None:
            root_event = self._events.get(trace_id)
        if root_event is None:
            raise ValueError(f"Trace {trace_id} not found")

        root_event.outcome = outcome
        all_events = self._collect_descendants(trace_id)
        all_events.insert(0, root_event)

        chain = CausalChain.from_events(
            chain_id=trace_id,
            root=root_event,
            events=all_events,
            outcome=outcome,
        )
        self._completed_chains.append(chain)

        logger.debug(
            "Completed trace %s outcome=%s events=%d depth=%d",
            trace_id, outcome, len(all_events), chain.depth,
        )
        return chain

    def get_chain(self, root_event_id: str) -> CausalChain | None:
        for chain in self._completed_chains:
            if chain.chain_id == root_event_id:
                return chain

        root = self._events.get(root_event_id)
        if root is None:
            return None

        descendants = self._collect_descendants(root_event_id)
        all_events = [root] + descendants
        return CausalChain.from_events(
            chain_id=root_event_id,
            root=root,
            events=all_events,
            outcome=root.outcome or "unknown",
        )

    def get_lineage(self, event_id: str) -> list[CausalEvent]:
        lineage: list[CausalEvent] = []
        current_id: str | None = event_id

        visited: set[str] = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            event = self._events.get(current_id)
            if event is None:
                break
            lineage.append(event)
            current_id = event.parent_event_id

        lineage.reverse()
        return lineage

    def get_descendants(self, event_id: str) -> list[CausalEvent]:
        return self._collect_descendants(event_id)

    def get_active_traces(self) -> list[str]:
        return list(self._active_traces.keys())

    def search(
        self,
        subsystem: str | None = None,
        event_type: CausalEventType | None = None,
        agent_id: str | None = None,
        since: float | None = None,
    ) -> list[CausalEvent]:
        results: list[CausalEvent] = []
        for eid in self._event_order:
            event = self._events.get(eid)
            if event is None:
                continue
            if subsystem and event.source_subsystem != subsystem:
                continue
            if event_type and event.event_type != event_type:
                continue
            if agent_id and event.agent_id != agent_id:
                continue
            if since and event.timestamp < since:
                continue
            results.append(event)
        return results

    def get_event(self, event_id: str) -> CausalEvent | None:
        return self._events.get(event_id)

    def event_count(self) -> int:
        return len(self._events)

    def _store_event(self, event: CausalEvent) -> None:
        self._events[event.event_id] = event
        self._event_order.append(event.event_id)
        self._enforce_limits()

    def _enforce_limits(self) -> None:
        while len(self._events) > self._config.max_events and self._event_order:
            oldest_id = self._event_order.pop(0)
            self._events.pop(oldest_id, None)
            self._children.pop(oldest_id, None)

    def _collect_descendants(self, event_id: str) -> list[CausalEvent]:
        descendants: list[CausalEvent] = []
        queue = list(self._children.get(event_id, []))
        visited: set[str] = set()

        while queue:
            eid = queue.pop(0)
            if eid in visited:
                continue
            visited.add(eid)
            event = self._events.get(eid)
            if event is None:
                continue
            descendants.append(event)
            queue.extend(self._children.get(eid, []))

        descendants.sort(key=lambda e: e.timestamp)
        return descendants

    def _persist_event(self, event: CausalEvent) -> None:
        try:
            filepath = self._persist_dir / "lineage.jsonl"
            with filepath.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            logger.warning("Failed to persist lineage event %s", event.event_id)
