"""Tests for v0.4 Truth, Entropy, Isolation stabilization layer."""

from __future__ import annotations

import pytest

from kernel.entropy import EntropyClassification, EntropyController
from kernel.isolation import ExecutionContext, ExecutionScope, Permission, StateGuard
from kernel.truth import Mutability, TruthGraph, TruthNode, TruthRegistry
from kernel.v04_stabilization import boot_stabilization


class TestTruthLayer:
    def test_truth_node_requires_provenance(self):
        node = TruthNode.create(
            node_id="test:1",
            source="test.source",
            owner="test.owner",
            version="1.0",
            mutability=Mutability.IMMUTABLE,
            payload={"key": "value"},
        )
        assert node.verify_checksum()

    def test_anonymous_write_rejected(self):
        with pytest.raises(ValueError, match="owner"):
            TruthNode.create(
                node_id="x",
                source="s",
                owner="",
                version="1",
                mutability=Mutability.MUTABLE,
            )

    def test_graph_detects_checksum_invalid(self):
        graph = TruthGraph()
        node = TruthNode.create(
            node_id="n1",
            source="s",
            owner="o",
            version="1",
            mutability=Mutability.MUTABLE,
            payload={"a": 1},
        )
        graph.register_node(node)
        # Tamper payload without updating checksum
        bad = TruthNode(
            id=node.id,
            source=node.source,
            owner=node.owner,
            timestamp=node.timestamp,
            checksum=node.checksum,
            version=node.version,
            mutability=node.mutability,
            payload={"a": 2},
        )
        graph.nodes[bad.id] = bad
        conflicts = graph.detect_conflicts()
        assert any(c.conflict_type == "checksum_invalid" for c in conflicts)


class TestEntropyLayer:
    def test_entropy_classification_bands(self):
        assert EntropyController.classify(0.1) == EntropyClassification.STABLE
        assert EntropyController.classify(0.4) == EntropyClassification.ACCEPTABLE
        assert EntropyController.classify(0.6) == EntropyClassification.WARNING
        assert EntropyController.classify(0.8) == EntropyClassification.UNSTABLE

    def test_entropy_compute_bounded(self):
        stab = boot_stabilization()
        report = stab.entropy_controller.compute(stab.truth_graph)
        assert 0.0 <= report.score <= 1.0


class TestIsolationLayer:
    def test_no_execution_without_context(self):
        scope = ExecutionScope()
        with pytest.raises(RuntimeError, match="without ExecutionContext"):
            scope.require_context()

    def test_write_target_enforcement(self):
        ctx = ExecutionContext.create(
            caller="agent.test",
            scope="test",
            permissions={Permission.WRITE},
            write_targets={"memory.kernel"},
        )
        guard = StateGuard()
        assert guard.check_write(ctx, "memory.kernel")
        assert not guard.check_write(ctx, "governance.audit_log")


class TestStabilizationBoot:
    def test_boot_stabilization_snapshot(self):
        stab = boot_stabilization()
        snap = stab.snapshot()
        assert "truth" in snap
        assert "entropy" in snap
        assert "isolation" in snap


class TestTruthRegistry:
    def test_subsystem_registration(self):
        registry = TruthRegistry()
        result = registry.register_memory(
            node_id="recall_baseline",
            owner="memory.kernel",
            version="1.0",
            payload={"op": "recall"},
        )
        assert result.valid
        assert "memory:recall_baseline" in registry.graph.nodes
