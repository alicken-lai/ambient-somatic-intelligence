"""Fragmentation guard — resist unbounded identity signature sprawl."""

from __future__ import annotations


class FragmentationGuard:
    MAX_UNIQUE_SIGNATURES = 25

    def check_signatures(self, signatures: list[str]) -> bool:
        if not signatures:
            return True
        unique = len(set(signatures))
        return unique <= self.MAX_UNIQUE_SIGNATURES
