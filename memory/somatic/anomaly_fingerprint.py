"""
Anomaly Fingerprint — Unique identification and matching for anomaly patterns.

Captures the *shape* of an anomaly — which signal types fire together, at what
severity, under which environmental conditions, and with what temporal pattern —
so that recurring anomalies can be recognised across episodes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from memory.somatic.environmental_signature import EnvironmentalSignature


def _severity_band(severity: float) -> str:
    if severity < 0.25:
        return "low"
    if severity < 0.5:
        return "medium"
    if severity < 0.75:
        return "high"
    return "critical"


def _temporal_pattern(timestamps: list[float]) -> str:
    """Classify the temporal distribution of signal timestamps."""
    if len(timestamps) < 2:
        return "burst"
    ts = sorted(timestamps)
    gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
    avg_gap = sum(gaps) / len(gaps)
    span = ts[-1] - ts[0]

    if span < 5.0:
        return "burst"
    if avg_gap > 30.0:
        return "intermittent"
    return "sustained"


@dataclass
class AnomalyFingerprint:
    """Hashable identity of an anomaly pattern."""

    fingerprint_id: str = ""
    signal_pattern: str = ""
    severity_band: str = "low"
    env_context: str = ""
    temporal_pattern: str = "burst"
    occurrence_count: int = 1
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Construction ──────────────────────────────────────────────────

    @classmethod
    def from_signals(
        cls,
        signals: list[dict[str, Any]],
        env_signature: EnvironmentalSignature,
    ) -> AnomalyFingerprint:
        types = sorted({str(s.get("type", "unknown")) for s in signals})
        signal_pattern = "+".join(t.upper() for t in types)

        severities = [
            float(s.get("value", 0.0)) or (int(s.get("urgency", 1)) / 5.0)
            for s in signals
        ]
        peak = max(severities) if severities else 0.0

        timestamps = []
        for s in signals:
            ts_raw = s.get("timestamp")
            if isinstance(ts_raw, (int, float)):
                timestamps.append(float(ts_raw))
            elif isinstance(ts_raw, str):
                try:
                    dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                    timestamps.append(dt.timestamp())
                except (ValueError, TypeError):
                    pass

        env_fp = env_signature.fingerprint()
        temp = _temporal_pattern(timestamps)

        canonical = f"{signal_pattern}|{_severity_band(peak)}|{env_fp[:16]}|{temp}"
        fp_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]

        now = datetime.now(timezone.utc)
        return cls(
            fingerprint_id=fp_id,
            signal_pattern=signal_pattern,
            severity_band=_severity_band(peak),
            env_context=env_fp,
            temporal_pattern=temp,
            occurrence_count=1,
            first_seen=now,
            last_seen=now,
        )

    # ── Matching ──────────────────────────────────────────────────────

    def match(self, other: AnomalyFingerprint, tolerance: float = 0.2) -> float:
        """Similarity score 0.0–1.0 against another fingerprint."""
        score = 0.0

        # Signal pattern: Jaccard similarity
        self_types = set(self.signal_pattern.split("+"))
        other_types = set(other.signal_pattern.split("+"))
        if self_types or other_types:
            jaccard = len(self_types & other_types) / len(self_types | other_types)
            score += jaccard * 0.40

        # Severity band match
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        s_idx = severity_order.get(self.severity_band, 0)
        o_idx = severity_order.get(other.severity_band, 0)
        diff = abs(s_idx - o_idx) / 3.0
        score += (1.0 - diff) * 0.20

        # Env context: exact fingerprint prefix match
        prefix_len = max(4, int(len(self.env_context) * tolerance))
        if self.env_context[:prefix_len] == other.env_context[:prefix_len]:
            score += 0.20

        # Temporal pattern
        if self.temporal_pattern == other.temporal_pattern:
            score += 0.20

        return min(score, 1.0)

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "fingerprint_id": self.fingerprint_id,
            "signal_pattern": self.signal_pattern,
            "severity_band": self.severity_band,
            "env_context": self.env_context,
            "temporal_pattern": self.temporal_pattern,
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnomalyFingerprint:
        def _parse_dt(val: Any) -> datetime:
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass
            return datetime.now(timezone.utc)

        return cls(
            fingerprint_id=data.get("fingerprint_id", ""),
            signal_pattern=data.get("signal_pattern", ""),
            severity_band=data.get("severity_band", "low"),
            env_context=data.get("env_context", ""),
            temporal_pattern=data.get("temporal_pattern", "burst"),
            occurrence_count=int(data.get("occurrence_count", 1)),
            first_seen=_parse_dt(data.get("first_seen")),
            last_seen=_parse_dt(data.get("last_seen")),
        )
