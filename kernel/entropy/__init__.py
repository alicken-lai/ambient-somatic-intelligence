"""Entropy controller — observable system drift and coupling metrics (SSOT)."""

from kernel.entropy.coupling_pressure import CouplingEdge, CouplingPressure
from kernel.entropy.drift_detector import DriftDetector, DriftObservation
from kernel.entropy.entropy_controller import (
    EntropyClassification,
    EntropyController,
    EntropyReport,
)
from kernel.entropy.entropy_metric import EntropyMetric, MetricKind, MetricSnapshot
from kernel.entropy.mutation_tracker import MutationRecord, MutationTracker
from kernel.entropy.orphan_pressure import ModuleLifecycle, OrphanPressure
from kernel.entropy.patch_entropy_adapter import PatchEntropyAdapter
from kernel.entropy.stale_state_detector import StaleStateDetector, StaleStateReport
from kernel.entropy.truth_entropy_adapter import TruthEntropyAdapter

__all__ = [
    "CouplingEdge",
    "CouplingPressure",
    "DriftDetector",
    "DriftObservation",
    "EntropyClassification",
    "EntropyController",
    "EntropyMetric",
    "EntropyReport",
    "MetricKind",
    "MetricSnapshot",
    "ModuleLifecycle",
    "MutationRecord",
    "MutationTracker",
    "OrphanPressure",
    "PatchEntropyAdapter",
    "StaleStateDetector",
    "StaleStateReport",
    "TruthEntropyAdapter",
]
