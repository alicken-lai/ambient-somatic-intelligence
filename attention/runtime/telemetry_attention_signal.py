"""
Telemetry-to-attention signal mapping.

Converts a :class:`TelemetryRecord` into a domain-agnostic
:class:`AttentionTarget`.  The telemetry *category* selects the attention
source domain, while the payload supplies the salience value and signal type.
A stable ``source_ref`` is derived so the adapter can detect duplicate
submissions of the same record.
"""

from __future__ import annotations

from attention.core.attention_target import AttentionTarget
from telemetry.core.telemetry_schema import TelemetryRecord

# Telemetry categories -> attention source domains (all in the kernel's
# accepted domain set: task / external / somatic / governance / memory).
_CATEGORY_DOMAIN: dict[str, str] = {
    "somatic": "somatic",
    "governance": "governance",
    "episodic": "memory",
    "semantic": "memory",
    "procedural": "memory",
    "reflex": "memory",
    "checkpoint": "memory",
    "incident": "external",
    "health": "external",
    "metric": "external",
    "state": "external",
    "action": "task",
    "attention": "task",
}


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def telemetry_to_target(record: TelemetryRecord) -> AttentionTarget:
    """Map *record* into an :class:`AttentionTarget`."""
    domain = _CATEGORY_DOMAIN.get(record.category, "task")
    payload = record.payload or {}
    raw_value = _clamp_unit(payload.get("salience", record.confidence))
    signal_type = str(payload.get("signal_type", record.category))
    source_ref = f"{record.source}|{record.timestamp}|{signal_type}"
    metadata = {
        "telemetry_category": record.category,
        "telemetry_confidence": record.confidence,
        "urgency": raw_value,
    }
    return AttentionTarget(
        source_domain=domain,
        signal_type=signal_type,
        raw_value=raw_value,
        metadata=metadata,
        source_ref=source_ref,
    )
