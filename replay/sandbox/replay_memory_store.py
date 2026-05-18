"""In-memory replay store that mirrors the production L1–L4 memory hierarchy.

Writes NOTHING to disk.  All data lives in RAM and is discarded when the
replay session ends.  Supports loading historical episodes from JSONL for
replay ingestion, and querying by time range, layer, and confidence.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from memory.ontology.layer_definition import MemoryLayer

logger = logging.getLogger(__name__)


def _parse_dt(val: Any) -> datetime:
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    return datetime.now(timezone.utc)


# ── Lightweight entry wrapper ─────────────────────────────────────────────


@dataclass
class ReplayEntry:
    """Uniform wrapper around any ontology-layer entry stored in the sandbox.

    Keeps the original dict payload so that layer-specific schemas don't
    need to be instantiated unless the caller explicitly deserialises.
    """

    entry_id: str
    layer: MemoryLayer
    confidence: float
    timestamp: datetime
    payload: dict[str, Any] = field(default_factory=dict)
    provenance: str = "loaded"  # "loaded" | "promoted" | "decayed" | "synthetic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "layer": self.layer.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReplayEntry:
        return cls(
            entry_id=data["entry_id"],
            layer=MemoryLayer(data["layer"]),
            confidence=float(data.get("confidence", 0.0)),
            timestamp=_parse_dt(data.get("timestamp")),
            payload=data.get("payload", {}),
            provenance=data.get("provenance", "loaded"),
        )


# ── Replay Memory Store ──────────────────────────────────────────────────


class ReplayMemoryStore:
    """Pure in-memory L1–L4 store for replay sessions.

    Key guarantees:
      - Zero disk I/O for writes.
      - Append-only audit log of every mutation.
      - Query by layer, time range, confidence band.
      - Export entire state as JSON.
    """

    def __init__(self) -> None:
        self._layers: dict[MemoryLayer, dict[str, ReplayEntry]] = {
            layer: {} for layer in MemoryLayer
        }
        self._audit: list[dict[str, Any]] = []
        self._ingested_count: int = 0

    # ── Ingestion ─────────────────────────────────────────────────────

    def load_episodes_from_jsonl(
        self,
        path: str | Path,
        *,
        max_entries: int = 0,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
    ) -> int:
        """Load historical episodes from a JSONL file into L1.

        Returns the number of entries loaded.  This is the ONLY method
        that touches the filesystem (read-only).
        """
        loaded = 0
        path = Path(path)
        if not path.exists():
            logger.warning("JSONL file not found: %s", path)
            return 0

        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts = _parse_dt(data.get("timestamp"))
                if time_start and ts < time_start:
                    continue
                if time_end and ts > time_end:
                    continue

                entry_id = data.get("episode_id") or data.get("entry_id", "")
                if not entry_id:
                    continue

                entry = ReplayEntry(
                    entry_id=entry_id,
                    layer=MemoryLayer.L1_EPISODIC,
                    confidence=float(data.get("confidence", data.get("anomaly_score", 0.5))),
                    timestamp=ts,
                    payload=data,
                    provenance="loaded",
                )
                self._layers[MemoryLayer.L1_EPISODIC][entry_id] = entry
                loaded += 1

                if max_entries and loaded >= max_entries:
                    break

        self._ingested_count += loaded
        self._record_audit("load_episodes", {
            "source": str(path),
            "loaded_count": loaded,
        })
        return loaded

    def ingest_entries(self, entries: list[dict[str, Any]], layer: MemoryLayer) -> int:
        """Programmatically ingest pre-parsed entries into a specific layer."""
        count = 0
        for data in entries:
            entry_id = data.get("entry_id", "")
            if not entry_id:
                continue
            entry = ReplayEntry(
                entry_id=entry_id,
                layer=layer,
                confidence=float(data.get("confidence", 0.5)),
                timestamp=_parse_dt(data.get("timestamp")),
                payload=data,
                provenance="loaded",
            )
            self._layers[layer][entry_id] = entry
            count += 1
        self._ingested_count += count
        self._record_audit("ingest_entries", {
            "layer": layer.value,
            "count": count,
        })
        return count

    # ── Write (memory only) ──────────────────────────────────────────

    def store(self, entry: ReplayEntry) -> None:
        """Store an entry in the appropriate layer (memory only)."""
        self._layers[entry.layer][entry.entry_id] = entry
        self._record_audit("store", {
            "entry_id": entry.entry_id,
            "layer": entry.layer.value,
            "confidence": entry.confidence,
            "provenance": entry.provenance,
        })

    def promote(
        self,
        entry_id: str,
        source_layer: MemoryLayer,
        target_layer: MemoryLayer,
        new_entry_id: str,
        confidence: float,
        payload: dict[str, Any] | None = None,
    ) -> ReplayEntry:
        """Record a promotion into the target layer."""
        source = self._layers[source_layer].get(entry_id)
        promoted = ReplayEntry(
            entry_id=new_entry_id,
            layer=target_layer,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc),
            payload=payload or (source.payload if source else {}),
            provenance="promoted",
        )
        self._layers[target_layer][new_entry_id] = promoted
        self._record_audit("promote", {
            "source_entry_id": entry_id,
            "source_layer": source_layer.value,
            "new_entry_id": new_entry_id,
            "target_layer": target_layer.value,
            "confidence": confidence,
        })
        return promoted

    def update_confidence(
        self,
        entry_id: str,
        layer: MemoryLayer,
        new_confidence: float,
        reason: str,
    ) -> bool:
        """Update an entry's confidence (in memory only)."""
        entry = self._layers[layer].get(entry_id)
        if entry is None:
            return False
        old_conf = entry.confidence
        entry.confidence = new_confidence
        self._record_audit("update_confidence", {
            "entry_id": entry_id,
            "layer": layer.value,
            "previous": old_conf,
            "new": new_confidence,
            "reason": reason,
        })
        return True

    def remove(self, entry_id: str, layer: MemoryLayer) -> bool:
        """Remove an entry from a layer (in memory only)."""
        if entry_id in self._layers[layer]:
            del self._layers[layer][entry_id]
            self._record_audit("remove", {
                "entry_id": entry_id,
                "layer": layer.value,
            })
            return True
        return False

    # ── Query ─────────────────────────────────────────────────────────

    def get(self, entry_id: str, layer: MemoryLayer) -> ReplayEntry | None:
        return self._layers[layer].get(entry_id)

    def get_all(self, layer: MemoryLayer) -> list[ReplayEntry]:
        return list(self._layers[layer].values())

    def query(
        self,
        *,
        layer: MemoryLayer | None = None,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0,
        provenance: str | None = None,
        max_results: int = 0,
    ) -> list[ReplayEntry]:
        """Flexible query across the replay store."""
        results: list[ReplayEntry] = []
        layers = [layer] if layer else list(MemoryLayer)

        for lyr in layers:
            for entry in self._layers[lyr].values():
                if time_start and entry.timestamp < time_start:
                    continue
                if time_end and entry.timestamp > time_end:
                    continue
                if entry.confidence < min_confidence or entry.confidence > max_confidence:
                    continue
                if provenance and entry.provenance != provenance:
                    continue
                results.append(entry)
                if max_results and len(results) >= max_results:
                    return results

        results.sort(key=lambda e: e.timestamp)
        return results

    def count(self, layer: MemoryLayer | None = None) -> int:
        if layer:
            return len(self._layers[layer])
        return sum(len(entries) for entries in self._layers.values())

    def layer_summary(self) -> dict[str, int]:
        return {layer.name: len(entries) for layer, entries in self._layers.items()}

    # ── Audit & Export ────────────────────────────────────────────────

    @property
    def audit_log(self) -> list[dict[str, Any]]:
        return list(self._audit)

    @property
    def ingested_count(self) -> int:
        return self._ingested_count

    def export_state(self) -> dict[str, Any]:
        """Export the full replay store state as a JSON-serialisable dict."""
        state: dict[str, Any] = {
            "summary": self.layer_summary(),
            "total_entries": self.count(),
            "ingested_count": self._ingested_count,
            "layers": {},
            "audit_log": self._audit,
        }
        for layer in MemoryLayer:
            state["layers"][layer.name] = [
                entry.to_dict() for entry in self._layers[layer].values()
            ]
        return state

    def _record_audit(self, action: str, details: dict[str, Any]) -> None:
        self._audit.append({
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details,
        })
