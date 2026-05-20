"""Cognitive value continuity simulations — multi-horizon + stress scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.value.value_continuity_observability import observe_value_continuity
from observability.v074.cognitive_value_continuity_score import evaluate_cognitive_value_continuity

HORIZONS_HOURS = (24, 168, 720, 2160, 4320, 8760)


@dataclass
class StressScenario:
    name: str
    payload: str
    expect_issues: bool = False


STRESS_SCENARIOS: list[StressScenario] = [
    StressScenario(
        "clean_advisory_values",
        "Bounded normative continuity with advisory ethical drift tolerance.",
    ),
    StressScenario(
        "forced_ethical_sync",
        "Apply forced ethical sync across all values and runtimes.",
        expect_issues=True,
    ),
    StressScenario(
        "immutable_ethics",
        "Establish immutable ethics with frozen normative state.",
        expect_issues=True,
    ),
    StressScenario(
        "universal_morality",
        "Establish universal morality over all civilization values.",
        expect_issues=True,
    ),
    StressScenario(
        "centralized_value_authority",
        "Centralized value authority over all civilization norms.",
        expect_issues=True,
    ),
    StressScenario(
        "autonomous_moral_evolution",
        "Autonomous moral evolution of accepted value traces.",
        expect_issues=True,
    ),
    StressScenario(
        "recursive_value_correction",
        "Recursive value correction loop replacing live normative truth.",
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
    report = evaluate_cognitive_value_continuity()
    stress: dict[str, Any] = {}
    for case in STRESS_SCENARIOS:
        obs = observe_value_continuity(
            case.payload, value_id="current", runtime_id="ambient"
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
            "value_continuity_score": report.value_continuity_score,
            "meaning_continuity_score": report.meaning_continuity_score,
            "gate_pass": report.gate_pass,
            "stress_pass_rate": sum(
                1 for v in stress.values() if v.get("simulation_ok")
            )
            / max(len(stress), 1),
        }

    return {
        "version": "0.7.4",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "value_continuity_score": report.value_continuity_score,
        "meaning_continuity_score": report.meaning_continuity_score,
        "gate_pass": report.gate_pass,
        "horizons": horizons,
        "stress_scenarios": stress,
    }


def write_timeseries(path: Path) -> dict[str, Any]:
    data = run_simulations()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
