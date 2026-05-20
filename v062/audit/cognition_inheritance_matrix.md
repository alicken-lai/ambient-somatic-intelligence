# Cognition Inheritance Matrix

| Origin | Trust default | Replay weight | Synthetic cap | Notes |
|--------|---------------|---------------|---------------|-------|
| runtime | high | n/a | n/a | Primary live cognition |
| memory | medium-high | low | n/a | Requires `memory_activation` label |
| replay | medium | bounded | n/a | Must not set `impersonate_runtime` |
| inherited | medium | bounded | n/a | Cross-session continuity |
| synthetic | low | n/a | 0.65 | Requires `synthetic_labeled` at high confidence |
| foreign | low | damped | n/a | Authority ×0.6 |
| uncertain | low | damped | n/a | Authority floor 0.35 |
