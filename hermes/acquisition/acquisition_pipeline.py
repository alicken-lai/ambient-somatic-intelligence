"""Evidence acquisition pipeline."""

from __future__ import annotations

from typing import Any

from hermes.acquisition.confidence_model import calculate_confidence
from hermes.acquisition.evidence_collector import EvidenceCollector
from hermes.acquisition.evidence_linker import EvidenceLinker
from hermes.acquisition.evidence_quality import evidence_quality_rating
from hermes.acquisition.knowledge_reuse import KnowledgeReuseEngine
from hermes.acquisition.sources import SourceRegistry
from hermes.verification.claims import ClaimExtractor, ClaimRegistry
from hermes.verification.evidence import EvidenceRegistry
from hermes.verification.verification_pipeline import VerificationPipeline


class AcquisitionPipeline:
    def __init__(
        self,
        extractor: ClaimExtractor | None = None,
        collector: EvidenceCollector | None = None,
        linker: EvidenceLinker | None = None,
    ):
        self.extractor = extractor or ClaimExtractor()
        self.collector = collector or EvidenceCollector()
        self.linker = linker or EvidenceLinker()
        self.sources = SourceRegistry()
        self.claim_registry = ClaimRegistry()
        self.evidence_registry = EvidenceRegistry()

    def run(self, artifact: Any, *, source: str = "artifact", task: str | None = None, playbook: str | None = None) -> dict[str, Any]:
        claims = self.extractor.extract(artifact, source=source)
        self.claim_registry.register(claims)
        existing = list(self.evidence_registry.load().values())
        all_evidence = []
        all_links = []
        trace = []
        reuse_events = []
        for claim in claims:
            reuse = KnowledgeReuseEngine().reuse(claim, existing)
            reuse_events.append({"claim_id": claim.claim_id, **reuse.to_dict()})
            candidates = self.collector.collect(claim=claim, task=task, playbook=playbook)
            links = self.linker.link(claim, candidates)
            evidence = [candidate.evidence for candidate in candidates]
            all_evidence.extend(evidence)
            all_links.extend(links)
            trace.extend([candidate.acquisition_trace for candidate in candidates])
        self.evidence_registry.upsert_many(all_evidence)
        verification = VerificationPipeline().run(artifact, source=source, evidence=[*existing, *all_evidence])
        confidence = calculate_confidence(evidence=all_evidence, links=all_links, sources=self.sources.load())
        quality = evidence_quality_rating(evidence=all_evidence, links=all_links, sources=self.sources.load())
        return {
            "claims": [claim.to_dict() for claim in claims],
            "candidate_evidence": [item.to_dict() for item in all_evidence],
            "links": [link.to_dict() for link in all_links],
            "confidence": confidence,
            "verification": verification,
            "quality": quality,
            "reuse_events": reuse_events,
            "acquisition_trace": trace,
        }
