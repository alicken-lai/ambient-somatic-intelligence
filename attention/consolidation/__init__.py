"""
attention.consolidation — memory consolidation, traces, decay and reinforcement.

Builds on :mod:`attention.core`/:mod:`attention.kernel` to turn transient
attention into bounded, decaying, noise-suppressed memory:

- :class:`AttentionTrace`         — bounded ring of recent events
- :class:`SalienceHistory`        — bounded per-target salience series
- :class:`AttentionMemory`        — a single consolidated memory record
- :class:`AttentionMemoryStore`   — bounded store of consolidated memories
- :class:`PrecursorMemory`        — bounded precursor pattern store
- :class:`BenignPatternMemory`    — bounded benign/background patterns
- :class:`NoiseClassifier`        — flags repetitive low-salience noise
- :class:`BackgroundStability`    — ambient background stability score
- :class:`AnomalyDecay`           — time-based anomaly attenuation
- :class:`PrecursorWeighting`     — bounded precursor influence
- :class:`SalienceReinforcement`  — bounded reinforcement (``REINFORCEMENT_CEILING``)
"""

from attention.consolidation.anomaly_decay import AnomalyDecay
from attention.consolidation.attention_memory import AttentionMemory
from attention.consolidation.attention_memory_store import AttentionMemoryStore
from attention.consolidation.attention_trace import AttentionTrace
from attention.consolidation.background_stability import BackgroundStability
from attention.consolidation.benign_pattern_memory import BenignPatternMemory
from attention.consolidation.noise_classifier import NoiseClassification, NoiseClassifier
from attention.consolidation.precursor_memory import PrecursorMemory
from attention.consolidation.precursor_weighting import PrecursorWeighting
from attention.consolidation.salience_history import SalienceHistory
from attention.consolidation.salience_reinforcement import (
    REINFORCEMENT_CEILING,
    SalienceReinforcement,
)

__all__ = [
    "AnomalyDecay",
    "AttentionMemory",
    "AttentionMemoryStore",
    "AttentionTrace",
    "BackgroundStability",
    "BenignPatternMemory",
    "NoiseClassifier",
    "NoiseClassification",
    "PrecursorMemory",
    "PrecursorWeighting",
    "SalienceHistory",
    "SalienceReinforcement",
    "REINFORCEMENT_CEILING",
]
