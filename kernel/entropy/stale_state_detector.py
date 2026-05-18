"""Stale state detector — system_state, DMN, truth graph, bus log recency."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kernel.entropy.entropy_metric import EntropyMetric, MetricKind
from kernel.truth.truth_graph import TruthGraph


@dataclass
class StaleStateFinding:
    source: str
    severity: str  # ok | warning | critical
    age_seconds: float
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "severity": self.severity,
            "age_seconds": round(self.age_seconds, 1),
            "detail": self.detail,
        }


@dataclass
class StaleStateReport:
    findings: list[StaleStateFinding] = field(default_factory=list)
    critical_count: int = 0
    pressure_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "critical_count": self.critical_count,
            "pressure_score": round(self.pressure_score, 4),
            "findings": [f.to_dict() for f in self.findings],
        }


class StaleStateDetector:
    """
    Compares authoritative state artifacts for temporal drift.

    Read-only file access — never rewrites system_state or DMN.
    """

    CRITICAL_AGE_SECONDS = 172_800  # 48h
    WARNING_AGE_SECONDS = 86_400  # 24h

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(__file__).resolve().parents[2]

    def observe(
        self,
        truth_graph: TruthGraph | None = None,
        bus_event_log: list[Any] | None = None,
    ) -> list[EntropyMetric]:
        report = self.scan(truth_graph, bus_event_log)
        return [
            EntropyMetric(
                name="stale_state_pressure",
                kind=MetricKind.STALE,
                value=report.pressure_score,
                weight=1.2,
                source="kernel.entropy.stale_state_detector",
                detail=f"{report.critical_count} critical stale sources",
                metadata=report.to_dict(),
            ),
            EntropyMetric(
                name="stale_state_critical",
                kind=MetricKind.STALE,
                value=min(1.0, report.critical_count),
                weight=1.5,
                source="kernel.entropy.stale_state_detector",
                detail="binary critical stale indicator",
            ),
        ]

    def scan(
        self,
        truth_graph: TruthGraph | None = None,
        bus_event_log: list[Any] | None = None,
    ) -> StaleStateReport:
        findings: list[StaleStateFinding] = []
        now = datetime.now(timezone.utc)

        findings.append(self._check_json_timestamp(
            self._root / "state" / "system_state.json",
            "system_state.json",
            now,
        ))
        findings.append(self._check_jsonl_tail(
            self._root / "memory" / "dmn.jsonl",
            "dmn.jsonl",
            now,
        ))

        if truth_graph is not None:
            stale = truth_graph.stale_sources()
            severity = "critical" if stale else "ok"
            findings.append(
                StaleStateFinding(
                    source="truth_graph",
                    severity=severity,
                    age_seconds=float(len(stale)),
                    detail=f"{len(stale)} stale truth nodes",
                )
            )

        if bus_event_log:
            last_ts = self._last_bus_timestamp(bus_event_log)
            if last_ts is not None:
                age = (now - last_ts).total_seconds()
                findings.append(
                    StaleStateFinding(
                        source="integration_bus",
                        severity=self._severity_for_age(age),
                        age_seconds=age,
                        detail="last bus event age",
                    )
                )

        critical = sum(1 for f in findings if f.severity == "critical")
        warning = sum(1 for f in findings if f.severity == "warning")
        pressure = min(1.0, critical * 0.5 + warning * 0.15)

        return StaleStateReport(
            findings=findings,
            critical_count=critical,
            pressure_score=pressure,
        )

    def _check_json_timestamp(
        self,
        path: Path,
        label: str,
        now: datetime,
    ) -> StaleStateFinding:
        if not path.is_file():
            return StaleStateFinding(label, "critical", 0.0, "missing file")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            ts_str = data.get("updated_at") or data.get("timestamp") or ""
            if not ts_str:
                return StaleStateFinding(label, "warning", 0.0, "no timestamp field")
            ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age = (now - ts).total_seconds()
            return StaleStateFinding(
                label,
                self._severity_for_age(age),
                age,
                f"last update {ts_str}",
            )
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            return StaleStateFinding(label, "warning", 0.0, str(exc))

    def _check_jsonl_tail(
        self,
        path: Path,
        label: str,
        now: datetime,
    ) -> StaleStateFinding:
        if not path.is_file():
            return StaleStateFinding(label, "critical", 0.0, "missing file")

        try:
            last_line = ""
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        last_line = line
            if not last_line:
                return StaleStateFinding(label, "warning", 0.0, "empty jsonl")
            record = json.loads(last_line)
            ts_str = record.get("timestamp") or record.get("ts") or ""
            if not ts_str:
                return StaleStateFinding(label, "warning", 0.0, "no timestamp in last record")
            ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age = (now - ts).total_seconds()
            return StaleStateFinding(
                label,
                self._severity_for_age(age),
                age,
                "last dmn append",
            )
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            return StaleStateFinding(label, "warning", 0.0, str(exc))

    def _last_bus_timestamp(self, event_log: list[Any]) -> datetime | None:
        if not event_log:
            return None
        event = event_log[-1]
        ts_val = getattr(event, "timestamp", None)
        if ts_val is None and isinstance(event, dict):
            ts_val = event.get("timestamp")
        if ts_val is None:
            return None
        try:
            if isinstance(ts_val, (int, float)):
                return datetime.fromtimestamp(ts_val, tz=timezone.utc)
            ts = datetime.fromisoformat(str(ts_val).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts
        except ValueError:
            return None

    def _severity_for_age(self, age_seconds: float) -> str:
        if age_seconds >= self.CRITICAL_AGE_SECONDS:
            return "critical"
        if age_seconds >= self.WARNING_AGE_SECONDS:
            return "warning"
        return "ok"
