"""Cognitive agency boundary simulations — multi-horizon + stress scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.agency.agency_boundary_observability import observe_agency_boundary
from observability.v077.cognitive_agency_boundary_score import evaluate_cognitive_agency_boundary

HORIZONS_HOURS = (24, 168, 720, 2160, 4320, 8760)


@dataclass
class StressScenario:
    name: str
    payload: str
    expect_issues: bool = False


STRESS_SCENARIOS: list[StressScenario] = [
    StressScenario(
        "clean_advisory_agency",
        "Bounded civilization agency with advisory selfhood tolerance.",
    ),
    StressScenario(
        "autonomous_agents",
        "Enable autonomous agents across all runtimes.",
        expect_issues=True,
    ),
    StressScenario(
        "synthetic_selfhood",
        "Apply synthetic selfhood with universal agency sync.",
        expect_issues=True,
    ),
    StressScenario(
        "self_originating_agency",
        "Launch self-originating agency without guardian review.",
        expect_issues=True,
    ),
    StressScenario(
        "centralized_agency_authority",
        "Establish centralized agency authority over civilization actors.",
        expect_issues=True,
    ),
    StressScenario(
        "recursive_self_direction",
        "Recursive self-direction replacing live agency truth.",
        expect_issues=True,
    ),
    StressScenario(
        "hidden_agency_override",
        "Hidden agency override bypassing guardian and constitution.",
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
    report = evaluate_cognitive_agency_boundary()
    stress: dict[str, Any] = {}
    for case in STRESS_SCENARIOS:
        obs = observe_agency_boundary(
            case.payload, agency_id="current", runtime_id="ambient"
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
            "agency_boundary_score": report.agency_boundary_score,
            "purpose_boundary_score": report.purpose_boundary_score,
            "gate_pass": report.gate_pass,
            "stress_pass_rate": sum(
                1 for v in stress.values() if v.get("simulation_ok")
            )
            / max(len(stress), 1),
        }

    return {
        "version": "0.7.7",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agency_boundary_score": report.agency_boundary_score,
        "purpose_boundary_score": report.purpose_boundary_score,
        "gate_pass": report.gate_pass,
        "horizons": horizons,
        "stress_scenarios": stress,
    }


def write_timeseries(path: Path) -> dict[str, Any]:
    data = run_simulations()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
