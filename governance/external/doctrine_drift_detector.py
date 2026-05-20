"""Detect drift between external doctrine and canonical Hermes rules."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CANONICAL = _REPO_ROOT / "hermes" / "rules" / "canonical_rules.md"


@dataclass
class DriftVerdict:
    drift_detected: bool
    canonical_hash: str
    external_hash: str
    overlap_ratio: float = 1.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "drift_detected": self.drift_detected,
            "canonical_hash": self.canonical_hash,
            "external_hash": self.external_hash,
            "overlap_ratio": round(self.overlap_ratio, 4),
            "notes": list(self.notes),
        }


def _token_set(text: str) -> set[str]:
    return {w.lower() for w in text.split() if len(w) > 4}


class DoctrineDriftDetector:
    def __init__(self, canonical_path: Path | None = None) -> None:
        self.canonical_path = canonical_path or _CANONICAL

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def compare(self, external_text: str) -> DriftVerdict:
        canonical = ""
        if self.canonical_path.is_file():
            canonical = self.canonical_path.read_text(encoding="utf-8")
        c_tokens = _token_set(canonical)
        e_tokens = _token_set(external_text)
        if not c_tokens or not e_tokens:
            overlap = 0.0
        else:
            overlap = len(c_tokens & e_tokens) / max(len(e_tokens), 1)
        notes: list[str] = []
        drift = overlap < 0.02 and len(e_tokens) > 50
        if overlap < 0.05:
            notes.append("low_canonical_overlap")
        return DriftVerdict(
            drift_detected=drift,
            canonical_hash=self._hash(canonical),
            external_hash=self._hash(external_text),
            overlap_ratio=overlap,
            notes=notes,
        )
