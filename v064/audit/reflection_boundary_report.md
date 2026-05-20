# v0.6.4 Reflection Boundary Report

**Version:** 0.6.4  
**Base:** v0.6.3 coherence-bounded cognition

## Boundaries

| Boundary | Module | Rule |
|----------|--------|------|
| Protected routes | `reflection_boundary.py` | Guardian/ontology core routes not reflectable |
| Introspection depth | `introspection_cap.py` | Max depth 2; window evaluation cap |
| Recursive reflection | `recursive_reflection_guard.py` | Blocks reflection-on-reflection loops |
| Cognition quality | `cognition_quality.py` | Quality floor 0.50 advisory |
| Degradation | `degradation_detector.py` | Sliding-window quality decline detection |
| Attention pathology | `attention_pathology.py` | Fixation, oscillation, budget overrun signals |
| Coherence reflection | `coherence_reflection.py` | Meta-view on coherence verdict only |
| Calibration reflection | `calibration_reflection.py` | Meta-view on calibration posture |

## Governor integration

`CognitiveGovernor._attach_metacognition()` runs **after** coherence evaluation. It is **observational only** — it does not change `accepted`, `governed_salience`, or governance `reason`.

## Non-goals (preserved)

- No consciousness, ego simulation, or autonomous introspection loops
- No recursive self-modification; Guardian supremacy unchanged
- v0.5.0–v0.6.3 stacks preserved
