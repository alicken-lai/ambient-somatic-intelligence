"""
Compatibility explainer — narrates an external skill record's compatibility.

Reports the mount status and compatibility score of a mounted external skill,
including any filter notes. Advisory only; never grants the skill authority.
"""

from __future__ import annotations

from typing import Any


class CompatibilityExplainer:
    """Transparent breakdown of an external skill record's compatibility."""

    def explain_record(self, record: Any) -> dict[str, Any]:
        status_obj = getattr(record, "status", None)
        status = getattr(status_obj, "value", str(status_obj))
        skill_id = str(getattr(record, "skill_id", ""))
        name = str(getattr(record, "name", ""))
        score = float(getattr(record, "compatibility_score", 0.0))
        filter_notes = [str(n) for n in getattr(record, "filter_notes", []) or []]

        summary = (
            f"External skill '{skill_id}' status={status}, "
            f"compatibility_score={score:.4f}, {len(filter_notes)} filter note(s). "
            "Advisory mount; no sovereign authority granted."
        )

        return {
            "advisory_only": True,
            "skill_id": skill_id,
            "name": name,
            "status": status,
            "compatibility_score": round(score, 4),
            "filter_notes": filter_notes,
            "summary": summary,
        }
