"""
Escalation salience — maps Guardian risk levels to a salience boost.

Higher-risk Guardian verdicts contribute more salience so governance concerns
rise in the attention queue.  ``ALLOW`` contributes nothing; ``BLOCK`` is the
most salient.
"""

from __future__ import annotations

_ESCALATION_BOOST: dict[str, float] = {
    "BLOCK": 0.9,
    "REVIEW_REQUIRED": 0.5,
    "ALLOW": 0.0,
}


def escalation_boost(risk: str) -> float:
    """Return the salience boost for a Guardian *risk* verdict (``[0, 1]``)."""
    return _ESCALATION_BOOST.get(str(risk).upper(), 0.0)
