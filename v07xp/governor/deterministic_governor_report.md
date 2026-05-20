# Deterministic Governor Report

**Cycles:** 1000 (×2 replay sequences)  
**Tool:** `v07xp/governor/stress_governor.py`

## Result

| Check | Status |
|-------|--------|
| Replay determinism (A == B) | **PASS** |
| `accepted` stable | **PASS** (single value across cycles) |
| Salience range | 0.115 – 0.192 (expected rotation across 3 targets) |

Governor outputs are **reproducible** for identical target sequences; salience variation reflects intentional multi-target stress, not nondeterministic RNG.
