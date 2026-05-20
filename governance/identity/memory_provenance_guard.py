"""Memory provenance guard — memory activation must carry origin labels."""

from __future__ import annotations

from governance.identity.cognition_origin import CognitionOrigin
from governance.identity.provenance_record import ProvenanceRecord


class MemoryProvenanceGuard:
    def label_memory_origin(self, record: ProvenanceRecord) -> bool:
        if record.origin != CognitionOrigin.MEMORY:
            return True
        meta = record.metadata
        if meta.get("unlabeled_memory"):
            return False
        return meta.get("memory_activation", True) or "memory" in record.target_key
