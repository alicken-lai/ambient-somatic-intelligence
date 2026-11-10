"""Knowledge diversity scoring for echo-chamber resistance."""

from __future__ import annotations

from collections import Counter
from typing import Any

from hermes.reality_alignment.reality_models import RealityTarget


INTERNAL_MARKERS = ("internal", "phase", "hermes", "deliberation", "report", "registry", "playbook", "skill")


def source_kind(source: str) -> str:
    lowered = source.lower()
    if lowered.startswith("http") or lowered.startswith("external:") or "benchmark" in lowered or "pytest" in lowered:
        return "external"
    if any(marker in lowered for marker in INTERNAL_MARKERS):
        return "internal"
    return "external"


def measure_knowledge_diversity(targets: list[RealityTarget]) -> dict[str, Any]:
    sources: list[str] = []
    internal = 0
    external = 0
    for target in targets:
        target_sources = target.sources or [*target.internal_sources, *target.external_sources]
        for source in target_sources:
            sources.append(source)
            if source_kind(source) == "internal":
                internal += 1
            else:
                external += 1

    total = max(1, internal + external)
    counts = Counter(sources)
    most_common = counts.most_common(1)[0][1] if counts else 0
    source_variety = len(counts)
    concentration = most_common / max(1, len(sources))
    external_ratio = external / total
    internal_ratio = internal / total
    variety_component = min(1.0, source_variety / max(1, len(targets) * 2))
    score = (external_ratio * 45.0) + (variety_component * 35.0) + ((1.0 - concentration) * 20.0)
    return {
        "diversity_score": round(max(0.0, min(100.0, score)), 2),
        "internal_ratio": round(internal_ratio, 4),
        "external_ratio": round(external_ratio, 4),
        "source_variety": source_variety,
        "source_concentration": round(concentration, 4),
    }
