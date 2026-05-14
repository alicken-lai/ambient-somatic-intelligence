"""
Precursor Matcher — Detect signal patterns that precede significant events.

Learns from historical episodes which signal-type / env-signature combinations
tend to appear *before* high-severity events, then matches current signals
against those learned patterns to issue early warnings.

This module is **detection-only** — it never takes corrective action.
Every match includes a confidence score.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from memory.somatic.environmental_signature import EnvironmentalSignature

logger = logging.getLogger(__name__)


# ── Data types ────────────────────────────────────────────────────────────


@dataclass
class PrecursorPattern:
    """A learned pattern that historically precedes a target event."""

    pattern_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    precursor_signals: list[str] = field(default_factory=list)
    precursor_env_signature: Optional[EnvironmentalSignature] = None
    target_event_type: str = ""
    confidence: float = 0.0
    support_count: int = 0
    avg_lead_time_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "precursor_signals": self.precursor_signals,
            "precursor_env_signature": (
                self.precursor_env_signature.to_dict()
                if self.precursor_env_signature
                else None
            ),
            "target_event_type": self.target_event_type,
            "confidence": round(self.confidence, 4),
            "support_count": self.support_count,
            "avg_lead_time_seconds": round(self.avg_lead_time_seconds, 2),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PrecursorPattern:
        env = data.get("precursor_env_signature")
        return cls(
            pattern_id=data.get("pattern_id", uuid.uuid4().hex[:12]),
            precursor_signals=data.get("precursor_signals", []),
            precursor_env_signature=(
                EnvironmentalSignature.from_dict(env) if env else None
            ),
            target_event_type=data.get("target_event_type", ""),
            confidence=float(data.get("confidence", 0.0)),
            support_count=int(data.get("support_count", 0)),
            avg_lead_time_seconds=float(data.get("avg_lead_time_seconds", 0.0)),
        )


@dataclass
class PrecursorMatch:
    """A current-state match against a learned precursor pattern."""

    pattern: PrecursorPattern
    match_confidence: float = 0.0
    estimated_time_to_event: float = 0.0
    recommended_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern": self.pattern.to_dict(),
            "match_confidence": round(self.match_confidence, 4),
            "estimated_time_to_event": round(self.estimated_time_to_event, 2),
            "recommended_action": self.recommended_action,
        }


# ── PrecursorMatcher ──────────────────────────────────────────────────────

_SEVERITY_THRESHOLD = 0.5
_MIN_SUPPORT = 2


class PrecursorMatcher:
    """
    Learns and detects precursor patterns from somatic episodes.

    Usage::

        matcher = PrecursorMatcher()
        patterns = matcher.learn_precursors(episodes)
        matches = matcher.match_current(current_signals, current_env, patterns)
        for m in matches:
            print(m.recommended_action, m.match_confidence)
    """

    def __init__(
        self,
        severity_threshold: float = _SEVERITY_THRESHOLD,
        min_support: int = _MIN_SUPPORT,
    ):
        self._severity_threshold = severity_threshold
        self._min_support = min_support

    # ── Learning ──────────────────────────────────────────────────────

    def learn_precursors(
        self,
        episodes: list[Any],
        lookback_minutes: int = 30,
    ) -> list[PrecursorPattern]:
        """Mine precursor patterns from a list of SensorEpisodes.

        For every high-severity episode, collect signal types from preceding
        episodes (within *lookback_minutes*) and record the combination as a
        candidate precursor pattern.  Patterns that recur at least
        ``min_support`` times are returned.
        """
        episodes_sorted = sorted(episodes, key=lambda e: e.timestamp)
        lookback = timedelta(minutes=lookback_minutes)

        candidate_counts: dict[str, dict[str, Any]] = {}

        for idx, target_ep in enumerate(episodes_sorted):
            if target_ep.severity_peak < self._severity_threshold:
                continue

            precursor_types: set[str] = set()
            precursor_envs: list[EnvironmentalSignature] = []
            lead_times: list[float] = []

            for prev_ep in episodes_sorted[:idx]:
                time_diff = target_ep.timestamp - prev_ep.timestamp
                if time_diff > lookback or time_diff.total_seconds() <= 0:
                    continue
                precursor_types.update(prev_ep.signal_types)
                if prev_ep.environmental_signature:
                    precursor_envs.append(
                        EnvironmentalSignature.from_dict(prev_ep.environmental_signature)
                    )
                lead_times.append(time_diff.total_seconds())

            if not precursor_types:
                continue

            target_type = self._dominant_signal_type(target_ep)
            key = "+".join(sorted(precursor_types)) + "→" + target_type

            if key not in candidate_counts:
                candidate_counts[key] = {
                    "precursor_signals": sorted(precursor_types),
                    "target_event_type": target_type,
                    "support": 0,
                    "lead_times": [],
                    "envs": [],
                }

            candidate_counts[key]["support"] += 1
            candidate_counts[key]["lead_times"].extend(lead_times)
            if precursor_envs:
                candidate_counts[key]["envs"].append(precursor_envs[0])

        patterns: list[PrecursorPattern] = []
        total_targets = max(
            sum(1 for e in episodes_sorted if e.severity_peak >= self._severity_threshold),
            1,
        )

        for key, info in candidate_counts.items():
            if info["support"] < self._min_support:
                continue

            avg_lead = (
                sum(info["lead_times"]) / len(info["lead_times"])
                if info["lead_times"]
                else 0.0
            )
            confidence = min(info["support"] / total_targets, 1.0)

            env_sig: Optional[EnvironmentalSignature] = None
            if info["envs"]:
                env_sig = info["envs"][0]

            patterns.append(PrecursorPattern(
                precursor_signals=info["precursor_signals"],
                precursor_env_signature=env_sig,
                target_event_type=info["target_event_type"],
                confidence=confidence,
                support_count=info["support"],
                avg_lead_time_seconds=avg_lead,
            ))

        patterns.sort(key=lambda p: p.confidence, reverse=True)
        logger.info("Learned %d precursor patterns from %d episodes", len(patterns), len(episodes))
        return patterns

    # ── Matching ──────────────────────────────────────────────────────

    def match_current(
        self,
        current_signals: list[dict[str, Any]],
        current_env: dict[str, Any],
        patterns: list[PrecursorPattern],
    ) -> list[PrecursorMatch]:
        """Match current state against learned patterns.

        Returns a list of matches sorted by descending confidence.
        Every match includes an uncertainty-aware confidence score.
        """
        current_types = {str(s.get("type", "")).lower() for s in current_signals}
        current_env_sig = EnvironmentalSignature.from_snapshot(current_env) if current_env else EnvironmentalSignature()

        matches: list[PrecursorMatch] = []
        for pattern in patterns:
            score = self._score_match(pattern, current_types, current_env_sig)
            if score < 0.2:
                continue

            combined = score * pattern.confidence

            action = self._suggest_action(pattern, combined)

            matches.append(PrecursorMatch(
                pattern=pattern,
                match_confidence=round(combined, 4),
                estimated_time_to_event=pattern.avg_lead_time_seconds,
                recommended_action=action,
            ))

        matches.sort(key=lambda m: m.match_confidence, reverse=True)
        return matches

    # ── Internal helpers ──────────────────────────────────────────────

    def _score_match(
        self,
        pattern: PrecursorPattern,
        current_types: set[str],
        current_env: EnvironmentalSignature,
    ) -> float:
        pattern_types = {s.lower() for s in pattern.precursor_signals}
        if not pattern_types:
            return 0.0

        overlap = current_types & pattern_types
        type_score = len(overlap) / len(pattern_types)

        env_score = 1.0
        if pattern.precursor_env_signature is not None:
            dist = pattern.precursor_env_signature.distance_to(current_env)
            env_score = 1.0 - dist

        return type_score * 0.7 + env_score * 0.3

    @staticmethod
    def _dominant_signal_type(episode: Any) -> str:
        if episode.signal_types:
            return episode.signal_types[0]
        return "unknown"

    @staticmethod
    def _suggest_action(pattern: PrecursorPattern, confidence: float) -> str:
        lead = pattern.avg_lead_time_seconds
        target = pattern.target_event_type

        if confidence >= 0.7:
            verb = "Prepare for likely"
        elif confidence >= 0.4:
            verb = "Monitor for possible"
        else:
            verb = "Low-confidence indicator of potential"

        if lead > 0:
            minutes = lead / 60.0
            return f"{verb} {target} event (avg lead time {minutes:.0f}m)"
        return f"{verb} {target} event"
