"""Constitutional coherence metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.coherence.constitutional_coherence import ConstitutionalCoherence


@dataclass
class ConstitutionalCoherenceMetrics:
    alignment_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"alignment_rate": round(self.alignment_rate, 4)}


def collect_constitutional_coherence_metrics() -> ConstitutionalCoherenceMetrics:
    checker = ConstitutionalCoherence()
    cases = [
        (True, {}),
        (True, {"violations": []}),
        (False, {"violations": ["epistemic_overreach"]}),
    ]
    aligned = sum(
        1
        for compliant, verdict in cases
        if checker.coherent(
            constitutional_compliant=compliant, constitutional_verdict=verdict
        )
    )
    return ConstitutionalCoherenceMetrics(alignment_rate=aligned / len(cases))
