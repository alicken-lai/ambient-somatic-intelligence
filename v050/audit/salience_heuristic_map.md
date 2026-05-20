# Salience Heuristic Map — v0.5.0 (10 dimensions)

| Dimension | Weight | Primary heuristic | Legacy mapping |
|-----------|--------|-------------------|----------------|
| urgency | 0.12 | metadata.urgency or raw×0.8 | operator_priority (partial) |
| anomaly | 0.12 | raw_value | anomaly_level |
| recurrence | 0.08 | log decay on occurrence count | recurrence |
| precursor_similarity | 0.10 | precursor registry / metadata | historical_similarity (partial) |
| somatic_severity | 0.10 | aggregate stress + adapter | somatic_stress |
| memory_relevance | 0.10 | recall hook / metadata | memory_relevance |
| governance_importance | 0.12 | domain + governance_relevant | governance_urgency |
| uncertainty | 0.08 | metadata.uncertainty (default 0.3) | — |
| temporal_proximity | 0.08 | exp decay on age (60s half) | temporal_decay |
| cross_domain_convergence | 0.10 | distinct domains per target | novelty (partial) |

**Composite:** weighted sum, clamped [0, 1].

**Explainability:** `attention/explainability/salience_breakdown.py` exposes per-dimension contribution.

**Gate:** `AttentionStabilityScore` ≥ 0.90 with zero hard failures.
