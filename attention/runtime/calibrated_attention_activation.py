"""
Calibrated attention activation — confidence-gated kernel submission.

Wraps kernel submission with the v0.5.4 calibration pipeline: every activation
carries a calibrated (never-certain) confidence, and the submitted salience is
weighted down by that confidence so activation can never amplify itself.
"""

from __future__ import annotations

from typing import Any, Optional

from attention.calibration.forecast_confidence import ForecastConfidenceCalibrator
from attention.consolidation.attention_memory import AttentionMemory
from attention.consolidation.attention_memory_store import AttentionMemoryStore
from attention.core.attention_target import AttentionTarget
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.confidence_weighted_salience import ConfidenceWeightedSalience


class CalibratedAttentionActivation:
    """Submits targets into the kernel with calibrated, weighted confidence."""

    def __init__(
        self,
        kernel: Optional[AttentionKernel] = None,
        store: Optional[AttentionMemoryStore] = None,
        calibrator: Optional[ForecastConfidenceCalibrator] = None,
        weighter: Optional[ConfidenceWeightedSalience] = None,
    ) -> None:
        self.kernel = kernel if kernel is not None else AttentionKernel()
        self.store = store
        self.calibrator = calibrator or ForecastConfidenceCalibrator()
        self.weighter = weighter or ConfidenceWeightedSalience()

    def activate_from_memory(
        self,
        memory: AttentionMemory,
        raw_confidence: float = 0.75,
        band_width: float = 0.15,
    ) -> dict[str, Any]:
        """Reactivate a consolidated memory with a calibrated confidence."""
        cal = self.calibrator.calibrate(
            raw_confidence, band_width=band_width, domain=memory.domain
        )
        base_salience = memory.salience_mean or memory.salience_peak
        weighted = self.weighter.weight(base_salience, cal.calibrated)
        target = AttentionTarget(
            source_domain=memory.domain,
            signal_type="calibrated_recall",
            raw_value=weighted.weighted,
            source_ref=memory.target_id,
        )
        submit = self.kernel.submit(target)
        return {
            "target_id": target.target_id,
            "calibrated_confidence": cal.calibrated,
            "weighted_salience": weighted.weighted,
            "accepted": submit.get("accepted", False),
        }

    def submit_calibrated_target(
        self,
        target: AttentionTarget,
        raw_confidence: float = 0.8,
        band_width: float = 0.15,
    ) -> dict[str, Any]:
        """Submit a live target with a calibrated, never-certain confidence."""
        cal = self.calibrator.calibrate(
            raw_confidence, band_width=band_width, domain=target.source_domain
        )
        weighted = self.weighter.weight(target.raw_value, cal.calibrated)
        submit = self.kernel.submit(target)
        return {
            "target_id": target.target_id,
            "calibrated_confidence": cal.calibrated,
            "weighted_salience": weighted.weighted,
            "accepted": submit.get("accepted", False),
        }
