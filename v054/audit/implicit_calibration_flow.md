# Implicit Calibration Flow (v0.5.4 audit)

**Base:** v0.5.3-alpha ANTICIPATORY  
**Date:** 2026-05-19

## Flow

1. **Forecast** produces raw `UncertaintyBand.confidence` from v0.5.3 projection.
2. **ForecastConfidenceCalibrator** applies humility decay, FP penalty, and `ConfidenceCap` (max 0.99).
3. **ConfidenceWeightedSalience** multiplies salience by calibrated confidence (no amplification).
4. **CalibratedAttentionActivation** gates kernel submit when calibrated confidence &lt; 0.2.
5. **Observability v054** collects metrics; `CalibrationStabilityScore` gates at 0.90.

## Invariants

- Confidence never reaches 1.0 (`ABSOLUTE_MAX_CONFIDENCE = 0.99`).
- No recursive confidence amplification.
- v0.5.0–v0.5.3 attention stack preserved.
