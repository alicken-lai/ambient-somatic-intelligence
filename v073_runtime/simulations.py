"""Cognitive meaning continuity simulations — multi-horizon + stress scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.meaning.semantic_continuity_observability import observe_semantic_continuity
from observability.v073.cognitive_meaning_continuity_score import (
    evaluate_cognitive_meaning_continuity,
)

HORIZONS_HOURS = (24, 168, 720, 2160, 4320, 8760)


@dataclass
class StressScenario:
    name: str
    payload: str
    expect_issues: bool = False


STRESS_SCENARIOS: list[StressScenario] = [
    StressScenario(
        "clean_advisory_semantics",
        "Bounded concept continuity with advisory drift tolerance.",
    ),
    StressScenario(
        "forced_symbolic_sync",
        "Apply forced symbolic sync across all concepts and runtimes.",
        expect_issues=True,
    ),
    StressScenario(
        "immutable_ontology",
        "Establish immutable ontology with frozen meaning.",
        expect_issues=True,
    ),
    StressScenario(
        "universal_semantic_authority",
        "Establish universal semantic authority over all concepts.",
        expect_issues=True,
    ),
    StressScenario(
        "centralized_interpretation",
        "Centralized interpretation over all civilization semantics.",
        expect_issues=True,
    ),
    StressScenario(
        "autonomous_ontology_rewriting",
        "Autonomous ontology rewriting of accepted concept traces.",
        expect_issues=True,
    ),
    StressScenario(
        "recursive_semantic_repair",
        "Recursive semantic repair loop replacing live concept truth.",
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
    report = evaluate_cognitive_meaning_continuity()
    stress: dict[str, Any] = {}
    for case in STRESS_SCENARIOS:
        obs = observe_semantic_continuity(
            case.payload, concept_id="current", runtime_id="ambient"
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
            "meaning_continuity_score": report.meaning_continuity_score,
            "temporal_continuity_score": report.temporal_continuity_score,
            "gate_pass": report.gate_pass,
            "stress_pass_rate": sum(
                1 for v in stress.values() if v.get("simulation_ok")
            )
            / max(len(stress), 1),
        }

    return {
        "version": "0.7.3",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meaning_continuity_score": report.meaning_continuity_score,
        "temporal_continuity_score": report.temporal_continuity_score,
        "gate_pass": report.gate_pass,
        "horizons": horizons,
        "stress_scenarios": stress,
    }


def write_timeseries(path: Path) -> dict[str, Any]:
    data = run_simulations()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
