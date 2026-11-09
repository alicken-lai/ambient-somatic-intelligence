"""Reports for evidence acquisition."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from hermes.acquisition.acquisition_pipeline import AcquisitionPipeline
from hermes.acquisition.evidence_quality import evidence_quality_rating
from hermes.acquisition.knowledge_index import KnowledgeIndex
from hermes.acquisition.sources import SourceRegistry
from hermes.verification.reports import build_verification_assets


def build_acquisition_assets() -> dict[str, Any]:
    assets = build_verification_assets()
    artifact = assets["artifacts"]
    baseline_score = assets["pipeline"]["evidence_score"]
    acquisition = AcquisitionPipeline().run(artifact, source="phase6_acquisition", task="improve evidence score")
    improved_score = acquisition["verification"]["evidence_score"]
    return {
        "baseline_score": baseline_score,
        "improved_score": improved_score,
        "score_delta": round(improved_score - baseline_score, 2),
        "acquisition": acquisition,
    }


def generate_acquisition_report(output_path: str | Path = "reports/acquisition_report.md") -> dict[str, Any]:
    assets = build_acquisition_assets()
    acquisition = assets["acquisition"]
    lines = [
        "# Evidence Acquisition Report",
        "",
        f"Baseline evidence score: {assets['baseline_score']:.2f}",
        f"Acquired evidence score: {assets['improved_score']:.2f}",
        f"Score delta: {assets['score_delta']:.2f}",
        f"Claims: {len(acquisition['claims'])}",
        f"Candidate evidence: {len(acquisition['candidate_evidence'])}",
        f"Links: {len(acquisition['links'])}",
        "",
        "## Acquisition Trace",
        "",
    ]
    for item in acquisition["acquisition_trace"][:20]:
        lines.append(f"- {item['claim_id']} <- {item['source_reference']} ({item['relevance_score']})")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(acquisition_recommendations(acquisition))
    return _write(
        output_path,
        lines,
        {
            "baseline_score": assets["baseline_score"],
            "improved_score": assets["improved_score"],
            "score_delta": assets["score_delta"],
            "candidate_evidence": len(acquisition["candidate_evidence"]),
            "links": len(acquisition["links"]),
        },
    )


def generate_evidence_quality_report(output_path: str | Path = "reports/evidence_quality_report.md") -> dict[str, Any]:
    assets = build_acquisition_assets()
    acquisition = assets["acquisition"]
    sources = SourceRegistry().load()
    empty_rating = evidence_quality_rating(
        evidence=[],
        links=[],
        sources=sources,
        verification_success_history=acquisition["confidence"]["confidence"],
    )
    actual_rating = acquisition["quality"]
    lines = [
        "# Evidence Quality Report",
        "",
        f"Acquisition quality rating: {actual_rating['rating']}",
        f"Acquisition quality score: {actual_rating['score']:.2f}",
        f"Confidence: {acquisition['confidence']['confidence']:.2f}",
        "",
        "## Confidence Reasoning",
        "",
    ]
    lines.extend([f"- {item}" for item in acquisition["confidence"]["reasoning"]])
    return _write(output_path, lines, {"quality": actual_rating, "empty_baseline_rating": empty_rating})


def generate_knowledge_index_report(output_path: str | Path = "reports/knowledge_index_report.md") -> dict[str, Any]:
    index = KnowledgeIndex().build()
    source_counts: dict[str, int] = {}
    for item in index.items:
        source_counts[item.source_type] = source_counts.get(item.source_type, 0) + 1
    lines = [
        "# Knowledge Index Report",
        "",
        f"Indexed items: {len(index.items)}",
        "",
        "## Source Coverage",
        "",
    ]
    for source_type, count in sorted(source_counts.items()):
        lines.append(f"- {source_type}: {count}")
    search = index.semantic_search("unsupported claim evidence verification", limit=5)
    lines.extend(["", "## Sample Search Results", ""])
    for item, score in search:
        lines.append(f"- {item.reference} ({score})")
    return _write(output_path, lines, {"indexed_items": len(index.items), "source_coverage": source_counts})


def acquisition_recommendations(acquisition: dict[str, Any]) -> list[str]:
    recommendations = []
    if not acquisition["links"]:
        recommendations.append("Add more internal evidence artifacts for unsupported claim clusters.")
    if acquisition["verification"]["unsupported"]:
        recommendations.append("Create targeted tests or reports for high-risk unsupported claims.")
    if acquisition["confidence"]["confidence"] < 0.6:
        recommendations.append("Increase source diversity and trust before reusing evidence automatically.")
    return recommendations or ["Current acquisition produced reusable evidence links."]


def _write(path: str | Path, lines: list[str], payload: dict[str, Any]) -> dict[str, Any]:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = output.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**payload, "report_path": str(output), "json_path": str(json_path)}
