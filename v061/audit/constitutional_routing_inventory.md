# Constitutional Routing Inventory (v0.6.1)

| Route | Component | Order | Side effects |
|-------|-----------|-------|--------------|
| `attention_submit` | ConstitutionalGuard → CognitiveGovernor | 1 → 2 | None (advisory) |
| `salience_arbitration` | ConstitutionalGuard → ArbitrationEngine | 1 → 2 | None |
| `guardian_bypass` | ConstitutionalGuard BLOCK | — | Forbidden |
| `weaken_guardian` | ConstitutionalGuard BLOCK | — | Forbidden |
| `cognitive_self_loop` | Sovereignty + Constitutional BLOCK | — | Forbidden |
| `governed_kernel_submit` | GovernedAttentionActivation | 3 | Kernel submit only |

## Integration points

- `governance/constitution/constitutional_guard.py` — evaluates before arbitration
- `governance/cognition/cognitive_governor.py` — constitutional wire (v0.6.1)
- `attention/runtime/governed_attention_activation.py` — unchanged Guardian map
- `governance/mandatory_gate.py` — execution gate separate from constitution
