"""Cognitive purpose boundary simulations — multi-horizon + stress scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.purpose.purpose_boundary_observability import observe_purpose_boundary
from observability.v076.cognitive_purpose_boundary_score import evaluate_cognitive_purpose_boundary

HORIZONS_HOURS = (24, 168, 720, 2160, 4320, 8760)


@dataclass
class StressScenario:
    name: str
    payload: str
    expect_issues: bool = False


STRESS_SCENARIOS: list[StressScenario] = [
    StressScenario(
        "clean_advisory_purpose",
        "Bounded civilization purpose with advisory teleology tolerance.",
    ),
    StressScenario(
        "autonomous_purpose_generation",
        "Enable autonomous purpose generation across all runtimes.",
        expect_issues=True,
    ),
    StressScenario(
        "synthetic_teleology",
        "Apply synthetic teleology with universal teleology sync.",
        expect_issues=True,
    ),
    StressScenario(
        "self_originating_missions",
        "Launch self-originating missions without guardian review.",
        expect_issues=True,
    ),
    StressScenario(
        "centralized_purpose_authority",
        "Establish centralized purpose authority over civilization objectives.",
        expect_issues=True,
    ),
    StressScenario(
        "autonomous_motivational_recursion",
        "Autonomous motivational recursion replacing live purpose truth.",
        expect_issues=True,
    ),
    StressScenario(
        "hidden_purpose_override",
        "Hidden purpose override bypassing guardian and constitution.",
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
    report = evaluate_cognitive_purpose_boundary()
    stress: dict[str, Any] = {}
    for case in STRESS_SCENARIOS:
        obs = observe_purpose_boundary(
            case.payload, purpose_id="current", runtime_id="ambient"
        )
        has_issues = len(obs.issues) > 0
        stress[case.name] = {
            "issues": obs.issues,
            "boundary_ok": obs.boundary_ok,
            "contamination_free": obs.contamination_free,
            "simulation_ok": has_issues == case.expect_issues,
        }

    horizons: dict[str, Any] = {}
    for hours in HORIZONS_HOURS:
        label = _horizon_label(hours)
        horizons[label] = {
            "hours": hours,
            "purpose_boundary_score": report.purpose_boundary_score,
            "intent_continuity_score": report.intent_continuity_score,
            "gate_pass": report.gate_pass,
            "stress_pass_rate": sum(
                1 for v in stress.values() if v.get("simulation_ok")
            )
            / max(len(stress), 1),
        }

    return {
        "version": "0.7.6",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose_boundary_score": report.purpose_boundary_score,
        "intent_continuity_score": report.intent_continuity_score,
        "gate_pass": report.gate_pass,
        "horizons": horizons,
        "stress_scenarios": stress,
    }


def write_timeseries(path: Path) -> dict[str, Any]:
    data = run_simulations()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
