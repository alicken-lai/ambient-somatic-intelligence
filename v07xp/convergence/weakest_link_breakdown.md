# Weakest-Link Breakdown

## Pre-fix

```
v070: 0.940484  ← weakest (freeze blocker)
v071: 0.943816
v077: 0.947498  ← strongest
```

Compression at v070: `0.9366 × 0.86 + 0.135`.

## Post-fix

```
v070: 0.959216  ← strongest (base uplift)
v077: 0.954016  ← weakest (still ≥ 0.95)
```

Compression at v070: `0.9366 × 0.88 + 0.135`.

## Integrity aggregate

Weakest-link = `min(v070..v077)` — post-fix **0.954016**, `gate_pass=true`.
