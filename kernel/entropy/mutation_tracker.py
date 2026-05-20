"""Mutation tracker — observes state mutation attempts without applying them."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from kernel.entropy.entropy_metric import EntropyMetric, MetricKind


@dataclass
class MutationRecord:
    """Recorded observation of a mutation attempt."""

    target: str
    caller: str
    scope: str
    allowed: bool
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    reason: str = ""


class MutationTracker:
    """
    Tracks mutation pressure across execution contexts.

    No silent mutation: every record is explicit and auditable.
    Observable hooks record globals, singletons, callbacks, and registry ops.
    """

    def __init__(self, window_size: int = 500) -> None:
        self._records: list[MutationRecord] = []
        self._window_size = window_size
        self._global_mutations: int = 0
        self._singleton_rewrites: int = 0
        self._callback_growth: int = 0
        self._registry_mutations: int = 0

    @property
    def records(self) -> list[MutationRecord]:
        return list(self._records)

    def observe_global_mutation(self, name: str, caller: str = "unknown") -> None:
        self._global_mutations += 1
        self.observe_attempt(f"global:{name}", caller, "global", allowed=False, reason="mutable_global")

    def observe_singleton_rewrite(self, name: str, caller: str = "unknown") -> None:
        self._singleton_rewrites += 1
        self.observe_attempt(f"singleton:{name}", caller, "singleton", allowed=False, reason="singleton_rewrite")

    def observe_callback_growth(self, count: int = 1) -> None:
        self._callback_growth += count

    def observe_registry_mutation(self, registry: str, operation: str, caller: str = "unknown") -> None:
        self._registry_mutations += 1
        self.observe_attempt(f"registry:{registry}", caller, operation, allowed=True, reason="registry_mutation")

    def observe_attempt(
        self,
        target: str,
        caller: str,
        scope: str,
        allowed: bool,
        reason: str = "",
    ) -> MutationRecord:
        record = MutationRecord(
            target=target,
            caller=caller,
            scope=scope,
            allowed=allowed,
            reason=reason,
        )
        self._records.append(record)
        if len(self._records) > self._window_size:
            self._records = self._records[-self._window_size:]
        return record

    def observe(self) -> list[EntropyMetric]:
        """Derive mutation-pressure metrics from recent records."""
        if not self._records:
            return [
                EntropyMetric(
                    name="mutation_rate",
                    kind=MetricKind.MUTATION,
                    value=0.0,
                    source="kernel.entropy.mutation_tracker",
                    detail="no mutation attempts recorded",
                )
            ]

        denied = [r for r in self._records if not r.allowed]
        denied_ratio = len(denied) / len(self._records)
        recent_window = self._records[-50:]
        recent_denied = sum(1 for r in recent_window if not r.allowed)
        recent_pressure = recent_denied / max(len(recent_window), 1)

        hook_pressure = min(
            1.0,
            (self._global_mutations + self._singleton_rewrites) / 10.0
            + self._callback_growth / 50.0
            + self._registry_mutations / 30.0,
        )

        return [
            EntropyMetric(
                name="mutation_denial_rate",
                kind=MetricKind.MUTATION,
                value=min(1.0, denied_ratio),
                weight=1.2,
                source="kernel.entropy.mutation_tracker",
                detail=f"{len(denied)}/{len(self._records)} denied",
            ),
            EntropyMetric(
                name="mutation_recent_pressure",
                kind=MetricKind.MUTATION,
                value=min(1.0, recent_pressure),
                weight=1.0,
                source="kernel.entropy.mutation_tracker",
                detail=f"{recent_denied} denied in last {len(recent_window)} attempts",
            ),
            EntropyMetric(
                name="mutation_hook_pressure",
                kind=MetricKind.MUTATION,
                value=hook_pressure,
                weight=1.0,
                source="kernel.entropy.mutation_tracker",
                detail=(
                    f"globals={self._global_mutations} singletons={self._singleton_rewrites} "
                    f"callbacks={self._callback_growth} registry={self._registry_mutations}"
                ),
            ),
        ]

    def stats(self) -> dict[str, Any]:
        return {
            "total_records": len(self._records),
            "denied": sum(1 for r in self._records if not r.allowed),
            "allowed": sum(1 for r in self._records if r.allowed),
            "global_mutations": self._global_mutations,
            "singleton_rewrites": self._singleton_rewrites,
            "callback_growth": self._callback_growth,
            "registry_mutations": self._registry_mutations,
        }
