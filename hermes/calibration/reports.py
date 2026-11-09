"""Reports for trust and knowledge calibration."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from hermes.acquisition.reports import build_acquisition_assets
from hermes.acquisition.sources import SourceRegistry
from hermes.calibration.confidence_model import confidence_from_assets
from hermes.calibration.drift_detector import detect_drift
from hermes.calibration.inflation_detector import detect_inflation
from hermes.calibration.knowledge_health import compute_knowledge_health
from hermes.calibration.source_trust import baseline_source_trust
from hermes.calibration.trust import TrustRegistry
from hermes.calibration.trust_evolution import evolve_trust


def build_calibration_assets() -> dict[str, Any]:
    acquisition = build_acquisition_assets()
    sources = SourceRegistry().load()
    trust_records = [baseline_source_trust(source) for source in sources.values()]
    TrustRegistry().upsert_many(trust_records)
    confidence = confidence_from_assets(acquisition)
    inflation = detect_inflation(
        [candidate for candidate in _evidence_from_acquisition(acquisition)],
        acquisition["acquisition"].get("links", []),
    )
    drift = detect_drift(list(sources.values()), stale_days=30)
    avg_trust = sum(record.trust_score for record in trust_records) / max(1, len(trust_records))
    health = compute_knowledge_health(
        trust=avg_trust,
        freshness=confidence["freshness"] / 100.0,
        consistency=confidence["consistency"] / 100.0,
        verification=confidence["verification"] / 100.0,
        drift=1.0 if drift["drift_detected"] else 0.0,
        inflation=float(inflation["inflation_risk"]),
        coverage=confidence["coverage"] / 100.0,
    )
    return {
        "acquisition": acquisition,
        "sources": sources,
        "trust_records": trust_records,
        "confidence": confidence,
        "inflation": inflation,
        "drift": drift,
        "health": health,
    }


def generate_knowledge_health_report(output_path: str | Path = "reports/knowledge_health_report.md") -> dict[str, Any]:
    assets = build_calibration_assets()
    health = assets["health"]
    trust_records = sorted(assets["trust_records"], key=lambda item: item.trust_score, reverse=True)
    lines = [
        "# Knowledge Health Report",
        "",
        f"Knowledge Health Score: {health['health_score']:.2f}",
        f"Risk Level: {health['risk_level']}",
        f"Raw acquired evidence score: {assets['acquisition']['improved_score']:.2f}",
        f"Calibrated confidence overall: {assets['confidence']['overall']:.2f}",
        "",
        "## Top Trusted Sources",
        "",
    ]
    for record in trust_records[:5]:
        lines.append(f"- {record.entity_id}: {record.trust_score:.2f}")
    lines.extend(["", "## Lowest Trusted Sources", ""])
    for record in trust_records[-5:]:
        lines.append(f"- {record.entity_id}: {record.trust_score:.2f}")
    lines.extend(["", "## Risks", "", f"- Drift: {assets['drift']['severity']}", f"- Inflation: {assets['inflation']['inflation_risk']} - {assets['inflation']['reason']}"])
    return _write(output_path, lines, {"health": health, "confidence": assets["confidence"], "inflation": assets["inflation"], "drift": assets["drift"]})


def generate_trust_report(output_path: str | Path = "reports/trust_report.md") -> dict[str, Any]:
    assets = build_calibration_assets()
    records = sorted(assets["trust_records"], key=lambda item: item.trust_score, reverse=True)
    evolutions = [evolve_trust(record.trust_score, verification_success=1, freshness=1.0) for record in records]
    lines = ["# Trust Report", "", "## Trust Rankings", ""]
    for record in records:
        lines.append(f"- {record.entity_id}: {record.trust_score:.2f} ({'; '.join(record.reasoning)})")
    lines.extend(["", "## Trust Evolution", ""])
    for record, evolution in zip(records, evolutions):
        lines.append(f"- {record.entity_id}: {evolution['event']} to {evolution['trust_score']}")
    lines.extend(["", "## Evidence Quality Distribution", "", f"- Inflation risk: {assets['inflation']['inflation_risk']}", f"- Calibrated confidence: {assets['confidence']['overall']:.2f}"])
    return _write(output_path, lines, {"trust_records": [record.to_dict() for record in records], "evolutions": evolutions, "confidence": assets["confidence"]})


def generate_drift_report(output_path: str | Path = "reports/drift_report.md") -> dict[str, Any]:
    assets = build_calibration_assets()
    drift = assets["drift"]
    lines = ["# Drift Report", "", f"Drift detected: {drift['drift_detected']}", f"Severity: {drift['severity']}", "", "## Stale Assets", ""]
    for item in drift["stale_assets"]:
        lines.append(f"- {item['item']}: {item['age_days']} days")
    lines.extend(["", "## Risk Recommendations", "", f"- {drift['recommendation']}"])
    return _write(output_path, lines, drift)


def _evidence_from_acquisition(acquisition: dict[str, Any]) -> list[Any]:
    from hermes.verification.evidence import Evidence

    return [Evidence.from_dict(item) for item in acquisition["acquisition"].get("candidate_evidence", [])]


def _write(path: str | Path, lines: list[str], payload: dict[str, Any]) -> dict[str, Any]:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = output.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**payload, "report_path": str(output), "json_path": str(json_path)}
