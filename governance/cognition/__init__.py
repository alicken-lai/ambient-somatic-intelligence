"""
Cognitive Governance Kernel (v0.6.0) — bounded arbitration over attention.

Advisory-only: does not execute actions, weaken Guardian, or form recursive loops.
"""

from governance.cognition.arbitration_engine import ArbitrationEngine, ArbitrationResult
from governance.cognition.cognitive_governor import CognitiveGovernor, GovernanceDecision
from governance.cognition.replay_authority import ReplayAuthority, ReplayAuthorityResult
from governance.cognition.salience_arbitrator import SalienceArbitrator, SalienceClaim
from governance.cognition.somatic_authority import SomaticAuthority, SomaticAuthorityResult
from governance.cognition.sovereignty_limits import SovereigntyLimits, SovereigntyReport
from governance.cognition.uncertainty_override import UncertaintyOverride, UncertaintyOverrideResult

__all__ = [
    "ArbitrationEngine",
    "ArbitrationResult",
    "CognitiveGovernor",
    "GovernanceDecision",
    "ReplayAuthority",
    "ReplayAuthorityResult",
    "SalienceArbitrator",
    "SalienceClaim",
    "SomaticAuthority",
    "SomaticAuthorityResult",
    "SovereigntyLimits",
    "SovereigntyReport",
    "UncertaintyOverride",
    "UncertaintyOverrideResult",
]
