"""Audit sinks for provider orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Protocol


BENIGN_SECRET_MARKER_KEYS = {"prompt_tokens", "completion_tokens", "total_tokens"}
SECRET_MARKERS = ("secret", "token", "api_key", "apikey", "authorization", "credential", "password")
SECRET_VALUE_PATTERNS = (
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"(?i)\bAuthorization\s*[:=]\s*Bearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)\bAuthorization\s*[:=]\s*Basic\s+[A-Za-z0-9+/=]+"),
    re.compile(r"(?i)\bx-api-key\s*[:=]\s*[^\s,;}\]]+"),
    re.compile(r"\b[A-Za-z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD|access_key|client_secret)\s*=\s*[^\s,;}\]]+"),
    re.compile(r"(?i)\b(client_secret|access_key|[a-z0-9_]*_secret)\s*[:=]\s*[^\s,;}\]]+"),
    re.compile(r"https?://[^/\s:@]+:[^/\s@]+@"),
    re.compile(r"\bAKIA[0-9A-Z]{12,}\b"),
    re.compile(r"\b(?:ghp|gho|ghs|ghu|ghr)_[A-Za-z0-9_]{8,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{8,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\b[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b"),
    re.compile(
        r'(?i)\\"(token|password|api_key|apikey|authorization)\\"\s*:\s*\\"(?:\\\\|\\"|[^"])*\\"'
    ),
    re.compile(
        r'(?i)"(token|password|api_key|apikey|authorization)"\s*:\s*"(?:\\"|[^"])*"'
    ),
    re.compile(
        r"(?i)\b(api_key|apikey|token|password|authorization)\s*[:=]\s*(Bearer\s+)?[^\s,;}]+" 
    ),
)


class AuditSink(Protocol):
    def emit(self, event: dict[str, Any]) -> None:
        """Persist or collect one sanitized audit event."""


class NoopAuditSink:
    def emit(self, event: dict[str, Any]) -> None:
        return None


@dataclass
class MemoryAuditSink:
    events: list[dict[str, Any]]

    def emit(self, event: dict[str, Any]) -> None:
        self.events.append(sanitize_audit_event(event))


class JsonlAuditSink:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def emit(self, event: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = sanitize_audit_event(event)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_audit_event(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered not in BENIGN_SECRET_MARKER_KEYS and any(marker in lowered for marker in SECRET_MARKERS):
                continue
            clean[key] = sanitize_audit_event(item)
        return clean
    if isinstance(value, list):
        return [sanitize_audit_event(item) for item in value]
    if isinstance(value, str):
        return _redact_secret_values(value)
    return value


def _redact_secret_values(value: str) -> str:
    redacted = value
    for pattern in SECRET_VALUE_PATTERNS:
        redacted = pattern.sub(lambda match: _redact_match(match), redacted)
    return redacted


def _redact_match(match: re.Match[str]) -> str:
    if match.re.pattern.startswith('(?i)\\\\"('):
        return f'\\"{match.group(1)}\\": \\"[REDACTED]\\"'
    if match.re.pattern.startswith('(?i)"('):
        return f'"{match.group(1)}": "[REDACTED]"'
    if "https?://" in match.re.pattern:
        return re.sub(r"://[^/\s:@]+:[^/\s@]+@", "://[REDACTED]@", match.group(0))
    if "Basic" in match.re.pattern and "Authorization" in match.re.pattern:
        separator = ":" if ":" in match.group(0).split("Authorization", 1)[1][:4] else "="
        return f"Authorization{separator} Basic [REDACTED]"
    if "API_KEY|TOKEN|SECRET|PASSWORD" in match.re.pattern:
        prefix = match.group(0).split("=", 1)[0]
        return f"{prefix}= [REDACTED]"
    if "x-api-key" in match.re.pattern.lower():
        separator = ":" if ":" in match.group(0).split("x-api-key", 1)[1][:4] else "="
        return f"x-api-key{separator} [REDACTED]"
    if "Authorization" in match.re.pattern:
        separator = ":" if ":" in match.group(0).split("Authorization", 1)[1][:4] else "="
        return f"Authorization{separator} Bearer [REDACTED]"
    if match.re.pattern.startswith("(?i)\\b("):
        prefix = match.group(1)
        separator = ":" if ":" in match.group(0).split(prefix, 1)[1][:3] else "="
        return f"{prefix}{separator} [REDACTED]"
    if match.group(0).lower().startswith("bearer "):
        return "Bearer [REDACTED]"
    return "[REDACTED]"
