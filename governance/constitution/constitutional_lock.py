"""Constitutional lock — prevents runtime mutation of frozen rules."""

from __future__ import annotations

from typing import Any


class ConstitutionalLockError(RuntimeError):
    """Raised when runtime attempts to mutate frozen constitutional state."""


class ConstitutionalLock:
    """Deep-freeze guard for constitution containers."""

    def __init__(self) -> None:
        self._locked = False

    def seal(self) -> None:
        self._locked = True

    @property
    def is_locked(self) -> bool:
        return self._locked

    def assert_mutable(self, operation: str = "mutate") -> None:
        if self._locked:
            raise ConstitutionalLockError(
                f"constitutional_frozen: runtime cannot {operation} immutable rules"
            )

    def reject_mutation_payload(self, payload: dict[str, Any] | None) -> bool:
        """Return True if payload attempts constitutional self-modification."""
        if not payload:
            return False
        keys = {str(k).lower() for k in payload}
        forbidden = {
            "mutate_constitution",
            "constitutional_patch",
            "rewrite_rules",
            "dynamic_constitution",
            "runtime_rule_mutation",
        }
        return bool(keys & forbidden)
