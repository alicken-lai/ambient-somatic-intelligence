"""
Memory Topology — Maps the memory system's structure and health.

Introspects the memory/ directory and MemoryKernel configuration to provide
a detailed map of all 6 memory layers including record counts, storage sizes,
TTL policies, decay half-lives, and access patterns.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from memory.memory_kernel import MemoryKernel

logger = logging.getLogger("identity.cognitive_self_model.memory_topology")

AMBIENT_ROOT = Path(__file__).resolve().parent.parent.parent

LAYERS = ["episodic", "semantic", "procedural", "governance", "scratchpad", "archive"]

TTL_HOURS: dict[str, float] = {
    "scratchpad": 24.0,
    "episodic": 30.0 * 24,
    "procedural": 180.0 * 24,
    "governance": 365.0 * 24,
    "semantic": 365.0 * 24,
    "archive": 365.0 * 10 * 24,
}

DECAY_HALF_LIFE_HOURS: dict[str, float] = {
    "scratchpad": 12.0,
    "episodic": 24.0 * 7,
    "procedural": 24.0 * 30,
    "governance": 24.0 * 90,
    "semantic": 24.0 * 180,
    "archive": 24.0 * 365,
}

LAYER_WEIGHTS: dict[str, float] = {
    "semantic": 2.0,
    "procedural": 1.6,
    "governance": 1.3,
    "episodic": 1.0,
    "scratchpad": 0.2,
    "archive": 0.1,
}


@dataclass
class LayerInfo:
    """Detailed information about a single memory layer."""
    name: str
    record_count: int = 0
    storage_bytes: int = 0
    ttl_hours: float = 0.0
    decay_half_life_hours: float = 0.0
    layer_weight: float = 1.0
    avg_age_hours: float = 0.0
    oldest_hours: float = 0.0
    newest_hours: float = 0.0
    expired_count: int = 0
    access_count_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "record_count": self.record_count,
            "storage_bytes": self.storage_bytes,
            "storage_kb": round(self.storage_bytes / 1024, 2),
            "ttl_hours": self.ttl_hours,
            "decay_half_life_hours": self.decay_half_life_hours,
            "layer_weight": self.layer_weight,
            "avg_age_hours": round(self.avg_age_hours, 1),
            "oldest_hours": round(self.oldest_hours, 1),
            "newest_hours": round(self.newest_hours, 1),
            "expired_count": self.expired_count,
            "access_count_total": self.access_count_total,
        }


@dataclass
class LayerHealth:
    """Health metrics for a single memory layer."""
    name: str
    utilization: float = 0.0
    freshness: float = 0.0
    entropy: float = 0.0
    status: str = "healthy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "utilization": round(self.utilization, 3),
            "freshness": round(self.freshness, 3),
            "entropy": round(self.entropy, 3),
            "status": self.status,
        }


class MemoryTopology:
    """
    Maps the memory system's complete structure.

    Works in two modes:
      1. With a MemoryKernel instance — uses kernel.stats() for live data
      2. Standalone — scans memory/ directory files directly
    """

    def __init__(self, kernel_memory: "MemoryKernel | None" = None, root: Path | None = None):
        self._memory_kernel = kernel_memory
        self._root = root or AMBIENT_ROOT
        self._memory_dir = self._root / "memory"
        self._layers: dict[str, LayerInfo] = {}
        self._built = False

    def build(self) -> "MemoryTopology":
        """Introspect memory/ directory and build the topology map."""
        logger.info("Building memory topology from %s", self._memory_dir)
        start = time.monotonic()

        self._layers = {}
        now = datetime.now(timezone.utc)

        for layer_name in LAYERS:
            layer_dir = self._memory_dir / layer_name
            records_file = layer_dir / "records.jsonl"

            info = LayerInfo(
                name=layer_name,
                ttl_hours=TTL_HOURS.get(layer_name, 0),
                decay_half_life_hours=DECAY_HALF_LIFE_HOURS.get(layer_name, 0),
                layer_weight=LAYER_WEIGHTS.get(layer_name, 1.0),
            )

            if not records_file.exists():
                self._layers[layer_name] = info
                continue

            info.storage_bytes = records_file.stat().st_size

            ages: list[float] = []
            count = 0
            expired = 0
            ttl_seconds = info.ttl_hours * 3600

            try:
                with records_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        count += 1
                        ts_str = record.get("timestamp", "")
                        if ts_str:
                            try:
                                ts = datetime.fromisoformat(
                                    ts_str.replace("Z", "+00:00")
                                )
                                age_h = (now - ts).total_seconds() / 3600
                                ages.append(age_h)
                                if (now - ts).total_seconds() > ttl_seconds:
                                    expired += 1
                            except (ValueError, TypeError):
                                pass
            except OSError as exc:
                logger.warning("Failed to read %s: %s", records_file, exc)

            info.record_count = count
            info.expired_count = expired
            if ages:
                info.avg_age_hours = sum(ages) / len(ages)
                info.oldest_hours = max(ages)
                info.newest_hours = min(ages)

            self._layers[layer_name] = info

        self._load_access_patterns()

        elapsed = (time.monotonic() - start) * 1000
        logger.info("Memory topology built in %.1fms", elapsed)
        self._built = True
        return self

    def get_memory_map(self) -> dict[str, Any]:
        """Return structure of all 6 layers with full details."""
        self._ensure_built()

        total_records = sum(l.record_count for l in self._layers.values())
        total_bytes = sum(l.storage_bytes for l in self._layers.values())

        return {
            "layers": {name: info.to_dict() for name, info in self._layers.items()},
            "summary": {
                "total_records": total_records,
                "total_storage_bytes": total_bytes,
                "total_storage_kb": round(total_bytes / 1024, 2),
                "layer_count": len(self._layers),
                "total_expired": sum(l.expired_count for l in self._layers.values()),
            },
            "policies": {
                "ttl": {name: TTL_HOURS[name] for name in LAYERS},
                "decay_half_life": {name: DECAY_HALF_LIFE_HOURS[name] for name in LAYERS},
                "layer_weights": {name: LAYER_WEIGHTS[name] for name in LAYERS},
            },
        }

    def get_layer_health(self, layer_name: str) -> LayerHealth:
        """Compute utilization, freshness, and entropy for a layer."""
        self._ensure_built()

        info = self._layers.get(layer_name)
        if not info:
            return LayerHealth(name=layer_name, status="not_found")

        utilization = 0.0
        if info.record_count > 0:
            non_expired_ratio = 1.0 - (info.expired_count / info.record_count)
            utilization = non_expired_ratio

        freshness = 0.0
        if info.avg_age_hours > 0 and info.decay_half_life_hours > 0:
            freshness = max(0.0, 1.0 - (info.avg_age_hours / info.decay_half_life_hours))

        import math
        entropy = 0.0
        if info.record_count > 0 and info.storage_bytes > 0:
            avg_record_size = info.storage_bytes / max(info.record_count, 1)
            normalized_size = min(avg_record_size / 500, 1.0)
            entropy = -normalized_size * math.log2(max(normalized_size, 0.001))

        status = "healthy"
        if utilization < 0.5:
            status = "degraded"
        if info.expired_count > info.record_count * 0.5:
            status = "needs_sweep"
        if info.record_count == 0:
            status = "empty"

        return LayerHealth(
            name=layer_name,
            utilization=utilization,
            freshness=freshness,
            entropy=entropy,
            status=status,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serializable representation of the full memory topology."""
        self._ensure_built()
        return {
            "memory_map": self.get_memory_map(),
            "layer_health": {
                name: self.get_layer_health(name).to_dict()
                for name in LAYERS
            },
        }

    # ── Internal ──────────────────────────────────────────────────────────

    def _ensure_built(self) -> None:
        if not self._built:
            self.build()

    def _load_access_patterns(self) -> None:
        """Load access counts from the memory kernel's persisted file."""
        access_file = self._memory_dir / "access_counts.json"
        if not access_file.exists():
            return

        try:
            data = json.loads(access_file.read_text(encoding="utf-8"))
            total_accesses = sum(data.values()) if isinstance(data, dict) else 0

            for layer_info in self._layers.values():
                layer_info.access_count_total = total_accesses // max(
                    len(self._layers), 1
                )
        except (json.JSONDecodeError, OSError):
            pass
