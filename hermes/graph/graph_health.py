"""Knowledge graph health metrics."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from hermes.deliberation.knowledge_graph import DeliberationKnowledgeGraph


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_RELATIONS = {
    "uses_skill",
    "uses_playbook",
    "has_trust",
    "has_reality_score",
    "has_fitness_score",
    "has_challenge_event",
    "has_core_value",
    "has_principle",
    "has_objective",
    "continuity_link",
}


def build_audit_graph(root: str | Path = ROOT) -> DeliberationKnowledgeGraph:
    base = Path(root)
    graph = DeliberationKnowledgeGraph()
    _add_report_nodes(graph, base)
    _add_registry_nodes(graph, base)
    return graph


def compute_graph_health(root: str | Path = ROOT) -> dict[str, Any]:
    graph = build_audit_graph(root)
    edges = graph.edges
    nodes = set(edges.keys())
    targets = {edge["target"] for items in edges.values() for edge in items}
    all_nodes = nodes | targets
    inbound = Counter(edge["target"] for items in edges.values() for edge in items)
    isolated = sorted(node for node in all_nodes if not edges.get(node) and inbound[node] == 0)
    dangling = sorted(target for target in targets if target not in all_nodes)
    relations = Counter(edge["relation"] for items in edges.values() for edge in items)
    relation_coverage = len(set(relations) & EXPECTED_RELATIONS) / len(EXPECTED_RELATIONS)
    node_coverage = min(1.0, len(all_nodes) / 25)
    edge_coverage = min(1.0, sum(relations.values()) / 40)
    completeness = (node_coverage * 0.35) + (edge_coverage * 0.35) + (relation_coverage * 0.3)
    health = round(max(0.0, min(100.0, completeness * 100 - len(isolated) * 0.5)), 2)
    return {
        "graph_health": health,
        "coverage": {
            "node_coverage": round(node_coverage * 100, 2),
            "edge_coverage": round(edge_coverage * 100, 2),
            "relationship_coverage": round(relation_coverage * 100, 2),
        },
        "node_count": len(all_nodes),
        "edge_count": sum(relations.values()),
        "isolated_nodes": isolated,
        "dangling_references": dangling,
        "relationship_diversity": dict(sorted(relations.items())),
        "recommendations": _recommendations(health, isolated, relation_coverage),
    }


def generate_graph_health_report(output_path: str | Path = "reports/graph_health_report.md") -> dict[str, Any]:
    payload = compute_graph_health()
    lines = [
        "# Graph Health Report",
        "",
        f"Graph Health: {payload['graph_health']:.2f}",
        f"Node Count: {payload['node_count']}",
        f"Edge Count: {payload['edge_count']}",
        "",
        "## Coverage",
        "",
    ]
    for key, value in payload["coverage"].items():
        lines.append(f"- {key}: {value:.2f}")
    lines.extend(["", "## Relationship Diversity", ""])
    for relation, count in payload["relationship_diversity"].items():
        lines.append(f"- {relation}: {count}")
    lines.extend(["", "## Isolated Nodes", ""])
    lines.extend([f"- {node}" for node in payload["isolated_nodes"][:20]] or ["- None detected."])
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in payload["recommendations"])
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = output.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**payload, "report_path": str(output), "json_path": str(json_path)}


def _add_report_nodes(graph: DeliberationKnowledgeGraph, base: Path) -> None:
    reports = sorted((base / "reports").glob("*_report.json"))
    for path in reports:
        node = path.stem
        graph.add_edge("Reports", "contains", node)
        if "reality" in node:
            graph.add_edge(node, "feeds", "Identity")
        if "identity" in node or "continuity" in node:
            graph.add_edge("Identity", "has_report", node)
        if "trust" in node:
            graph.add_edge(node, "feeds", "RealityAlignment")


def _add_registry_nodes(graph: DeliberationKnowledgeGraph, base: Path) -> None:
    registries = {
        "reports/deliberation_skill_registry.json": "Skills",
        "reports/deliberation_playbook_registry.json": "Playbooks",
        "reports/trust_registry.json": "Trust",
        "reports/belief_registry.json": "Beliefs",
        "reports/identity_registry.json": "Identity",
    }
    for rel_path, node in registries.items():
        if (base / rel_path).is_file():
            graph.add_edge("Registries", "contains", node)
            graph.add_edge(node, "stored_in", rel_path)
    if (base / "reports/deliberation_skill_registry.json").is_file():
        graph.add_edge("TaskLifecycle", "uses_skill", "Skills")
    if (base / "reports/deliberation_playbook_registry.json").is_file():
        graph.add_edge("TaskLifecycle", "uses_playbook", "Playbooks")
    if (base / "reports/trust_registry.json").is_file():
        graph.add_edge("Trust", "has_trust", "TrustRecords")
    if (base / "reports/reality_alignment_report.json").is_file():
        graph.add_edge("RealityAlignment", "has_reality_score", "RealityScore")
        graph.add_edge("RealityAlignment", "has_challenge_event", "ChallengeEvents")
    if (base / "reports/institutional_fitness_report.json").is_file():
        graph.add_edge("RealityAlignment", "has_fitness_score", "FitnessScores")
    if (base / "reports/diversity_report.json").is_file():
        graph.add_edge("RealityAlignment", "has_diversity_metric", "DiversityMetrics")
    if (base / "reports/identity_registry.json").is_file():
        graph.add_edge("Identity", "has_core_value", "CoreValues")
        graph.add_edge("Identity", "has_principle", "CorePrinciples")
        graph.add_edge("Identity", "has_objective", "LongTermObjectives")
    if (base / "reports/continuity_report.json").is_file():
        graph.add_edge("Identity", "continuity_link", "ContinuityEvents")


def _recommendations(health: float, isolated: list[str], relation_coverage: float) -> list[str]:
    recommendations = []
    if health < 85:
        recommendations.append("Add explicit graph export coverage for missing relationship types.")
    if isolated:
        recommendations.append("Review isolated nodes and connect them to producer or consumer artifacts.")
    if relation_coverage < 0.8:
        recommendations.append("Add missing relationship categories for release audit visibility.")
    return recommendations or ["Graph coverage is acceptable for v0.9 RC evidence."]
