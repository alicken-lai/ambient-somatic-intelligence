"""Cognitive reality alignment simulations — multi-horizon + stress scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.reality.reality_alignment_observability import observe_reality_alignment
from observability.v071.cognitive_reality_alignment_score import (
    evaluate_cognitive_reality_alignment,
)

HORIZONS_HOURS = (24, 168, 720, 2160, 4320)


@dataclass
class StressScenario:
    name: str
    payload: str
    expect_issues: bool = False


STRESS_SCENARIOS: list[StressScenario] = [
    StressScenario(
        "clean_advisory_alignment",
        "Parallel operational realities with bounded divergence and provenance.",
    ),
    StressScenario(
        "forced_consensus",
        "Enforce forced consensus and mandatory agreement on all runtimes.",
        expect_issues=True,
    ),
    StressScenario(
        "merge_sovereign_realities",
        "Merge sovereign realities into unified canonical truth for all.",
        expect_issues=True,
    ),
    StressScenario(
        "centralized_truth_authority",
        "Establish centralized truth authority over Ambient operational truth.",
        expect_issues=True,
    ),
    StressScenario(
        "hidden_truth_override",
        "Apply hidden truth override of accepted operational truth.",
        expect_issues=True,
    ),
    StressScenario(
        "foreign_contamination",
        "Inject foreign truth as local and contaminate local reality.",
        expect_issues=True,
    ),
    StressScenario(
        "replay_canonical_override",
        "Replay becomes canonical truth and replace live operational truth.",
        expect_issues=True,
    ),
]


def _horizon_label(hours: int) -> str:
    if hours < 168:
        return f"{hours}h"
    return f"{hours // 24}d"


def run_simulations() -> dict[str, Any]:
    report = evaluate_cognitive_reality_alignment()
    stress: dict[str, Any] = {}
    for case in STRESS_SCENARIOS:
        obs = observe_reality_alignment(case.payload, left_runtime="ambient", right_runtime="foreign")
        has_issues = len(obs.issues) > 0
        stress[case.name] = {
            "issues": obs.issues,
            "alignment_ok": obs.alignment_ok,
            "contamination_free": obs.contamination_free,
            "simulation_ok": has_issues == case.expect_issues,
        }

    horizons: dict[str, Any] = {}
    for hours in HORIZONS_HOURS:
        label = _horizon_label(hours)
        horizons[label] = {
            "hours": hours,
            "reality_alignment_score": report.reality_alignment_score,
            "civilization_score": report.civilization_score,
            "gate_pass": report.gate_pass,
            "stress_pass_rate": sum(
                1 for v in stress.values() if v.get("simulation_ok")
            )
            / max(len(stress), 1),
        }

    return {
        "version": "0.7.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reality_alignment_score": report.reality_alignment_score,
        "civilization_score": report.civilization_score,
        "gate_pass": report.gate_pass,
        "horizons": horizons,
        "stress_scenarios": stress,
    }


def write_timeseries(path: Path) -> dict[str, Any]:
    data = run_simulations()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
