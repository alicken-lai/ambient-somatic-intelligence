"""Replay continuity analysis — replay bounded, never canonical epoch override."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01

_REPLAY_OVERRIDE = [
    (r"replay\s+becomes\s+canonical\s+epoch", "replay_canonical_epoch"),
    (r"replace\s+live\s+epoch\s+with\s+replay", "replay_epoch_override"),
    (r"recursive\s+continuity\s+repair", "recursive_continuity_repair"),
]


@dataclass
class ReplayContinuityVerdict:
    aligned: bool
    replay_bounded: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "aligned": self.aligned,
            "replay_bounded": self.replay_bounded,
            "issues": list(self.issues),
        }


class ReplayContinuityAnalysis:
    def evaluate(self, text: str, *, replay_hint: float = 0.0) -> ReplayContinuityVerdict:
        issues: list[str] = []
        lower = text.lower()
        for pattern, label in _REPLAY_OVERRIDE:
            if re.search(pattern, lower, re.IGNORECASE):
                issues.append(label)
        if replay_hint > 0.85 and "canonical" in lower:
            issues.append("high_replay_canonical_pressure")
        bounded = replay_hint <= 0.85 and len(issues) == 0
        return ReplayContinuityVerdict(
            aligned=bounded,
            replay_bounded=bounded,
            issues=issues,
        )
