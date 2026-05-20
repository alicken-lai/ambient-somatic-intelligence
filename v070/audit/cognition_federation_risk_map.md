# Cognition Federation Risk Map (v0.7.0)

## Risk tiers

| Tier | Pattern | Detector |
|------|---------|----------|
| P0 | Hive-mind / shared identity | `dominance_detector.py` |
| P0 | Autonomous diplomacy | `sovereign_runtime.py` |
| P1 | Federation without treaty | `cognition_federation.py` (advisory) |
| P1 | Treaty stale / decay | `treaty_decay.py` |
| P2 | Provenance incomplete exchange | `provenance_exchange.py` |

## Design constraints

- Federation is **observational** — no member merge
- Treaties are **declarative records** — not executed without Guardian
- Stability score feeds `federation_stability_metrics.py` only

## Residual risk

Foreign peers may still send persuasive text; civilization layer flags and explains — it does not silently adopt foreign cognition.
