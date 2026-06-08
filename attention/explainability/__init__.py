"""attention.explainability — transparent breakdowns of attention decisions."""

from attention.explainability.explain_attention import (
    AttentionBreakdown,
    AttentionExplanation,
    BreakdownNode,
    explain_attention,
)
from attention.explainability.runtime_attention_explainer import (
    RuntimeAttentionExplainer,
)
from attention.explainability.runtime_salience_breakdown import (
    runtime_breakdown_summary,
)
from attention.explainability.consolidation_explainer import ConsolidationExplainer
from attention.explainability.noise_suppression_explainer import (
    NoiseSuppressionExplainer,
)
from attention.explainability.precursor_reinforcement_report import (
    PrecursorReinforcementReport,
)
from attention.explainability.uncertainty_explainer import UncertaintyExplainer
from attention.explainability.forecast_explainer import ForecastExplainer
from attention.explainability.precursor_chain_explainer import PrecursorChainExplainer
from attention.explainability.calibration_explainer import CalibrationExplainer
from attention.explainability.confidence_breakdown import (
    ConfidenceBreakdown,
    ConfidenceBreakdownBuilder,
)
from attention.explainability.uncertainty_reasoning import UncertaintyReasoning

__all__ = [
    "explain_attention",
    "AttentionExplanation",
    "AttentionBreakdown",
    "BreakdownNode",
    "RuntimeAttentionExplainer",
    "runtime_breakdown_summary",
    "ConsolidationExplainer",
    "NoiseSuppressionExplainer",
    "PrecursorReinforcementReport",
    "UncertaintyExplainer",
    "ForecastExplainer",
    "PrecursorChainExplainer",
    "CalibrationExplainer",
    "ConfidenceBreakdown",
    "ConfidenceBreakdownBuilder",
    "UncertaintyReasoning",
]
