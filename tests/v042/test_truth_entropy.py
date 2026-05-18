"""Duplicate and truth integrity detection."""

from __future__ import annotations

from kernel.entropy.truth_entropy_adapter import TruthEntropyAdapter
from kernel.truth import Mutability, TruthGraph, TruthNode


def test_duplicate_and_checksum_detection(truth_graph: TruthGraph) -> None:
    adapter = TruthEntropyAdapter()
    clean = adapter.observe(truth_graph)
    assert all(m.value == 0.0 for m in clean if m.name == "truth_duplicate_nodes")

    node = truth_graph.nodes["test:baseline"]
    bad = TruthNode(
        id=node.id,
        source=node.source,
        owner=node.owner,
        timestamp=node.timestamp,
        checksum=node.checksum,
        version=node.version,
        mutability=node.mutability,
        payload={"tampered": True},
    )
    truth_graph.nodes[bad.id] = bad

    metrics = {m.name: m for m in adapter.observe(truth_graph)}
    assert metrics["truth_checksum_divergence"].value > 0
    assert metrics["truth_orphan_nodes"].value == 1.0  # isolated node has no edges


def test_orphan_truth_node() -> None:
    graph = TruthGraph()
    for i in range(2):
        n = TruthNode.create(
            node_id=f"orphan:{i}",
            source="tests",
            owner="tests",
            version="1",
            mutability=Mutability.MUTABLE,
            payload={"i": i},
        )
        graph.register_node(n)

    metrics = {m.name: m for m in TruthEntropyAdapter().observe(graph)}
    assert metrics["truth_orphan_nodes"].value == 1.0  # both lack edges
