# Gate Dependency Matrix — v070–v077

| Gate | Hard depends on | Soft inherits score from | Regression tests include |
|------|-----------------|--------------------------|-------------------------|
| v070 civilization | v065c external runtime | v065c | v060–v065c |
| v071 reality | v070 gate_pass | v070 civilization score | v070 + stack |
| v072 temporal | v071 gate_pass | v071 reality score | v071 + stack |
| v073 meaning | v072 gate_pass | v072 temporal score | v072 + stack |
| v074 value | v073 gate_pass | v073 meaning score | v073 + stack |
| v075 intent | v074 gate_pass | v074 value score | v074 + stack |
| v076 purpose | v075 gate_pass | v075 intent score | v075 + stack |
| v077 agency | v076 gate_pass | v076 purpose score | v076 + stack |
| **v07x freeze** | all v070–v077 gate_pass | min(v070..v077 scores) | v060–v077 full pytest |

## Failure propagation

If any parent `gate_pass` is false, child combined score still computes but `hard_failures` may accumulate. Freeze aggregate uses **weakest-link** (`min`) across primary scores with threshold **0.95**.
