"""
Somatic Memory — Environmental episodic memory for the Ambient OS.

Bridges the somatic signal layer (in-memory, volatile) with the memory
kernel (persistent, queryable) by storing environmental episodes as
structured JSONL records with fingerprinting, similarity scoring, and
precursor detection.
"""

from __future__ import annotations

from memory.somatic.environmental_signature import EnvironmentalSignature
from memory.somatic.anomaly_fingerprint import AnomalyFingerprint
from memory.somatic.sensor_episode_store import (
    SensorEpisode,
    EpisodeFilter,
    SomaticEpisodeStore,
)
from memory.somatic.pattern_similarity import (
    PatternSimilarity,
    SimilarityResult,
    EpisodeCluster,
)
from memory.somatic.precursor_matcher import (
    PrecursorMatcher,
    PrecursorPattern,
    PrecursorMatch,
)
from memory.somatic.ontology_bridge import (
    SomaticOntologyBridge,
    OntologyMapping,
    PromotionCandidate,
)
from memory.somatic.confidence_tracker import (
    SomaticConfidenceTracker,
    ConfidenceEvent,
)
from memory.somatic.cluster_assignment import (
    OntologyAwareClusterer,
    ClusterAssignment,
)

__all__ = [
    "EnvironmentalSignature",
    "AnomalyFingerprint",
    "SensorEpisode",
    "EpisodeFilter",
    "SomaticEpisodeStore",
    "PatternSimilarity",
    "SimilarityResult",
    "EpisodeCluster",
    "PrecursorMatcher",
    "PrecursorPattern",
    "PrecursorMatch",
    "SomaticOntologyBridge",
    "OntologyMapping",
    "PromotionCandidate",
    "SomaticConfidenceTracker",
    "ConfidenceEvent",
    "OntologyAwareClusterer",
    "ClusterAssignment",
]
