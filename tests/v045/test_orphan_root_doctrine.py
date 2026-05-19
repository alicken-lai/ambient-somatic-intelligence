"""Root-only graphs are clean by doctrine."""

from kernel.entropy.truth_entropy_adapter import TruthEntropyAdapter
from kernel.truth import Mutability, TruthGraph, TruthNode
from kernel.truth.truth_edge import EdgeKind, TruthEdge


def test_edgeless_single_node_not_orphan() -> None:
    graph = TruthGraph()
    graph.register_node(
        TruthNode.create(
            node_id="root",
            source="test",
            owner="test",
            version="1",
            mutability=Mutability.IMMUTABLE,
            payload={},
        )
    )
    assert TruthEntropyAdapter._orphan_truth_nodes(graph) == []


def test_disconnected_node_on_edged_graph_is_orphan() -> None:
    graph = TruthGraph()
    a = TruthNode.create(
        node_id="a",
        source="test",
        owner="test",
        version="1",
        mutability=Mutability.MUTABLE,
        payload={},
    )
    b = TruthNode.create(
        node_id="b",
        source="test",
        owner="test",
        version="1",
        mutability=Mutability.MUTABLE,
        payload={},
    )
    c = TruthNode.create(
        node_id="c",
        source="test",
        owner="test",
        version="1",
        mutability=Mutability.MUTABLE,
        payload={},
    )
    graph.register_node(a)
    graph.register_node(b)
    graph.register_node(c)
    graph.add_edge(
        TruthEdge(source_id="a", target_id="b", kind=EdgeKind.DEPENDS_ON),
    )
    orphans = TruthEntropyAdapter._orphan_truth_nodes(graph)
    assert "c" in orphans
