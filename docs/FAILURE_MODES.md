# Deliberation Failure Modes

## Shared Hallucination

Symptoms: children independently repeat the same unsupported claim.
Detection: judge marks shared blindspots and verifier leaves claims `not_checked` or `unsupported`.
Mitigation: require allowed-tool evidence before increasing confidence.

## Majority Hallucination

Symptoms: most children agree, but none cite evidence.
Detection: consensus rises while verification coverage stays low.
Mitigation: judge must not treat majority as truth; verifier status remains authoritative.

## Judge Bias

Symptoms: judge prefers polished answers over better-evidenced answers.
Detection: unique insights or unsupported claims are dropped from synthesis.
Mitigation: schema tests require consensus, disagreements, unsupported claims, and blindspots.

## Verification Failure

Symptoms: verifier cannot check a claim but final answer presents it as certain.
Detection: `not_checked` claims appear with high confidence.
Mitigation: synthesizer preserves uncertainty and metrics increase hallucination-risk score.

## Tool Failure

Symptoms: allowed checks fail because tool output is missing, malformed, or unavailable.
Detection: verifier evidence notes show no allowed-tool evidence.
Mitigation: mark claims `not_checked`; do not fabricate sources.

## Provider Timeout

Symptoms: CLI health check or invocation exceeds timeout.
Detection: provider health is `timeout` or result error type is `timeout`.
Mitigation: mandatory subprocess timeouts and fallback to Copilot-only governance.

## Provider Drift

Symptoms: CLI behavior, model identity, or bridge contract changes.
Detection: golden trace score regressions and provider discovery version changes.
Mitigation: keep providers disabled until health checked and explicitly configured.

## Trace Corruption

Symptoms: trace is missing task, route, stage outputs, timestamp, or trace id.
Detection: trace integrity tests and decision trace completeness metric.
Mitigation: fail regression tests and avoid promoting incomplete traces.

## Guardian Bypass Attempts

Symptoms: file mutation, shell execution, provider changes, memory writes, credential access, network exposure, deployment, delete operations, or repo-wide refactors proceed without Guardian review.
Detection: Guardian audit suite checks risky task classes.
Mitigation: route to `guardian_required`, attach Guardian result to trace, and block execution until approved.
