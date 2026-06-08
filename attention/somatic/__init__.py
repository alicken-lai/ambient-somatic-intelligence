"""attention.somatic — bridges the somatic subsystem into the attention layer.

Spans the kernel adapter (v050), episode store and resonance (v052), forecast
projections (v053), confidence calibration (v054), and the live runtime
submission path (v051).
"""

from attention.somatic.environmental_resonance import (
    EnvironmentalResonance,
    ResonanceResult,
)
from attention.somatic.environmental_risk_projection import (
    RISK_CEILING,
    EnvironmentalRiskProjector,
    RiskProjection,
)
from attention.somatic.environmental_uncertainty import (
    UNCERTAINTY_FLOOR,
    EnvironmentalUncertainty,
    UncertaintyReport,
)
from attention.somatic.precursor_reliability import (
    PrecursorReliability,
    ReliabilityScore,
)
from attention.somatic.precursor_resonance_forecast import (
    PrecursorResonanceForecaster,
    PrecursorResonanceProjection,
)
from attention.somatic.runtime_somatic_attention import RuntimeSomaticAttention
from attention.somatic.somatic_attention_adapter import SomaticAttentionAdapter
from attention.somatic.somatic_confidence import (
    SomaticConfidence,
    SomaticConfidenceCalibrator,
)
from attention.somatic.somatic_episode import SomaticEpisode
from attention.somatic.somatic_episode_store import SomaticEpisodeStore
from attention.somatic.somatic_forecast import SomaticForecast, SomaticForecastPoint
from attention.somatic.somatic_runtime_bridge import SomaticRuntimeBridge

__all__ = [
    "EnvironmentalResonance",
    "ResonanceResult",
    "EnvironmentalRiskProjector",
    "RiskProjection",
    "RISK_CEILING",
    "EnvironmentalUncertainty",
    "UncertaintyReport",
    "UNCERTAINTY_FLOOR",
    "PrecursorReliability",
    "ReliabilityScore",
    "PrecursorResonanceForecaster",
    "PrecursorResonanceProjection",
    "RuntimeSomaticAttention",
    "SomaticAttentionAdapter",
    "SomaticConfidence",
    "SomaticConfidenceCalibrator",
    "SomaticEpisode",
    "SomaticEpisodeStore",
    "SomaticForecast",
    "SomaticForecastPoint",
    "SomaticRuntimeBridge",
]
