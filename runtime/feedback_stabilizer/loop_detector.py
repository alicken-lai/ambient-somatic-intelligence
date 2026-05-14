from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DetectorConfig:
    max_generation_depth: int = 5
    detection_window_seconds: float = 300.0
    max_events: int = 5000
    enable_suppression: bool = False


@dataclass
class CausalEvent:
    event_id: str
    event_type: str
    source: str
    timestamp: float
    parent_event_id: str | None
    generation: int
    payload_summary: str


@dataclass
class DetectedLoop:
    loop_id: str
    events: list[str]
    generation_depth: int
    frequency: float
    first_seen: float
    last_seen: float
    is_known: bool


@dataclass
class CausalChain:
    chain_id: str
    events: list[CausalEvent]
    depth: int
    total_amplification: float
    is_bounded: bool


@dataclass
class DetectionResult:
    event_recorded: bool
    loop_detected: bool
    loops: list[DetectedLoop]
    generation: int
    should_suppress: bool
    reason: str


class LoopDetector:

    def __init__(self, config: DetectorConfig | None = None) -> None:
        self._config = config or DetectorConfig()
        self._events: deque[CausalEvent] = deque(maxlen=self._config.max_events)
        self._event_index: dict[str, CausalEvent] = {}
        self._detected_loops: dict[str, DetectedLoop] = {}
        self._known_loop_ids: set[str] = set()

    def record_event(self, event: CausalEvent) -> DetectionResult:
        now = time.time()
        self._prune_window(now)

        generation = self._compute_generation(event)
        event = CausalEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            source=event.source,
            timestamp=event.timestamp,
            parent_event_id=event.parent_event_id,
            generation=generation,
            payload_summary=event.payload_summary,
        )

        self._events.append(event)
        self._event_index[event.event_id] = event

        loops = self._check_for_loops(event)
        exceeds_depth = generation >= self._config.max_generation_depth

        should_suppress = False
        reason = ""
        if exceeds_depth:
            reason = f"Generation {generation} exceeds max depth {self._config.max_generation_depth}"
            if self._config.enable_suppression:
                should_suppress = True
        elif loops:
            reason = f"Loop detected: {[l.loop_id for l in loops]}"

        return DetectionResult(
            event_recorded=True,
            loop_detected=len(loops) > 0,
            loops=loops,
            generation=generation,
            should_suppress=should_suppress,
            reason=reason,
        )

    def _compute_generation(self, event: CausalEvent) -> int:
        if event.parent_event_id is None:
            return 0
        parent = self._event_index.get(event.parent_event_id)
        if parent is None:
            return event.generation
        return parent.generation + 1

    def _check_for_loops(self, event: CausalEvent) -> list[DetectedLoop]:
        loops: list[DetectedLoop] = []
        chain = self._trace_chain(event)

        sources_seen: dict[str, list[CausalEvent]] = {}
        for ev in chain:
            sources_seen.setdefault(ev.source, []).append(ev)

        for source, occurrences in sources_seen.items():
            if len(occurrences) < 2:
                continue
            loop_id = f"detected_{source}_{int(event.timestamp)}"
            event_ids = [e.event_id for e in chain]
            detected = DetectedLoop(
                loop_id=loop_id,
                events=event_ids,
                generation_depth=event.generation,
                frequency=len(occurrences) / max(
                    chain[-1].timestamp - chain[0].timestamp, 0.001
                ),
                first_seen=occurrences[0].timestamp,
                last_seen=occurrences[-1].timestamp,
                is_known=source in self._known_loop_ids,
            )
            self._detected_loops[loop_id] = detected
            loops.append(detected)

        return loops

    def _trace_chain(self, event: CausalEvent) -> list[CausalEvent]:
        chain: list[CausalEvent] = []
        current: CausalEvent | None = event
        visited: set[str] = set()
        while current is not None and current.event_id not in visited:
            visited.add(current.event_id)
            chain.append(current)
            if current.parent_event_id is None:
                break
            current = self._event_index.get(current.parent_event_id)
        chain.reverse()
        return chain

    def _prune_window(self, now: float) -> None:
        cutoff = now - self._config.detection_window_seconds
        while self._events and self._events[0].timestamp < cutoff:
            old = self._events.popleft()
            self._event_index.pop(old.event_id, None)

    def detect_loops(self) -> list[DetectedLoop]:
        return list(self._detected_loops.values())

    def get_active_chains(self) -> list[CausalChain]:
        chains: list[CausalChain] = []
        root_events = [e for e in self._events if e.parent_event_id is None]
        for root in root_events:
            chain_events = self._find_descendants(root)
            if len(chain_events) < 2:
                continue
            depth = max(e.generation for e in chain_events)
            chains.append(CausalChain(
                chain_id=f"chain_{root.event_id}",
                events=chain_events,
                depth=depth,
                total_amplification=float(len(chain_events)),
                is_bounded=depth <= self._config.max_generation_depth,
            ))
        return chains

    def _find_descendants(self, root: CausalEvent) -> list[CausalEvent]:
        descendants = [root]
        queue: deque[str] = deque([root.event_id])
        while queue:
            parent_id = queue.popleft()
            for ev in self._events:
                if ev.parent_event_id == parent_id and ev.event_id != parent_id:
                    descendants.append(ev)
                    queue.append(ev.event_id)
        return descendants

    def get_generation_depth(self, event_id: str) -> int:
        event = self._event_index.get(event_id)
        if event is None:
            return -1
        return event.generation

    def is_loop_active(self, loop_id: str) -> bool:
        return loop_id in self._detected_loops

    def reset(self) -> None:
        self._events.clear()
        self._event_index.clear()
        self._detected_loops.clear()
