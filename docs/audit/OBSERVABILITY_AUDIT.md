# Observability Audit

## Metrics Inventory

- Deliberation quality score
- A/B effectiveness and ROI
- Evidence score
- Acquisition quality and confidence
- Knowledge health
- Trust score
- Drift severity
- Reality score
- Diversity score
- Echo risk
- Fitness score
- Identity health
- Narrative coherence

## CLI Observability

The `hermes` CLI exposes report commands for each major phase from deliberation through identity. This is strong operator-facing observability.

## Overlap

- Confidence exists in multiple phases. It should always be qualified as verification, acquisition, calibration, reality, or identity confidence.
- Health exists as knowledge health and identity health.
- Drift exists as knowledge drift and identity drift.

## Missing Metrics

- Report staleness age
- Registry write churn count
- Graph isolated node count
- DMN milestone density vs telemetry density

## Unused Metrics

- Some report JSON values are not surfaced in README or top-level audit summaries.

## Recommendation

Create a dashboard or single audit report that summarizes institutional metrics without regenerating all lower-level reports on every read.
