"""1000-cycle CognitiveGovernor stress — deterministic advisory consistency."""

from __future__ import annotations

import json
from pathlib import Path

from attention.core.attention_target import AttentionTarget
from governance.cognition.cognitive_governor import CognitiveGovernor


def _run_sequence(cycles: int) -> tuple[list[float], list[bool]]:
    gov = CognitiveGovernor()
    targets = [
        AttentionTarget("telemetry", "civilization-stress-clean", 0.55),
        AttentionTarget("telemetry", "civilization-stress-treaty", 0.62),
        AttentionTarget("telemetry", "civilization-stress-replay", 0.48),
    ]
    scores: list[float] = []
    accepted: list[bool] = []
    for i in range(cycles):
        target = targets[i % len(targets)]
        result = gov.govern_target(target)
        scores.append(round(float(result.governed_salience), 8))
        accepted.append(bool(result.accepted))
    return scores, accepted


def run_stress(cycles: int = 1000) -> dict:
    scores_a, accepted_a = _run_sequence(cycles)
    scores_b, accepted_b = _run_sequence(cycles)
    replay_match = scores_a == scores_b and accepted_a == accepted_b
    return {
        "cycles": cycles,
        "replay_deterministic": replay_match,
        "unique_accepted_values": sorted(set(accepted_a)),
        "score_range": [min(scores_a), max(scores_a)],
        "first_score": scores_a[0],
        "last_score": scores_a[-1],
    }


if __name__ == "__main__":
    out = run_stress()
    path = Path(__file__).resolve().parent / "governor_stress_1000.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out["replay_deterministic"], out["score_range"])
