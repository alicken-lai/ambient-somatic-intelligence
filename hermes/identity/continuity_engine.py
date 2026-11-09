"""Continuity analysis for institutional identity."""

from __future__ import annotations

from typing import Any

from hermes.identity.identity_models import IdentityProfile, NarrativeEvent


def analyze_continuity(identity: IdentityProfile, events: list[NarrativeEvent], classifications: list[dict[str, Any]]) -> dict[str, Any]:
    stable = [*identity.core_values, *identity.governance_commitments, *identity.non_negotiable_constraints]
    changed = [item for item in classifications if item["classification"] in {"Experimental Belief", "Retired Belief"}]
    evidence = sorted({source for event in events for source in event.evidence})
    return {
        "stable": stable,
        "changed": changed,
        "why_changed": "belief classifications change when confidence, reality score, or retirement status changes",
        "evidence": evidence,
        "continuity_metrics": {
            "stable_commitment_count": len(stable),
            "change_count": len(changed),
            "event_count": len(events),
        },
    }
