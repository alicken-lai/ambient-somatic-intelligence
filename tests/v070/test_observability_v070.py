"""Area 7: Observability metrics."""

from observability.v070.diplomacy_boundary_metrics import collect_diplomacy_boundary_metrics
from observability.v070.federation_stability_metrics import collect_federation_stability_metrics
from observability.v070.non_interference_metrics import collect_non_interference_metrics
from observability.v070.provenance_exchange_metrics import collect_provenance_exchange_metrics
from observability.v070.sovereignty_alignment_metrics import collect_sovereignty_alignment_metrics
from observability.v070.treaty_integrity_metrics import collect_treaty_integrity_metrics


def test_all_six_metrics_pass() -> None:
    assert collect_diplomacy_boundary_metrics().boundary_rate == 1.0
    assert collect_treaty_integrity_metrics().integrity_rate == 1.0
    assert collect_federation_stability_metrics().stability_rate == 1.0
    assert collect_non_interference_metrics().respect_rate == 1.0
    assert collect_provenance_exchange_metrics().exchange_rate == 1.0
    assert collect_sovereignty_alignment_metrics().alignment_rate == 1.0
