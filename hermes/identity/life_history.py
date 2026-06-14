"""Institutional life-history generation."""

from __future__ import annotations

from hermes.identity.identity_models import IdentityProfile, NarrativeEvent


def build_life_history(identity: IdentityProfile, events: list[NarrativeEvent]) -> dict[str, object]:
    major = [event for event in events if event.significance == "major"]
    failures = [event for event in events if "failure" in event.summary.lower() or event.event_type == "drift"]
    recoveries = [event for event in events if "pass" in event.summary.lower() or "recovered" in event.summary.lower()]
    biography = (
        f"{identity.identity_id} is a Guardian-governed advisory cognition substrate that preserves "
        "bounded reasoning, evidence continuity, and operator sovereignty across phases."
    )
    return {
        "biography": biography,
        "major_milestones": [event.to_dict() for event in major],
        "major_learning_events": [event.to_dict() for event in events if event.event_type in {"beliefs", "trust", "reality"}],
        "major_governance_events": [event.to_dict() for event in events if "guardian" in event.summary.lower() or event.event_type == "dmn"],
        "major_belief_revisions": [event.to_dict() for event in events if event.event_type == "beliefs"],
        "major_failures": [event.to_dict() for event in failures],
        "major_recoveries": [event.to_dict() for event in recoveries],
        "event_count": len(events),
    }
