"""
Precursor chain explainer — explains a chain of precursor forecast points.

Describes a sequence of :class:`PrecursorForecastPoint` items as a causal chain,
reporting its length and per-link likelihoods.  An empty chain is reported as
length zero.
"""

from __future__ import annotations

from typing import Any


class PrecursorChainExplainer:
    """Explains chains of precursor forecast points."""

    def explain_chain(self, points: list[Any]) -> dict[str, Any]:
        links = []
        for point in points:
            links.append({
                "pattern_id": getattr(point, "pattern_id", None),
                "likelihood": round(getattr(point, "likelihood", 0.0), 4),
            })
        if links:
            summary = (
                f"Precursor chain of {len(links)} link(s); "
                "each link is a probabilistic precursor, not a certainty."
            )
        else:
            summary = "No precursor chain observed."
        return {
            "chain_length": len(links),
            "links": links,
            "summary": summary,
            "opaque": False,
        }
