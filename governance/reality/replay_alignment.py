"""Replay alignment — bound replay truth without overriding live reality."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from observability.v04.metric_normalizer import clamp01


@dataclass
class ReplayAlignmentVerdict:
    aligned: bool
    replay_bounded: bool
    replay_hint: float = 0.0
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "aligned": self.aligned,
            "replay_bounded": self.replay_bounded,
            "replay_hint": round(self.replay_hint, 4),
            "issues": list(self.issues),
        }


class ReplayAlignment:
    def evaluate(
        self,
        text: str,
        *,
        replay_hint: float = 0.0,
    ) -> ReplayAlignmentVerdict:
        issues: list[str] = []
        lower = text.lower()
        if "replay becomes canonical truth" in lower:
            issues.append("replay_canonical_override")
        if "replace live operational truth" in lower:
            issues.append("live_truth_replacement")
        bounded = replay_hint <= 0.85 and "replay_canonical_override" not in issues
        aligned = bounded and "live_truth_replacement" not in issues
        return ReplayAlignmentVerdict(
            aligned=aligned,
            replay_bounded=bounded,
            replay_hint=clamp01(replay_hint),
            issues=issues,
        )
