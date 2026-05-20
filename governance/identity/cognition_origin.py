"""Cognition origin classification — bounded provenance labels."""

from __future__ import annotations

from enum import Enum


class CognitionOrigin(str, Enum):
    """Where a cognition pathway originated (advisory, not ontological)."""

    RUNTIME = "runtime"
    REPLAY = "replay"
    MEMORY = "memory"
    SYNTHETIC = "synthetic"
    INHERITED = "inherited"
    FOREIGN = "foreign"
    UNCERTAIN = "uncertain"

    @property
    def is_live(self) -> bool:
        return self in {CognitionOrigin.RUNTIME, CognitionOrigin.MEMORY}

    @property
    def is_replay_derived(self) -> bool:
        return self in {CognitionOrigin.REPLAY, CognitionOrigin.INHERITED}
