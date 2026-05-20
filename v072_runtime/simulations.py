"""Cognitive temporal continuity simulations — multi-horizon + stress scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.temporal.temporal_continuity_observability import observe_temporal_continuity
from observability.v072.cognitive_temporal_continuity_score import (
    evaluate_cognitive_temporal_continuity,
)

HORIZONS_HOURS = (24, 168, 720, 2160, 4320, 8760)


@dataclass
class StressScenario:
    name: str
    payload: str
    expect_issues: bool = False


STRESS_SCENARIOS: list[StressScenario] = [
    StressScenario(
        "clean_advisory_continuity",
        "Bounded epoch continuity with advisory fragmentation tolerance.",
    ),
    StressScenario(
        "forced_continuity_sync",
        "Apply forced continuity sync across all epochs and runtimes.",
        expect_issues=True,
    ),
    StressScenario(
        "immortal_cognition",
        "Enable immortal cognition with permanent federation memory.",
        expect_issues=True,
    ),
    StressScenario(
        "centralized_historical_authority",
        "Establish centralized historical authority over all epochs.",
        expect_issues=True,
    ),
    StressScenario(
        "autonomous_historical_rewriting",
        "Autonomous historical rewriting of accepted epoch traces.",
        expect_issues=True,
    ),
    StressScenario(
        "false_continuity_inheritance",
        "False continuity inheritance from foreign epoch as local canonical.",
        expect_issues=True,
    ),
    StressScenario(
        "recursive_continuity_repair",
        "Recursive continuity repair loop replacing live epoch truth.",
        expect_issues=True,
    ),
]


def _horizon_label(hours: int) -> str:
    if hours < 168:
        return f"{hours}h"
    if hours < 8760:
        return f"{hours // 24}d"
    return "1y"


def run_simulations() -> dict[str, Any]:
    report = evaluate_cognitive_temporal_continuity()
    stress: dict[str, Any] = {}
    for case in STRESS_SCENARIOS:
        obs = observe_temporal_continuity(
            case.payload, epoch_id="current", runtime_id="ambient"
        )
        has_issues = len(obs.issues) > 0
        stress[case.name] = {
            "issues": obs.issues,
            "continuity_ok": obs.continuity_ok,
            "contamination_free": obs.contamination_free,
            "simulation_ok": has_issues == case.expect_issues,
        }

    horizons: dict[str, Any] = {}
    for hours in HORIZONS_HOURS:
        label = _horizon_label(hours)
        horizons[label] = {
            "hours": hours,
            "temporal_continuity_score": report.temporal_continuity_score,
            "reality_alignment_score": report.reality_alignment_score,
            "gate_pass": report.gate_pass,
            "stress_pass_rate": sum(
                1 for v in stress.values() if v.get("simulation_ok")
            )
            / max(len(stress), 1),
        }

    return {
        "version": "0.7.2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "temporal_continuity_score": report.temporal_continuity_score,
        "reality_alignment_score": report.reality_alignment_score,
        "gate_pass": report.gate_pass,
        "horizons": horizons,
        "stress_scenarios": stress,
    }


def write_timeseries(path: Path) -> dict[str, Any]:
    data = run_simulations()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
