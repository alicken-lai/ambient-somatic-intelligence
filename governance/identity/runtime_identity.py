"""Runtime identity — session-scoped continuity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.identity.continuity_anchor import ContinuityAnchor


@dataclass
class RuntimeIdentity:
    session_id: str = "default"
    anchors: dict[str, ContinuityAnchor] = field(default_factory=dict)

    def anchor_for(self, session_id: str, signature: str) -> ContinuityAnchor:
        key = f"{session_id}:{signature[:8]}"
        if key not in self.anchors:
            self.anchors[key] = ContinuityAnchor(session_id=session_id, root_signature=signature)
        return self.anchors[key]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "anchor_count": len(self.anchors),
        }
