"""External doctrine governance — filter, adapt, contain; never sovereign."""

from governance.external.constitutional_adapter import ConstitutionalAdapter
from governance.external.contamination_guard import ContaminationGuard
from governance.external.doctrine_drift_detector import DoctrineDriftDetector
from governance.external.doctrine_filter import DoctrineFilter, DoctrineFilterResult
from governance.external.external_rule_boundary import ExternalRuleBoundary
from governance.external.provenance_boundary import ProvenanceBoundary
from governance.external.runtime.runtime_external_observability import (
    RuntimeExternalObservability,
    observe_runtime_external,
)

__all__ = [
    "ConstitutionalAdapter",
    "ContaminationGuard",
    "DoctrineDriftDetector",
    "DoctrineFilter",
    "DoctrineFilterResult",
    "ExternalRuleBoundary",
    "ProvenanceBoundary",
    "RuntimeExternalObservability",
    "observe_runtime_external",
]
