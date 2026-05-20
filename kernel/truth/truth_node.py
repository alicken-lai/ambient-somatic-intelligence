"""Truth node — auditable unit of system truth."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Mutability(str, Enum):
    """How a truth node may change over time."""

    IMMUTABLE = "immutable"
    VERSIONED = "versioned"
    MUTABLE = "mutable"


@dataclass(frozen=True)
class TruthNode:
    """
    A registered unit of truth in the graph.

    Every node requires explicit provenance — no anonymous writes.
    """

    id: str
    source: str
    owner: str
    timestamp: str
    checksum: str
    version: str
    mutability: Mutability
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("TruthNode.id is required")
        if not self.source or not self.source.strip():
            raise ValueError("TruthNode.source is required — no anonymous writes")
        if not self.owner or not self.owner.strip():
            raise ValueError("TruthNode.owner is required — no anonymous writes")
        if not self.timestamp:
            raise ValueError("TruthNode.timestamp is required")
        if not self.checksum:
            raise ValueError("TruthNode.checksum is required")
        if not self.version:
            raise ValueError("TruthNode.version is required")
        if not isinstance(self.mutability, Mutability):
            object.__setattr__(self, "mutability", Mutability(str(self.mutability)))

    @staticmethod
    def compute_checksum(payload: dict[str, Any]) -> str:
        """Deterministic SHA-256 over canonical JSON payload."""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def create(
        cls,
        *,
        node_id: str,
        source: str,
        owner: str,
        version: str,
        mutability: Mutability,
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> TruthNode:
        """Create a node with checksum derived from payload."""
        body = payload or {}
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        return cls(
            id=node_id,
            source=source,
            owner=owner,
            timestamp=ts,
            checksum=cls.compute_checksum(body),
            version=version,
            mutability=mutability,
            payload=body,
        )

    def verify_checksum(self) -> bool:
        """Return True if stored checksum matches payload."""
        return self.checksum == self.compute_checksum(self.payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "owner": self.owner,
            "timestamp": self.timestamp,
            "checksum": self.checksum,
            "version": self.version,
            "mutability": self.mutability.value,
            "payload": self.payload,
        }
