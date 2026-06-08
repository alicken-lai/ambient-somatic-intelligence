"""
Continuity breakdown — explains session-scoped identity continuity.

Reports whether the runtime identity's continuity anchors remain chain-verified.
Read-only and descriptive: continuity here is a bounded session property, not a
claim of persistent selfhood.
"""

from __future__ import annotations

from typing import Any


class ContinuityBreakdown:
    """Describes the continuity state of a RuntimeIdentity."""

    def explain_runtime(self, runtime: Any) -> dict[str, Any]:
        anchors = list(getattr(runtime, "anchors", {}).values())
        verified = sum(1 for a in anchors if bool(getattr(a, "chain_verified", False)))
        continuity_held = all(bool(getattr(a, "chain_verified", False)) for a in anchors)

        summary = (
            f"Session '{getattr(runtime, 'session_id', 'default')}' holds "
            f"{verified}/{len(anchors)} verified anchor(s); "
            f"continuity_held={continuity_held}. Bounded session continuity, "
            "not persistent selfhood."
        )

        return {
            "advisory_only": True,
            "session_id": str(getattr(runtime, "session_id", "default")),
            "anchor_count": len(anchors),
            "verified_anchors": verified,
            "continuity_held": continuity_held,
            "summary": summary,
        }
