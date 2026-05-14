"""Memory Ontology Layer — formal 4-layer memory system for Ambient OS."""

from .layer_definition import MemoryLayer, LayerDefinition, LAYER_REGISTRY
from .episodic_schema import EpisodicEntry
from .instinct_schema import InstinctEntry
from .skill_schema import SkillMemoryEntry
from .strategic_schema import StrategicEntry
from .promotion_rules import PromotionRule, PROMOTION_RULES, check_promotion_eligibility
from .decay_rules import DecayRule, DECAY_RULES, DECAY_RULE_REGISTRY, compute_decay, should_remove
from .confidence_model import ConfidenceUpdate, ConfidenceHistory, ConfidenceModel
from .promotion_engine import PromotionCandidate, PromotionResult, PromotionEngine
from .decay_engine import DecayReport, DecayEngine

__all__ = [
    "MemoryLayer",
    "LayerDefinition",
    "LAYER_REGISTRY",
    "EpisodicEntry",
    "InstinctEntry",
    "SkillMemoryEntry",
    "StrategicEntry",
    "PromotionRule",
    "PROMOTION_RULES",
    "check_promotion_eligibility",
    "DecayRule",
    "DECAY_RULES",
    "DECAY_RULE_REGISTRY",
    "compute_decay",
    "should_remove",
    "ConfidenceUpdate",
    "ConfidenceHistory",
    "ConfidenceModel",
    "PromotionCandidate",
    "PromotionResult",
    "PromotionEngine",
    "DecayReport",
    "DecayEngine",
]
