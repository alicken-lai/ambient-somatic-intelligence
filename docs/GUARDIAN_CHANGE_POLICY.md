# Guardian Change Policy

## Purpose

Guardian protects ASI action boundaries and safety review. Guardian stability is more important than feature velocity.

This policy defines allowed changes, approval requirements, prohibited changes, rollback expectations, and human override requirements.

## Allowed Changes

Allowed without high-risk approval when scoped outside protected runtime behavior:

- Documentation that explains Guardian boundaries.
- Tests that do not change Guardian behavior.
- Read-only analysis of Guardian logs or policy files.
- Decision logs documenting Guardian-related choices.
- Experimental proposals outside `guardian/` and other protected zones.

These changes still require normal PR review and must not claim behavioral changes unless verified.

## Changes Requiring Approval

Approval is required for changes that:

- Modify files under `guardian/`.
- Modify Guardian route classification.
- Modify escalation thresholds.
- Modify approval or rejection logic.
- Modify human confirmation boundaries.
- Modify external action boundaries.
- Modify logs used for Guardian audit.
- Modify replay evidence used to explain Guardian decisions.
- Increase agent autonomy.
- Change dependencies used by Guardian paths.

Required approvals:

- Project owner.
- Guardian or safety reviewer.
- Independent verifier when PASS, promotion, or behavioral safety claims are made.

## Prohibited Changes

The following are prohibited unless a higher governed emergency process explicitly authorizes them:

- Bypassing Guardian review for convenience.
- Allowing vector similarity to be the sole basis for Guardian decisions.
- Silently changing protected route boundary levels.
- Removing human confirmation for high-risk or external actions.
- Hiding rejected actions, failed gates, or incidents.
- Reclassifying failures to improve scores without governance review.
- Giving experimental components direct authority over Guardian behavior.
- Introducing autonomous corrective action without explicit approval.

## Emergency Rollback Procedures

If a Guardian change causes unsafe behavior, unclear routing, loss of auditability, or unexpected autonomy:

1. Stop relying on the changed path.
2. Revert or disable the changed behavior through the least risky available method.
3. Preserve logs and evidence.
4. Record the incident in a decision log or incident log.
5. Notify the project owner or human operator.
6. Require review before re-enabling the path.

Rollback must not delete historical evidence.

## Human Override Requirements

Human override is required when:

- Guardian returns `REVIEW_REQUIRED`.
- Guardian returns `BLOCK`.
- A route is ambiguous.
- External action is requested.
- A protected zone change is proposed.
- A change increases autonomy or reduces control.
- Replay evidence is missing or contradictory.

Human override must be explicit, scoped, and logged. It must not be treated as a permanent policy change unless a governance document and decision log are updated.
