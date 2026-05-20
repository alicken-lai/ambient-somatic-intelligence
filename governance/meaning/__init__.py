"""Semantic meaning governance — bounded interpretive continuity without frozen ontology."""

from governance.meaning.semantic_continuity import SemanticContinuity, SemanticContinuityVerdict
from governance.meaning.semantic_continuity_observability import (
    SemanticContinuityObservability,
    observe_semantic_continuity,
)

__all__ = [
    "SemanticContinuity",
    "SemanticContinuityVerdict",
    "SemanticContinuityObservability",
    "observe_semantic_continuity",
]
