# v0.6.4 Degradation & Pathology Map

| Signal | Detector | Pressure threshold | Explainability |
|--------|----------|-------------------|----------------|
| Quality decline | `degradation_detector.py` | ≥ 0.35 degrading | `degradation_explainer.py` |
| Attention fixation | `attention_pathology.py` | low entropy + high submissions | `reflection_breakdown.py` |
| Attention oscillation | `attention_pathology.py` | high entropy + high submissions | `reflection_breakdown.py` |
| Budget overrun | `attention_pathology.py` | overrun flag | `metacognitive_reasoning.py` |
| Opaque salience cluster | `attention_pathology.py` | count > 2 | `reflection_breakdown.py` |
| Calibration drift | `calibration_reflection.py` | fp/cap pressure | `metacognitive_reasoning.py` |
| Coherence misalignment | `coherence_reflection.py` | low coherence score | `metacognitive_reasoning.py` |

All signals are **advisory** and feed `MetaCognitiveStabilityScore` only.
