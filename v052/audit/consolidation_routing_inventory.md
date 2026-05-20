# Consolidation Routing Inventory — v0.5.2

| Route | Source | Target | Bounded |
|-------|--------|--------|---------|
| C1 | `attention_trace` | `salience_history` | ring cap 256 |
| C2 | `salience_history` | `salience_reinforcement` | ceiling 1.0 |
| C3 | `precursor_memory` | `precursor_weighting` | decay applied |
| C4 | `noise_classifier` | `benign_pattern_memory` | max 200 patterns |
| C5 | `attention_memory_store` | `consolidated_attention_activation` | activation cap |
| C6 | `somatic_episode_store` | `environmental_resonance` | max 100 episodes |
| C7 | `runtime_attention_memory_bridge` | `AttentionKernel` | duplicate guard |
| C8 | metrics | `attention_memory_stability_score` | gate 0.90 |

No routes bypass Guardian or rewrite ontology / TruthGraph surfaces.
