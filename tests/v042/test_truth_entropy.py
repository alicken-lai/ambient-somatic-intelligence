"""Duplicate and truth integrity detection."""

from __future__ import annotations

from kernel.entropy.truth_entropy_adapter import TruthEntropyAdapter
from kernel.truth import Mutability, TruthGraph, TruthNode
from kernel.truth.truth_edge import EdgeKind, TruthEdge


def test_duplicate_and_checksum_detection(truth_graph: TruthGraph) -> None:
    adapter = TruthEntropyAdapter()
    clean = adapter.observe(truth_graph)
    assert all(m.value == 0.0 for m in clean if m.name == "truth_duplicate_nodes")

    linked = TruthNode.create(
        node_id="test:linked",
        source="tests.v042",
        owner="tests",
        version="1.0",
        mutability=Mutability.IMMUTABLE,
        payload={"linked": True},
    )
    truth_graph.register_node(linked)
    truth_graph.add_edge(
        TruthEdge(
            source_id="test:baseline",
            target_id="test:linked",
            kind=EdgeKind.DEPENDS_ON,
        )
    )

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
    # Edgeless exemption: baseline-only graphs do not incur orphan pressure.
    assert metrics["truth_orphan_nodes"].value == 0.0


def test_orphan_truth_node() -> None:
    graph = TruthGraph()
    nodes = []
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
        nodes.append(n)

    graph.add_edge(
        TruthEdge(
            source_id=nodes[0].id,
            target_id=nodes[1].id,
            kind=EdgeKind.DEPENDS_ON,
        )
    )
    disconnected = TruthNode.create(
        node_id="orphan:isolated",
        source="tests",
        owner="tests",
        version="1",
        mutability=Mutability.MUTABLE,
        payload={"isolated": True},
    )
    graph.register_node(disconnected)

    metrics = {m.name: m for m in TruthEntropyAdapter().observe(graph)}
    assert metrics["truth_orphan_nodes"].value > 0
    assert "orphan:isolated" in metrics["truth_orphan_nodes"].metadata.get(
        "orphan_ids", []
    )
