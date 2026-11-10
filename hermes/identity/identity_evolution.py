"""Identity evolution audit helpers."""

from __future__ import annotations

from hermes.identity.identity_models import IdentityChange


def validate_identity_change(change: IdentityChange) -> dict[str, object]:
    ok = bool(change.justification.strip()) and bool(change.evidence)
    return {
        "change_id": change.change_id,
        "accepted_for_review": ok,
        "reason": "justified with evidence" if ok else "identity changes require explicit justification and evidence",
    }


def summarize_identity_evolution(changes: list[IdentityChange]) -> dict[str, object]:
    reviews = [validate_identity_change(change) for change in changes]
    return {
        "change_count": len(changes),
        "accepted_for_review": sum(1 for item in reviews if item["accepted_for_review"]),
        "reviews": reviews,
        "silent_evolution_allowed": False,
    }
