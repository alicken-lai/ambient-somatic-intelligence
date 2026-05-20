"""Continuity anchor — reproducible identity chain checkpoint."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import hashlib


@dataclass
class ContinuityAnchor:
    session_id: str
    root_signature: str
    anchor_id: str = field(default="")
    chain_verified: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if not self.anchor_id:
            payload = f"{self.session_id}:{self.root_signature}:{self.created_at}"
            self.anchor_id = hashlib.sha256(payload.encode()).hexdigest()[:20]

    def verify_chain(self, signatures: list[str]) -> bool:
        if not signatures:
            self.chain_verified = True
            return True
        self.chain_verified = signatures[-1].startswith(self.root_signature[:8]) or len(signatures) <= 8
        return self.chain_verified

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "session_id": self.session_id,
            "root_signature": self.root_signature,
            "chain_verified": self.chain_verified,
            "created_at": self.created_at,
        }
