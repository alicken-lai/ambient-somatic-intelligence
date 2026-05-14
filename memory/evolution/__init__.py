"""
Memory-Guided Evolution — Mine execution patterns, learn from incidents,
and propose system optimizations based on historical evidence.

Subsystem: memory/evolution
Phase: C (Ambient OS v0.3)

Modules:
    pattern_miner          — Mine success/failure patterns from execution history
    incident_learner       — Learn from governance incidents and decisions
    optimization_proposer  — Generate candidate optimization proposals
    orchestration_templates — Store and retrieve reusable orchestration templates
    efficiency_reporter    — Generate comprehensive efficiency reports
"""

from memory.evolution.pattern_miner import (
    PatternMiner,
    SuccessPattern,
    FailurePattern,
    MemoryPatterns,
)
from memory.evolution.incident_learner import (
    IncidentLearner,
    IncidentAnalysis,
    DecisionAnalysis,
)
from memory.evolution.optimization_proposer import (
    OptimizationProposer,
    OptimizationProposal,
    ProposalType,
    ImpactLevel,
)
from memory.evolution.orchestration_templates import (
    OrchestrationTemplateStore,
    OrchestrationTemplate,
)
from memory.evolution.efficiency_reporter import (
    EfficiencyReporter,
    EfficiencyReport,
)

__all__ = [
    "PatternMiner",
    "SuccessPattern",
    "FailurePattern",
    "MemoryPatterns",
    "IncidentLearner",
    "IncidentAnalysis",
    "DecisionAnalysis",
    "OptimizationProposer",
    "OptimizationProposal",
    "ProposalType",
    "ImpactLevel",
    "OrchestrationTemplateStore",
    "OrchestrationTemplate",
    "EfficiencyReporter",
    "EfficiencyReport",
]
