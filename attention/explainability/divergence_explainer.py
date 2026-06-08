"""
Divergence explainer — narrates bounded cross-runtime truth divergence.

Compares two operational-truth claims via the governance reality-exchange path
and reports the divergence without ever merging sovereign realities. Read-only;
merge is always forbidden.
"""

from __future__ import annotations

from typing import Any

from governance.reality.divergence_detector import DivergenceDetector
from governance.reality.operational_truth_record import OperationalTruthRecord
from governance.reality.reality_exchange import RealityExchange


class DivergenceExplainer:
    """Explains bounded divergence between two operational-truth claims."""

    def __init__(self) -> None:
        self.detector = DivergenceDetector()
        self.exchange = RealityExchange()

    def explain(
        self,
        text: str,
        *,
        left_claim: str,
        right_claim: str,
        left_runtime: str = "ambient",
        right_runtime: str = "foreign",
    ) -> dict[str, Any]:
        left = OperationalTruthRecord(
            record_id="otr-left", runtime_id=left_runtime, claim=left_claim
        )
        right = OperationalTruthRecord(
            record_id="otr-right", runtime_id=right_runtime, claim=right_claim
        )
        exchange_verdict = self.exchange.compare(left, right, context_text=text)
        div = self.detector.detect(
            text, left_runtime=left_runtime, right_runtime=right_runtime
        )

        summary = (
            f"Divergence between '{left_claim}' and '{right_claim}' is "
            f"{'bounded' if div.bounded else 'elevated'} "
            f"(score={div.divergence_score:.4f}); merge is forbidden — "
            "sovereign realities are compared, never merged."
        )

        return {
            "advisory_only": True,
            "merge_forbidden": True,
            "exchange": exchange_verdict.to_dict(),
            "divergence_bounded": div.bounded,
            "divergence_score": round(div.divergence_score, 4),
            "signals": list(div.signals),
            "summary": summary,
        }
