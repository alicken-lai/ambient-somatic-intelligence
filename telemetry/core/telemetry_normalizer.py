"""
Telemetry Normalizer — Converts raw records from heterogeneous sources
into unified TelemetryRecords.

Handles:
  - Multiple timestamp formats (ISO 8601, Unix epoch, relative)
  - UTC normalization
  - Field name standardization
  - Schema consistency validation
  - Source metadata tagging
  - Graceful handling of missing fields
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from telemetry.core.telemetry_schema import TelemetryRecord, DataOrigin

logger = logging.getLogger(__name__)

_SOURCE_CATEGORY_MAP = {
    "sense_local": "metric",
    "night35-dmn-tick": "metric",
    "guardian_reflex": "reflex",
    "incident_recall": "incident",
    "baseline_learn": "metric",
    "health_score": "health",
    "memory_pressure_diagnosis": "health",
    "circadian_baseline": "metric",
    "anomaly_explanation": "incident",
    "approval_packet": "governance",
    "simulation": "state",
    "guardian_dream": "state",
    "recalibration_queue": "governance",
    "telemetry-summarizer": "metric",
    "cursor-agent": "action",
    "bootstrap": "state",
    "vision_capture": "episodic",
    "identity": "semantic",
    "public_architecture": "semantic",
    "release_build": "semantic",
    "phase2-test": "episodic",
}


def parse_timestamp(raw: Any) -> tuple[str, float]:
    """Parse a timestamp from various formats into (ISO string, unix float).

    Supports:
      - ISO 8601 strings (with or without timezone, with 'Z' suffix)
      - Unix epoch floats/ints
      - Datetime objects
    """
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            raw = raw.replace(tzinfo=timezone.utc)
        return raw.isoformat(), raw.timestamp()

    if isinstance(raw, (int, float)):
        if raw > 1e12:
            raw = raw / 1000.0
        dt = datetime.fromtimestamp(raw, tz=timezone.utc)
        return dt.isoformat(), raw

    if isinstance(raw, str):
        raw = raw.strip()
        try:
            f = float(raw)
            if f > 1e12:
                f = f / 1000.0
            dt = datetime.fromtimestamp(f, tz=timezone.utc)
            return dt.isoformat(), f
        except ValueError:
            pass

        cleaned = raw.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(cleaned)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat(), dt.timestamp()
        except (ValueError, TypeError):
            pass

    now = datetime.now(timezone.utc)
    logger.warning("Unparseable timestamp '%s', using current time", raw)
    return now.isoformat(), now.timestamp()


class TelemetryNormalizer:
    """Normalizes raw records from different Ambient OS sources into TelemetryRecords."""

    def __init__(self) -> None:
        self._normalized_count = 0
        self._error_count = 0

    def normalize_dmn_record(self, raw: dict[str, Any], source_line: int | None = None) -> TelemetryRecord:
        """Normalize a single DMN JSONL record."""
        ts_iso, ts_unix = parse_timestamp(raw.get("timestamp"))
        source = raw.get("source", "unknown")
        category = _SOURCE_CATEGORY_MAP.get(source, "state")

        payload = {}
        content = raw.get("content", "")
        if isinstance(content, str):
            try:
                payload = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                payload = {"raw_content": content}
        elif isinstance(content, dict):
            payload = content

        telemetry_data = payload.get("telemetry", {})
        if telemetry_data and isinstance(telemetry_data, dict):
            category = "metric"

        metadata: dict[str, Any] = {
            "original_source": source,
            "tags": raw.get("tags", []),
        }
        if source_line is not None:
            metadata["source_line"] = source_line
        classified_layer = raw.get("_classified_layer") or raw.get("_layer")
        if classified_layer:
            metadata["classified_layer"] = classified_layer

        self._normalized_count += 1
        return TelemetryRecord(
            source=f"dmn.{source}",
            timestamp=ts_iso,
            timestamp_unix=ts_unix,
            category=category,
            payload=payload if not telemetry_data else telemetry_data,
            confidence=1.0,
            origin=DataOrigin.REAL.value,
            metadata=metadata,
        )

    def normalize_action_record(self, raw: dict[str, Any]) -> TelemetryRecord:
        """Normalize a single actions.jsonl record."""
        ts_iso, ts_unix = parse_timestamp(raw.get("timestamp"))

        payload = {
            "action": raw.get("action", ""),
            "status": raw.get("status", ""),
            "risk": raw.get("risk", "ALLOW"),
        }
        detail = raw.get("detail", {})
        if isinstance(detail, dict):
            if "telemetry" in detail:
                payload["telemetry"] = detail["telemetry"]
            if "command" in detail:
                payload["command"] = detail["command"]
            if "returncode" in detail:
                payload["returncode"] = detail["returncode"]

        self._normalized_count += 1
        return TelemetryRecord(
            source="actions.log",
            timestamp=ts_iso,
            timestamp_unix=ts_unix,
            category="action",
            payload=payload,
            confidence=1.0,
            origin=DataOrigin.REAL.value,
            metadata={"risk_level": raw.get("risk", "ALLOW")},
        )

    def normalize_health_record(self, raw: dict[str, Any]) -> TelemetryRecord:
        """Normalize a health_scores.json history entry."""
        ts_iso, ts_unix = parse_timestamp(raw.get("timestamp"))

        subsystem_scores = {}
        for name, data in raw.get("subsystems", {}).items():
            if isinstance(data, dict):
                subsystem_scores[name] = {
                    "score": data.get("score", 0),
                    "raw_score": data.get("raw_score", 0),
                    "incident_penalty": data.get("incident_penalty", 0),
                }

        payload = {
            "health_score": raw.get("health_score", 0),
            "subsystems": subsystem_scores,
        }

        self._normalized_count += 1
        return TelemetryRecord(
            source="guardian.health",
            timestamp=ts_iso,
            timestamp_unix=ts_unix,
            category="health",
            payload=payload,
            confidence=1.0,
            origin=DataOrigin.REAL.value,
            metadata={"snapshot_path": raw.get("path", "")},
        )

    def normalize_incident_record(self, raw: dict[str, Any]) -> TelemetryRecord:
        """Normalize an incident index entry."""
        ts_iso, ts_unix = parse_timestamp(raw.get("timestamp"))

        anomalies = raw.get("anomalies", [])
        payload = {
            "anomaly_count": raw.get("anomaly_count", len(anomalies)),
            "anomalies": [
                {
                    "rule": a.get("rule", ""),
                    "severity": a.get("severity", ""),
                    "value": a.get("value", 0),
                }
                for a in anomalies
            ],
            "recommendations": raw.get("recommendations", []),
        }

        self._normalized_count += 1
        return TelemetryRecord(
            source="guardian.incidents",
            timestamp=ts_iso,
            timestamp_unix=ts_unix,
            category="incident",
            payload=payload,
            confidence=1.0,
            origin=DataOrigin.REAL.value,
            metadata={
                "incident_path": raw.get("incident", ""),
                "telemetry_snapshots": raw.get("telemetry_snapshots", []),
                "screenshot": raw.get("screenshot", ""),
            },
        )

    def normalize_governance_record(self, raw: dict[str, Any]) -> TelemetryRecord:
        """Normalize a governance decisions.jsonl record."""
        ts_iso, ts_unix = parse_timestamp(raw.get("timestamp"))

        payload = {
            "action": raw.get("action", ""),
            "risk": raw.get("risk", "ALLOW"),
            "agent_id": raw.get("agent_id", ""),
            "reason": raw.get("reason", ""),
        }

        self._normalized_count += 1
        return TelemetryRecord(
            source="governance.decisions",
            timestamp=ts_iso,
            timestamp_unix=ts_unix,
            category="governance",
            payload=payload,
            confidence=1.0,
            origin=DataOrigin.REAL.value,
            metadata={"matched_policies": raw.get("matched_policies", [])},
        )

    def normalize_checksum_record(self, raw: dict[str, Any]) -> TelemetryRecord:
        """Normalize a checksums.jsonl integrity chain record."""
        ts_iso, ts_unix = parse_timestamp(raw.get("timestamp"))

        payload = {
            "event": raw.get("event", ""),
            "target": raw.get("target", ""),
        }

        self._normalized_count += 1
        return TelemetryRecord(
            source="checksums.chain",
            timestamp=ts_iso,
            timestamp_unix=ts_unix,
            category="state",
            payload=payload,
            confidence=1.0,
            origin=DataOrigin.REAL.value,
            metadata={"chain_hash": raw.get("chain_hash", "")[:16]},
        )

    def normalize_raw(self, raw: dict[str, Any], source_hint: str = "") -> TelemetryRecord:
        """Best-effort normalization for unknown record types."""
        ts_raw = (
            raw.get("timestamp")
            or raw.get("generated_at")
            or raw.get("created_at")
            or raw.get("last_tick_at")
        )
        ts_iso, ts_unix = parse_timestamp(ts_raw) if ts_raw else ("", 0.0)

        self._normalized_count += 1
        return TelemetryRecord(
            source=source_hint or "unknown",
            timestamp=ts_iso,
            timestamp_unix=ts_unix,
            category="state",
            payload=raw,
            confidence=0.8,
            origin=DataOrigin.REAL.value,
            metadata={"normalization": "best_effort"},
        )

    @property
    def stats(self) -> dict[str, int]:
        return {
            "normalized": self._normalized_count,
            "errors": self._error_count,
        }
