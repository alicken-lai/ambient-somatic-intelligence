"""Reports for the verification and evidence kernel."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from hermes.deliberation.evaluation.knowledge_reports import build_knowledge_assets
from hermes.deliberation.playbooks import PlaybookRegistry
from hermes.verification.claim_graph import ClaimEvidenceGraph
from hermes.verification.claims import ClaimExtractor, ClaimRegistry
from hermes.verification.evidence import EvidenceRegistry
from hermes.verification.evidence_scoring import evidence_metrics, evidence_score
from hermes.verification.verification_pipeline import VerificationPipeline


def build_verification_assets() -> dict[str, Any]:
    knowledge = build_knowledge_assets()
    artifacts = {
        "skills": [skill.to_dict() for skill in knowledge["skills"]],
        "playbooks": [playbook.to_dict() for playbook in knowledge["playbooks"].values()],
        "failures": knowledge["failures"],
        "patterns": knowledge["patterns"],
    }
    pipeline = VerificationPipeline()
    result = pipeline.run(artifacts, source="phase5_knowledge_assets")
    claims = ClaimExtractor().extract(artifacts, source="phase5_knowledge_assets")
    ClaimRegistry().register(claims)
    EvidenceRegistry().upsert_many([])
    graph = ClaimEvidenceGraph()
    for claim in claims:
        graph.add_claim(claim.claim_id, claim.source)
    return {"knowledge": knowledge, "artifacts": artifacts, "pipeline": result, "claims": claims, "graph": graph}


def playbook_evidence_quality() -> list[dict[str, Any]]:
    playbooks = PlaybookRegistry().load().values()
    ratings: list[dict[str, Any]] = []
    pipeline = VerificationPipeline()
    for playbook in playbooks:
        result = pipeline.run(playbook.to_dict(), source=f"playbook:{playbook.playbook_id}")
        claim_count = len(result["claims"])
        verified = len(result["verified"])
        unsupported = len(result["unsupported"])
        contradicted = len(result["contradicted"])
        score = result["evidence_score"]
        rating = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"
        ratings.append(
            {
                "playbook_id": playbook.playbook_id,
                "claim_count": claim_count,
                "verified_claims": verified,
                "unsupported_claims": unsupported,
                "contradictions": contradicted,
                "evidence_score": score,
                "evidence_quality_rating": rating,
            }
        )
    return ratings


def generate_evidence_report(output_path: str | Path = "reports/evidence_report.md") -> dict[str, Any]:
    assets = build_verification_assets()
    result = assets["pipeline"]
    acquisition_summary = None
    try:
        from hermes.acquisition.reports import build_acquisition_assets

        acquisition_summary = build_acquisition_assets()
    except Exception:
        acquisition_summary = None
    ratings = playbook_evidence_quality()
    lines = [
        "# Evidence Report",
        "",
        f"Evidence score: {result['evidence_score']:.2f}",
        f"Claims extracted: {len(result['claims'])}",
        f"Unsupported claims: {len(result['unsupported'])}",
        f"Contradicted claims: {len(result['contradicted'])}",
    ]
    if acquisition_summary:
        lines.extend(
            [
                f"Acquired evidence score: {acquisition_summary['improved_score']:.2f}",
                f"Evidence score delta: {acquisition_summary['score_delta']:.2f}",
            ]
        )
    lines.extend(["", "## Most Unsupported Claims", ""])
    for claim in result["unsupported"][:10]:
        lines.append(f"- [{claim['risk_level']}] {claim['claim_text']}")
    lines.extend(["", "## Playbook Evidence Quality", "", "| Playbook | Claims | Verified | Unsupported | Contradictions | Score | Rating |", "| --- | ---: | ---: | ---: | ---: | ---: | --- |"])
    for rating in ratings:
        lines.append(
            f"| {rating['playbook_id']} | {rating['claim_count']} | {rating['verified_claims']} | "
            f"{rating['unsupported_claims']} | {rating['contradictions']} | {rating['evidence_score']:.2f} | {rating['evidence_quality_rating']} |"
        )
    payload = {
        "evidence_score": result["evidence_score"],
        "claim_count": len(result["claims"]),
        "unsupported_count": len(result["unsupported"]),
        "playbook_ratings": ratings,
    }
    if acquisition_summary:
        payload["acquired_evidence_score"] = acquisition_summary["improved_score"]
        payload["score_delta"] = acquisition_summary["score_delta"]
    return _write(output_path, lines, payload)


def generate_claim_report(output_path: str | Path = "reports/claim_report.md") -> dict[str, Any]:
    assets = build_verification_assets()
    claims = assets["pipeline"]["claims"]
    by_type: dict[str, int] = {}
    for claim in claims:
        by_type[claim["claim_type"]] = by_type.get(claim["claim_type"], 0) + 1
    lines = ["# Claim Report", "", "## Claim Volume By Type", ""]
    for claim_type, count in sorted(by_type.items()):
        lines.append(f"- {claim_type}: {count}")
    lines.extend(["", "## Highest-Risk Unsupported Claims", ""])
    for claim in assets["pipeline"]["unsupported"]:
        if claim["risk_level"] == "high":
            lines.append(f"- {claim['claim_text']}")
    return _write(output_path, lines, {"claim_count": len(claims), "by_type": by_type})


def generate_verification_report(output_path: str | Path = "reports/verification_report.md") -> dict[str, Any]:
    assets = build_verification_assets()
    result = assets["pipeline"]
    metrics = evidence_metrics(result["claims"], [], result["statuses"], result["contradictions"])
    lines = [
        "# Verification Report",
        "",
        f"Verified: {len(result['verified'])}",
        f"Unsupported: {len(result['unsupported'])}",
        f"Contradicted: {len(result['contradicted'])}",
        f"Confidence: {result['confidence']}",
        "",
        "Verification remains advisory and may not override Guardian.",
    ]
    return _write(output_path, lines, {"verified": len(result["verified"]), "unsupported": len(result["unsupported"]), "contradicted": len(result["contradicted"]), "confidence": result["confidence"], "metrics": metrics})


def generate_contradiction_report(output_path: str | Path = "reports/contradiction_report.md") -> dict[str, Any]:
    assets = build_verification_assets()
    contradictions = [item for item in assets["pipeline"]["contradictions"] if item.get("contradiction")]
    lines = ["# Contradiction Report", "", f"Contradictions detected: {len(contradictions)}", ""]
    for item in contradictions[:20]:
        lines.append(f"- {item['claim_id']}: {item['severity']} - {item['reason']}")
    return _write(output_path, lines, {"contradiction_count": len(contradictions), "contradictions": contradictions})


def recommended_verification_rules() -> list[str]:
    return [
        "High-risk claims require evidence before synthesis confidence can increase.",
        "Provider, security, and governance claims require verification or explicit unsupported status.",
        "Unsupported claims from playbooks should lower evidence quality rating.",
    ]


def _write(path: str | Path, lines: list[str], payload: dict[str, Any]) -> dict[str, Any]:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = output.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**payload, "report_path": str(output), "json_path": str(json_path)}
