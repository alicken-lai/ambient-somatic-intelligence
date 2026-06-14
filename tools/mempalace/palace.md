# MemPalace

- generated_at: 2026-06-13T23:32:07.775838+00:00
- node_count: 9
- link_count: 5
- corrective_actions: none
- response_mode: recommendations only

## system_health

- event_id: simulation:2026-06-13T23:31:54.108534+00:00
- timestamp: 2026-06-13T23:31:54.108534+00:00
- anomaly_type: review
- confidence: 0.6
- explanation: Simulation predicts memory pressure remains the primary driver over 2h.
- linked_events: ["observability\\snapshots\\telemetry-2026-06-13T233017.792275Z0000.json"]
- lessons: ["Use simulation horizons to prioritize review before drift compounds."]

## memory_pressure

- event_id: guardian\incidents\incident-2026-05-11T214902.702883Z0000.md
- timestamp: 2026-05-11T21:49:02.702891+00:00
- anomaly_type: high_memory_usage
- confidence: None
- explanation: Review memory pressure and avoid launching additional heavy local tasks.
- linked_events: ["observability/snapshots/telemetry-2026-05-11T133644.338636Z0000.json"]
- lessons: ["Review memory pressure and avoid launching additional heavy local tasks."]

- event_id: guardian\incidents\incident-2026-05-11T221437.780998Z0000.md
- timestamp: 2026-05-11T22:14:37.781007+00:00
- anomaly_type: high_memory_usage
- confidence: 0.1
- explanation: Review memory pressure and avoid launching additional heavy local tasks.
- linked_events: ["observability/snapshots/telemetry-2026-05-11T215712.348987Z0000.json"]
- lessons: ["Review memory pressure and avoid launching additional heavy local tasks."]

## docker_runtime

- event_id: docker:2026-06-13T23:31:59.634150+00:00
- timestamp: 2026-06-13T23:31:59.634150+00:00
- anomaly_type: runtime_context
- confidence: 0.1
- explanation: Docker runtime remained lightly loaded while the memory-scoring artifact persisted.
- linked_events: ["guardian\\incidents\\incident-2026-05-11T214902.702883Z0000.md","guardian\\incidents\\incident-2026-05-11T221437.780998Z0000.md"]
- lessons: ["Keep docker runtime context attached to memory-pressure events."]

## guardian_reflex

- event_id: queue:guardian\incidents\incident-2026-05-11T214902.702883Z0000.md
- timestamp: 2026-06-13T23:31:57.172730+00:00
- anomaly_type: high_memory_usage
- confidence: 0.15
- explanation: Keep reflex confidence conservative, but escalate repeated memory warnings to review.
- linked_events: ["dream_candidate=guardian\\dreams\\latest_dream.json","incident=guardian\\incidents\\incident-2026-05-11T214902.702883Z0000.md","rule=high_memory_usage","incident_count=2","repeated_anomaly_types={\"high_memory_usage\":2}","confidence_classes={\"low_confidence_watch\":1}","latest_reflex_confidence=0.1","calibration_latest_rule=high_memory_usage"]
- lessons: ["Treat recalibration as review-only until approval is granted."]

- event_id: queue:guardian\incidents\incident-2026-05-11T221437.780998Z0000.md
- timestamp: 2026-06-13T23:31:57.172730+00:00
- anomaly_type: high_memory_usage
- confidence: 0.2
- explanation: Lower confidence for this rule family and treat the warning as artifact-prone.
- linked_events: ["dream_candidate=guardian\\dreams\\latest_dream.json","incident=guardian\\incidents\\incident-2026-05-11T221437.780998Z0000.md","rule=high_memory_usage","incident_count=2","repeated_anomaly_types={\"high_memory_usage\":2}","confidence_classes={\"low_confidence_watch\":1}","latest_reflex_confidence=0.1","calibration_latest_rule=high_memory_usage"]
- lessons: ["Treat recalibration as review-only until approval is granted."]

## visual_layer

- event_id: dream-brief:2026-06-13T23:31:56.372441+00:00
- timestamp: 2026-06-13T23:31:56.372441+00:00
- anomaly_type: narrative_replay
- confidence: 0.1
- explanation: The reflection and briefing surfaces preserve a readable replay of prior state.
- linked_events: ["docs\\reflections\\latest.md"]
- lessons: ["Keep human-readable summaries synchronized with the underlying state."]

- event_id: reflection:2026-06-13T23:31:59.634150+00:00
- timestamp: 2026-06-13T23:31:59.634150+00:00
- anomaly_type: self_reflection
- confidence: 0.1
- explanation: Self-reflection carries the current watch posture and the memory-pressure narrative.
- linked_events: ["docs\\reflections\\latest.md"]
- lessons: ["Keep self-reflection aligned with the latest operator briefing and anomaly explanation."]

## operator_decisions

- event_id: dream:2026-06-13T23:31:56.372441+00:00
- timestamp: 2026-06-13T23:31:56.372441+00:00
- anomaly_type: recalibration_candidate
- confidence: 0.2
- explanation: Dream replay surfaced recalibration candidates for repeated memory warnings.
- linked_events: ["guardian\\incidents\\incident-2026-05-11T214902.702883Z0000.md","guardian\\incidents\\incident-2026-05-11T221437.780998Z0000.md"]
- lessons: ["Queue repeated rule-family observations for review before changing calibration."]

## Links

- {"domain":"memory_pressure","relation":"same_domain","source":"guardian\\incidents\\incident-2026-05-11T214902.702883Z0000.md","target":"guardian\\incidents\\incident-2026-05-11T221437.780998Z0000.md"}
- {"domain":"guardian_reflex","relation":"same_domain","source":"queue:guardian\\incidents\\incident-2026-05-11T214902.702883Z0000.md","target":"queue:guardian\\incidents\\incident-2026-05-11T221437.780998Z0000.md"}
- {"domain":"visual_layer","relation":"same_domain","source":"dream-brief:2026-06-13T23:31:56.372441+00:00","target":"reflection:2026-06-13T23:31:59.634150+00:00"}
- {"domain":"memory_pressure","relation":"cross_domain_echo","source":"guardian\\incidents\\incident-2026-05-11T214902.702883Z0000.md","target":"guardian\\incidents\\incident-2026-05-11T214902.702883Z0000.md"}
- {"domain":"memory_pressure","relation":"cross_domain_echo","source":"guardian\\incidents\\incident-2026-05-11T221437.780998Z0000.md","target":"guardian\\incidents\\incident-2026-05-11T221437.780998Z0000.md"}

## Sources

- incidents: guardian\incidents\index.json
- patterns: guardian\incidents\index.json
- simulations: guardian\simulations\latest_simulation.json
- dreams: guardian\dreams\latest_dream.json
- recalibration_queue: guardian\recalibration\queue.json
- self_reflections: docs\reflections\latest.md
