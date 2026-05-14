"""
Environmental Signature — Fingerprint for system environment states.

Quantizes raw metrics (CPU, memory, disk, load, process count) into
categorical bands and a composite numeric vector, enabling:
  - Fast fingerprint comparison via SHA-256 hash of bands
  - Continuous distance calculation via normalized vector
  - Similarity gating for episode matching
"""

from __future__ import annotations

import hashlib
import math
import os
from dataclasses import dataclass, field
from typing import Any


_CPU_BANDS = [
    (10.0, "idle"),
    (30.0, "light"),
    (60.0, "moderate"),
    (85.0, "heavy"),
    (float("inf"), "saturated"),
]

_MEMORY_BANDS = [
    (30.0, "idle"),
    (50.0, "light"),
    (70.0, "moderate"),
    (85.0, "heavy"),
    (float("inf"), "saturated"),
]

_DISK_BANDS = [
    (40.0, "idle"),
    (60.0, "light"),
    (75.0, "moderate"),
    (90.0, "heavy"),
    (float("inf"), "saturated"),
]

_PROCESS_BANDS = [
    (100, "low"),
    (250, "normal"),
    (400, "high"),
    (float("inf"), "excessive"),
]


def _quantize(value: float, bands: list[tuple[float, str]]) -> str:
    for threshold, label in bands:
        if value < threshold:
            return label
    return bands[-1][1]


def _load_band(load_1m: float) -> str:
    cpu_count = os.cpu_count() or 4
    ratio = load_1m / cpu_count
    if ratio < 0.25:
        return "idle"
    if ratio < 0.5:
        return "light"
    if ratio < 0.8:
        return "moderate"
    if ratio < 1.2:
        return "heavy"
    return "saturated"


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


@dataclass
class EnvironmentalSignature:
    """Multi-dimensional fingerprint of a system environment state."""

    cpu_band: str = "idle"
    memory_band: str = "idle"
    disk_band: str = "idle"
    load_band: str = "idle"
    process_band: str = "low"
    composite_vector: list[float] = field(default_factory=lambda: [0.0] * 5)

    # ── Construction ──────────────────────────────────────────────────

    @classmethod
    def from_snapshot(cls, snapshot_dict: dict[str, Any]) -> EnvironmentalSignature:
        cpu = float(snapshot_dict.get("cpu_percent", 0.0))
        mem = float(snapshot_dict.get("memory_percent", 0.0))
        disk = float(snapshot_dict.get("disk_percent", 0.0))
        load_1m = float(snapshot_dict.get("load_1m", 0.0))
        procs = int(snapshot_dict.get("process_count", 0))

        cpu_count = os.cpu_count() or 4
        load_ratio = load_1m / cpu_count

        return cls(
            cpu_band=_quantize(cpu, _CPU_BANDS),
            memory_band=_quantize(mem, _MEMORY_BANDS),
            disk_band=_quantize(disk, _DISK_BANDS),
            load_band=_load_band(load_1m),
            process_band=_quantize(procs, _PROCESS_BANDS),
            composite_vector=[
                _clamp(cpu / 100.0),
                _clamp(mem / 100.0),
                _clamp(disk / 100.0),
                _clamp(load_ratio / 2.0),
                _clamp(procs / 500.0),
            ],
        )

    # ── Fingerprint ───────────────────────────────────────────────────

    def fingerprint(self) -> str:
        canonical = f"{self.cpu_band}|{self.memory_band}|{self.disk_band}|{self.load_band}|{self.process_band}"
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # ── Distance / Similarity ─────────────────────────────────────────

    def distance_to(self, other: EnvironmentalSignature) -> float:
        """Euclidean distance between composite vectors, normalized to 0.0–1.0."""
        if len(self.composite_vector) != len(other.composite_vector):
            return 1.0
        sq_sum = sum(
            (a - b) ** 2
            for a, b in zip(self.composite_vector, other.composite_vector)
        )
        max_distance = math.sqrt(len(self.composite_vector))
        return _clamp(math.sqrt(sq_sum) / max_distance)

    def is_similar_to(
        self, other: EnvironmentalSignature, threshold: float = 0.15
    ) -> bool:
        return self.distance_to(other) <= threshold

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_band": self.cpu_band,
            "memory_band": self.memory_band,
            "disk_band": self.disk_band,
            "load_band": self.load_band,
            "process_band": self.process_band,
            "composite_vector": [round(v, 6) for v in self.composite_vector],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvironmentalSignature:
        return cls(
            cpu_band=data.get("cpu_band", "idle"),
            memory_band=data.get("memory_band", "idle"),
            disk_band=data.get("disk_band", "idle"),
            load_band=data.get("load_band", "idle"),
            process_band=data.get("process_band", "low"),
            composite_vector=data.get("composite_vector", [0.0] * 5),
        )
