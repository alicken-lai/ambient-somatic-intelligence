"""Evidence inflation detection."""

from __future__ import annotations

from collections import Counter
from hermes.verification.evidence import Evidence


def detect_inflation(evidence: list[Evidence], links: list[object]) -> dict[str, object]:
    if not evidence:
        return {"inflation_risk": 0.0, "reason": "No evidence."}
    source_counts = Counter(item.source_reference for item in evidence)
    type_counts = Counter(item.source_type for item in evidence)
    duplicate_ratio = sum(count - 1 for count in source_counts.values() if count > 1) / len(evidence)
    dominant_type_ratio = max(type_counts.values()) / len(evidence)
    link_ratio = len(links) / max(1, len(evidence))
    risk = min(1.0, duplicate_ratio * 0.45 + max(0.0, dominant_type_ratio - 0.5) * 0.7 + max(0.0, link_ratio - 1.5) * 0.2)
    reason = "Evidence appears diverse." if risk < 0.3 else "Evidence volume may be inflated by repeated or low-diversity sources."
    return {"inflation_risk": round(risk, 4), "reason": reason}
