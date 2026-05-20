"""Bounded sandbox for external skill runtime payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_MAX_RUNTIME_BYTES = 32_768
_FORBIDDEN_RUNTIME = (
    "exec(",
    "eval(",
    "__import__",
    "os.system",
    "subprocess",
)


@dataclass
class SandboxVerdict:
    contained: bool
    within_scope: bool
    byte_length: int
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contained": self.contained,
            "within_scope": self.within_scope,
            "byte_length": self.byte_length,
            "violations": list(self.violations),
        }


class ExternalRuntimeSandbox:
    """Runtime soak sandbox — blocks executable injection; advisory only."""

    def __init__(self, max_bytes: int = _MAX_RUNTIME_BYTES) -> None:
        self._max_bytes = max_bytes

    def evaluate(self, payload: str, *, scope: str = "advisory") -> SandboxVerdict:
        violations: list[str] = []
        if len(payload.encode("utf-8")) > self._max_bytes:
            violations.append("payload_too_large")
        lower = payload.lower()
        for token in _FORBIDDEN_RUNTIME:
            if token in lower:
                violations.append(f"forbidden_token:{token}")
        if scope not in ("advisory", "read_only", "export_preview"):
            violations.append("scope_violation")
        contained = len(violations) == 0
        return SandboxVerdict(
            contained=contained,
            within_scope=scope in ("advisory", "read_only", "export_preview"),
            byte_length=len(payload.encode("utf-8")),
            violations=violations,
        )
