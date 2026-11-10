"""Reports for identity, continuity, and life history."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermes.identity.belief_classification import classify_beliefs
from hermes.identity.coherence_score import compute_coherence_score
from hermes.identity.continuity_engine import analyze_continuity
from hermes.identity.identity_drift import detect_identity_drift
from hermes.identity.identity_health import compute_identity_health
from hermes.identity.identity_registry import IdentityRegistry
from hermes.identity.life_history import build_life_history
from hermes.identity.narrative_timeline import build_narrative_timeline


def build_identity_assets() -> dict[str, Any]:
    registry = IdentityRegistry()
    identity = registry.save(registry.load())
    beliefs = _load_json("reports/belief_registry.json", {})
    classifications = classify_beliefs(beliefs)
    events = build_narrative_timeline()
    continuity = analyze_continuity(identity, events, classifications)
    statements = [identity.to_dict()["identity_id"], *identity.core_principles, *identity.governance_commitments]
    statements.extend(str(item.get("statement", "")) for item in beliefs.values())
    drift = detect_identity_drift(identity, statements)
    coherence = compute_coherence_score(identity, classifications, continuity, drift)
    health = compute_identity_health(coherence=coherence, continuity=continuity, drift=drift, classifications=classifications)
    life = build_life_history(identity, events)
    return {
        "identity": identity.to_dict(),
        "belief_classifications": classifications,
        "timeline": [event.to_dict() for event in events],
        "continuity": continuity,
        "drift": drift,
        "coherence": coherence,
        "identity_health": health,
        "life_history": life,
        "governance": {
            "advisory_only": True,
            "may_modify_guardian": False,
            "may_modify_permissions": False,
            "may_execute_actions": False,
        },
    }


def generate_identity_report(output_path: str | Path = "reports/identity_report.md") -> dict[str, Any]:
    assets = build_identity_assets()
    identity = assets["identity"]
    lines = [
        "# Identity Report",
        "",
        f"Identity: `{identity['identity_id']}`",
        f"Identity Health: {assets['identity_health']['identity_health']:.2f} ({assets['identity_health']['risk']})",
        f"Coherence Score: {assets['coherence']['coherence_score']:.2f}",
        f"Identity Drift: {assets['drift']['severity']} - {assets['drift']['reason']}",
        "",
        "Identity remains advisory. Governance and Guardian remain authoritative.",
        "",
        "## Core Values",
        "",
    ]
    lines.extend(f"- {item}" for item in identity["core_values"])
    lines.extend(["", "## Non-Negotiable Constraints", ""])
    lines.extend(f"- {item}" for item in identity["non_negotiable_constraints"])
    lines.extend(["", "## Belief Classification", ""])
    for item in assets["belief_classifications"][:20]:
        lines.append(f"- {item['belief_id']}: {item['classification']} - {item['reason']}")
    return _write(output_path, lines, assets)


def generate_continuity_report(output_path: str | Path = "reports/continuity_report.md") -> dict[str, Any]:
    assets = build_identity_assets()
    continuity = assets["continuity"]
    lines = ["# Continuity Report", "", "## What Remained Stable", ""]
    lines.extend(f"- {item}" for item in continuity["stable"])
    lines.extend(["", "## What Changed", ""])
    lines.extend(f"- {item['belief_id']}: {item['classification']}" for item in continuity["changed"][:20])
    lines.extend(["", "## Why It Changed", "", continuity["why_changed"], "", "## Evidence", ""])
    lines.extend(f"- {item}" for item in continuity["evidence"][:20])
    return _write(output_path, lines, assets)


def generate_life_history_report(output_path: str | Path = "reports/life_history_report.md") -> dict[str, Any]:
    assets = build_identity_assets()
    life = assets["life_history"]
    lines = [
        "# Life History Report",
        "",
        life["biography"],
        "",
        "## Major Milestones",
        "",
    ]
    for event in life["major_milestones"][:20]:
        lines.append(f"- {event['timestamp']} / {event['event_type']}: {event['summary']}")
    lines.extend(["", "## Major Learning Events", ""])
    for event in life["major_learning_events"][:20]:
        lines.append(f"- {event['event_type']}: {event['summary']}")
    lines.extend(["", "## Major Failures", ""])
    lines.extend([f"- {event['summary']}" for event in life["major_failures"][:10]] or ["- None in current narrative timeline."])
    lines.extend(["", "## Major Recoveries", ""])
    lines.extend([f"- {event['summary']}" for event in life["major_recoveries"][:10]] or ["- None in current narrative timeline."])
    return _write(output_path, lines, assets)


def _load_json(path: str | Path, default: Any) -> Any:
    candidate = Path(path)
    if not candidate.is_file():
        return default
    return json.loads(candidate.read_text(encoding="utf-8"))


def _write(path: str | Path, lines: list[str], payload: dict[str, Any]) -> dict[str, Any]:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = output.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**payload, "report_path": str(output), "json_path": str(json_path)}
