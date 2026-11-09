"""Claim-evidence graph."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


class ClaimEvidenceGraph:
    def __init__(self):
        self.edges: dict[str, list[dict[str, str]]] = defaultdict(list)
        self.claim_sources: dict[str, str] = {}

    def add_claim(self, claim_id: str, source: str) -> None:
        self.claim_sources[claim_id] = source

    def add_edge(self, source: str, relation: str, target: str) -> None:
        edge = {"relation": relation, "target": target}
        if edge not in self.edges[source]:
            self.edges[source].append(edge)

    def link_evidence(self, claim_id: str, evidence_id: str) -> None:
        self.add_edge(claim_id, "supported_by", evidence_id)

    def link_contradiction(self, claim_id: str, target: str) -> None:
        self.add_edge(claim_id, "contradicted_by", target)

    def unsupported_by_source(self, unsupported_claim_ids: list[str]) -> list[dict[str, Any]]:
        counts = Counter(self.claim_sources.get(claim_id, "unknown") for claim_id in unsupported_claim_ids)
        return [{"source": source, "unsupported_count": count} for source, count in counts.most_common()]

    def repeated_failures(self, statuses: dict[str, str]) -> list[str]:
        return [claim_id for claim_id, status in statuses.items() if status in {"unsupported", "contradicted"}]

    def query(self, claim_id: str, relation: str | None = None) -> list[dict[str, str]]:
        edges = self.edges.get(claim_id, [])
        if relation is None:
            return list(edges)
        return [edge for edge in edges if edge["relation"] == relation]
