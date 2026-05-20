"""Treaty record — declarative inter-sovereign agreements (advisory, non-binding)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class TreatyRecord:
    """Read-only treaty metadata — never merges identity or overrides Guardian."""

    treaty_id: str
    sovereign_a: str
    sovereign_b: str
    scope: str = "advisory_interop"
    non_interference: bool = True
    guardian_supremacy: bool = True
    constitutional_aligned: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    expires_at: str | None = None
    clauses: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        sovereign_a: str,
        sovereign_b: str,
        *,
        scope: str = "advisory_interop",
        clauses: list[str] | None = None,
    ) -> TreatyRecord:
        return cls(
            treaty_id=f"treaty-{uuid4().hex[:12]}",
            sovereign_a=sovereign_a,
            sovereign_b=sovereign_b,
            scope=scope,
            clauses=list(clauses or ["no_cognition_merge", "guardian_supremacy"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "treaty_id": self.treaty_id,
            "sovereign_a": self.sovereign_a,
            "sovereign_b": self.sovereign_b,
            "scope": self.scope,
            "non_interference": self.non_interference,
            "guardian_supremacy": self.guardian_supremacy,
            "constitutional_aligned": self.constitutional_aligned,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "clauses": list(self.clauses),
        }
