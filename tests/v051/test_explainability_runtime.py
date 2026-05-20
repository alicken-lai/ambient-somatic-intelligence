"""Area 6: runtime explainability."""

from attention.explainability.runtime_attention_explainer import RuntimeAttentionExplainer
from attention.explainability.runtime_salience_breakdown import runtime_breakdown_summary
from attention.core.salience import SalienceVector


def test_runtime_explainer(somatic_target, runtime_kernel) -> None:
    expl = RuntimeAttentionExplainer(runtime_kernel)
    out = expl.explain_target(somatic_target)
    assert out["total"] >= 0.0
    assert out["runtime_summary"]["opaque"] is False


def test_breakdown_summary() -> None:
    vec = SalienceVector("t1", {"urgency": 0.8, "novelty": 0.3})
    s = runtime_breakdown_summary(vec)
    assert s["factor_count"] >= 1
