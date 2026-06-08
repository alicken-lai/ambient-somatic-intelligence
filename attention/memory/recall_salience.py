"""
Recall salience — boosts targets that resonate with recent memory.

A target is more salient when it matches patterns the system has recently found
important (tracked by :class:`ResonanceMemory`) and when its tags overlap the
caller's ``recent_tags`` context.

``RecallSalience.score`` blends three signals into a ``[0, 1]`` score:

- the target's intrinsic ``raw_value``
- the resonance strength for its ``(source_domain, signal_type)``
- the overlap between its tags and the supplied ``recent_tags``
"""

from __future__ import annotations

from typing import Optional

from attention.core.attention_target import AttentionTarget


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class ResonanceMemory:
    """Tracks an exponentially-weighted resonance per ``(domain, type)``."""

    def __init__(self, alpha: float = 0.5) -> None:
        self.alpha = max(0.0, min(1.0, float(alpha)))
        self._strength: dict[tuple[str, str], float] = {}

    def record(self, domain: str, signal_type: str, value: float) -> None:
        """Reinforce the resonance for ``(domain, signal_type)``."""
        key = (domain, signal_type)
        prev = self._strength.get(key, 0.0)
        self._strength[key] = _clamp_unit(
            (1.0 - self.alpha) * prev + self.alpha * _clamp_unit(value)
        )

    def lookup(self, domain: str, signal_type: str) -> float:
        """Return the current resonance strength (0.0 if unseen)."""
        return self._strength.get((domain, signal_type), 0.0)


class RecallSalience:
    """Scores a target by how strongly it resonates with recent memory."""

    def __init__(
        self,
        raw_weight: float = 0.4,
        resonance_weight: float = 0.4,
        tag_weight: float = 0.2,
    ) -> None:
        self.raw_weight = raw_weight
        self.resonance_weight = resonance_weight
        self.tag_weight = tag_weight
        self.resonance = ResonanceMemory()

    def score(
        self,
        target: AttentionTarget,
        recent_tags: Optional[list[str]] = None,
    ) -> float:
        """Return the recall-boosted salience for *target* in ``[0, 1]``."""
        base = _clamp_unit(target.raw_value)
        res = self.resonance.lookup(target.source_domain, target.signal_type)

        tag_overlap = 0.0
        if recent_tags:
            target_tags = set(target.metadata.get("tags", []) or [])
            if target_tags:
                matches = target_tags & set(recent_tags)
                tag_overlap = len(matches) / len(set(recent_tags))

        return _clamp_unit(
            self.raw_weight * base
            + self.resonance_weight * res
            + self.tag_weight * tag_overlap
        )
