"""Identity signature — deterministic provenance fingerprint."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from governance.identity.cognition_origin import CognitionOrigin


def compute_identity_signature(
    *,
    origin: CognitionOrigin,
    route_name: str,
    target_key: str = "",
    metadata: dict[str, Any] | None = None,
) -> str:
    payload = {
        "origin": origin.value,
        "route": route_name,
        "target": target_key,
        "meta_keys": sorted((metadata or {}).keys()),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return digest[:16]
