"""attention.governance — routes Guardian governance signals into attention.

Only the v0.5.1 escalation bridge is reconstructed so far; governed activation
(v0.6.0+) remains to be rebuilt.
"""

from attention.governance.escalation_salience import escalation_boost
from attention.governance.guardian_attention_bridge import GuardianAttentionBridge

__all__ = ["escalation_boost", "GuardianAttentionBridge"]
