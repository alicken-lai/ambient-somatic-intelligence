"""Trace persistence for ASI deliberation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re
from typing import Any


SECRET_KEY_RE = re.compile(r"(api[_-]?key|token|secret|password|credential|authorization)", re.IGNORECASE)
SECRET_VALUE_RE = re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/=-]+", re.IGNORECASE)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if SECRET_KEY_RE.search(str(key)) else redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return SECRET_VALUE_RE.sub(r"\1[REDACTED]", value)
    return value


def save_trace(trace: dict[str, Any], *, trace_dir: str | Path = "logs/deliberation") -> Path:
    safe_trace = redact(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **trace,
        }
    )
    path = Path(trace_dir)
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{safe_trace['trace_id']}.json"
    file_path.write_text(json.dumps(safe_trace, indent=2, ensure_ascii=False), encoding="utf-8")
    return file_path
