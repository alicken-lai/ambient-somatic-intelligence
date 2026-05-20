"""Area 1: telemetry → kernel adapter."""

from attention.runtime.telemetry_attention_signal import telemetry_to_target
from attention.runtime.telemetry_attention_adapter import TelemetryAttentionAdapter
from telemetry.core.telemetry_schema import TelemetryRecord


def test_telemetry_to_target(telemetry_adapter: TelemetryAttentionAdapter, sample_record: TelemetryRecord) -> None:
    target = telemetry_to_target(sample_record)
    assert target.source_domain in ("task", "external", "somatic", "governance", "memory")
    result = telemetry_adapter.ingest(sample_record)
    assert result["accepted"] is True


def test_duplicate_submission_blocked(telemetry_adapter: TelemetryAttentionAdapter, sample_record: TelemetryRecord) -> None:
    telemetry_adapter.ingest(sample_record)
    second = telemetry_adapter.ingest(sample_record)
    assert second["accepted"] is False
    assert second["reason"] == "duplicate_submission"
