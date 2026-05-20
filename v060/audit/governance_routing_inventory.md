# Governance Routing Inventory (v0.6.0)

| Route | Component | Depth | Side effects |
|-------|-----------|-------|--------------|
| `attention_submit` | CognitiveGovernor.govern_target | 1 | None (advisory) |
| `salience_arbitration` | SalienceArbitrator.arbitrate | 1 | None |
| `governance_on_governance` | BLOCKED | — | Recursive loop forbidden |
| `cognitive_self_loop` | BLOCKED | — | Recursive loop forbidden |
| `governed_kernel_submit` | GovernedAttentionActivation | 2 | Kernel submit only |

## Integration points

- `attention/runtime/governed_attention_activation.py` — wraps calibrated path
- `attention/governance/guardian_attention_bridge.py` — unchanged (read-only Guardian map)
- `governance/mandatory_gate.py` — unchanged (execution gate separate from cognition)
