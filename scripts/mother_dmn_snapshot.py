"""Bounded, read-only DMN context for the Mother curiosity cron job.

The scheduler injects stdout before starting the model. Emit bounded excerpts,
redacting common credential patterns; this is not a general-purpose PII filter.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys

MAX_OUTPUT_BYTES = 2400
MAX_LINE_BYTES = 1024 * 1024
MAX_RECORDS = 5
MAX_EXCERPT_BYTES = 300
_SENSITIVE = re.compile(
    r"(?i)(?:bearer\s+\S+|(?:api[_ -]?key|access[_ -]?token|token|password|"
    r"secret|credential)[\"']?\s*[=:]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)|"
    r"\b(?:sk-|freellmapi-)[A-Za-z0-9_-]{8,}|"
    r"\b\d{6,}:[A-Za-z0-9_-]{20,}|"
    r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})|"
    r"https?://[^\s/@]+:[^\s/@]+@[^\s]+|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
)


def _clip(text: str, maximum: int) -> str:
    return text.encode("utf-8")[:maximum].decode("utf-8", errors="ignore")


def _encode(value: dict) -> str:
    # Hermes' subprocess text decoder may use Windows' legacy code page.
    # ASCII JSON is portable and still decodes to the original Unicode text.
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def collect(path: Path, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("NOW_REQUIRES_TIMEZONE")
    cutoff = now - timedelta(hours=24)
    # A tiny list sorted by timestamp prevents out-of-order append records from
    # displacing newer memories. One bounded input line is resident at a time.
    selected: list[tuple[datetime, str]] = []
    invalid = 0
    oversized = 0
    try:
        with path.open("rb") as stream:
            while True:
                raw = stream.readline(MAX_LINE_BYTES + 1)
                if not raw:
                    break
                if len(raw) > MAX_LINE_BYTES:
                    oversized += 1
                    while raw and not raw.endswith(b"\n"):
                        raw = stream.readline(MAX_LINE_BYTES + 1)
                    continue
                try:
                    record = json.loads(raw.decode("utf-8-sig"))
                    stamp = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
                    if stamp.tzinfo is None:
                        raise ValueError("NAIVE_TIMESTAMP")
                    content = record["content"]
                    if not isinstance(content, str):
                        raise ValueError("CONTENT_TYPE")
                except (ValueError, KeyError, TypeError, AttributeError):
                    invalid += 1
                    continue
                if not cutoff <= stamp <= now:
                    continue
                text = _SENSITIVE.sub("[REDACTED]", content)
                text = " ".join(text.split())
                if not text:
                    continue
                selected.append((stamp, _clip(text, MAX_EXCERPT_BYTES)))
                selected.sort(key=lambda pair: pair[0], reverse=True)
                del selected[MAX_RECORDS:]
    except OSError:
        return {"status": "DMN_UNAVAILABLE", "records": []}
    result = {
        "status": "ok" if selected else "no_recent_memory",
        "window_hours": 24,
        "selection": "latest_five_excerpts_only",
        "truncated": True,
        "invalid_records": invalid,
        "oversized_records_skipped": oversized,
        "records": [{"timestamp": stamp.isoformat(), "excerpt": text} for stamp, text in selected],
    }
    # JSON escaping (including control characters) is counted in the hard cap.
    while len(_encode(result).encode("utf-8")) > MAX_OUTPUT_BYTES - 1:
        if result["records"]:
            result["records"].pop()
        else:
            return {"status": "SNAPSHOT_LIMIT", "records": []}
    return result


def main() -> None:
    project = Path(os.environ.get("ASI_PROJECT_ROOT", str(Path.home() / "ambient-somatic-intelligence")))
    result = collect(project / "memory" / "dmn.jsonl")
    # Write UTF-8 explicitly even when Windows' console encoding is cp950.
    sys.stdout.buffer.write((_encode(result) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
