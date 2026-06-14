"""Knowledge drift detection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def detect_drift(items: list[Any], *, stale_days: int = 30) -> dict[str, Any]:
    stale = []
    now = datetime.now(timezone.utc)
    for item in items:
        timestamp = getattr(item, "last_updated", None) or getattr(item, "timestamp", None)
        if not timestamp and isinstance(item, dict):
            timestamp = item.get("last_updated") or item.get("timestamp")
        if not timestamp:
            continue
        try:
            age = (now - datetime.fromisoformat(str(timestamp))).days
        except ValueError:
            continue
        if age > stale_days:
            stale.append({"item": getattr(item, "source_id", str(item)), "age_days": age})
    severity = "none" if not stale else ("high" if len(stale) > 5 else "medium")
    return {
        "drift_detected": bool(stale),
        "severity": severity,
        "stale_assets": stale,
        "recommendation": "Refresh stale evidence and re-run verification." if stale else "No drift detected.",
    }
