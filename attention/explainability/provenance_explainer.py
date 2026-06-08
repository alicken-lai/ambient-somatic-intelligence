"""
Provenance explainer — narrates a cognition ProvenanceRecord.

Explains where a cognition pathway came from and whether it is trusted, using
the canonical trust rule (is_trusted_cognition). Advisory and non-ontological:
provenance labels describe origin, they do not assert consciousness or autonomy.
"""

from __future__ import annotations

from typing import Any

from governance.identity.trusted_cognition import is_trusted_cognition


class ProvenanceExplainer:
    """Transparent breakdown of a single provenance record."""

    def explain_record(self, record: Any) -> dict[str, Any]:
        origin_obj = getattr(record, "origin", None)
        origin = getattr(origin_obj, "value", str(origin_obj))
        is_live = bool(getattr(origin_obj, "is_live", False))
        corrupted = bool(getattr(record, "corrupted", False))
        prov_conf = float(getattr(record, "provenance_confidence", 0.0))
        route_name = str(getattr(record, "route_name", ""))

        trusted = is_trusted_cognition(record)

        summary = (
            f"Cognition originated from '{origin}' via route '{route_name}' "
            f"(provenance_confidence={prov_conf:.4f}, trusted={trusted}, "
            f"corrupted={corrupted}). Advisory provenance label, not an ontological claim."
        )

        return {
            "advisory_only": True,
            "origin": origin,
            "is_live": is_live,
            "route_name": route_name,
            "provenance_confidence": round(prov_conf, 4),
            "corrupted": corrupted,
            "trusted": trusted,
            "summary": summary,
        }
