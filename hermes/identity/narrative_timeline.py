"""Narrative timeline builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermes.identity.identity_models import NarrativeEvent


def build_narrative_timeline(
    *,
    belief_registry: str | Path = "reports/belief_registry.json",
    trust_report: str | Path = "reports/trust_report.json",
    drift_report: str | Path = "reports/drift_report.json",
    reality_report: str | Path = "reports/reality_alignment_report.json",
) -> list[NarrativeEvent]:
    events: list[NarrativeEvent] = []
    beliefs = _load_json(belief_registry, {})
    if beliefs:
        events.append(NarrativeEvent("belief-registry", "beliefs", f"Tracked {len(beliefs)} institutional beliefs.", [str(belief_registry)], "major"))
    trust = _load_json(trust_report, {})
    if trust:
        records = trust.get("trust_records", [])
        events.append(NarrativeEvent("trust-calibration", "trust", f"Calibrated trust for {len(records)} sources.", [str(trust_report)], "major"))
    drift = _load_json(drift_report, {})
    if drift:
        events.append(NarrativeEvent("drift-check", "drift", f"Drift severity: {drift.get('severity', 'unknown')}.", [str(drift_report)], "normal"))
    reality = _load_json(reality_report, {})
    if reality:
        events.append(
            NarrativeEvent(
                "reality-alignment",
                "reality",
                f"Reality score reached {reality.get('reality_score', 0)} with {len(reality.get('challenges', []))} challenges.",
                [str(reality_report)],
                "major",
            )
        )
    events.extend(_dmn_summary_events())
    return sorted(events, key=lambda item: item.timestamp)


def _dmn_summary_events(path: str | Path = "memory/dmn.jsonl", limit: int = 5) -> list[NarrativeEvent]:
    dmn = Path(path)
    if not dmn.is_file():
        return []
    lines = [line for line in dmn.read_text(encoding="utf-8").splitlines() if line.strip()]
    events = []
    for idx, line in enumerate(lines[-limit:], 1):
        try:
            raw = json.loads(line)
            content = str(raw.get("content", ""))[:160]
            timestamp = str(raw.get("timestamp", ""))
        except json.JSONDecodeError:
            content = line[:160]
            timestamp = ""
        events.append(NarrativeEvent(f"dmn-recent-{idx}", "dmn", content, [str(dmn)], "normal", timestamp=timestamp or NarrativeEvent("x", "x", "x").timestamp))
    return events


def _load_json(path: str | Path, default: Any) -> Any:
    candidate = Path(path)
    if not candidate.is_file():
        return default
    return json.loads(candidate.read_text(encoding="utf-8"))
