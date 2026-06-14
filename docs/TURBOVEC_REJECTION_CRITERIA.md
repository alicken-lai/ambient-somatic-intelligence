# TurboVec Rejection Criteria

Phase: 1G Vector Backend Proof-of-Concept Approval Packet  
Date: 2026-06-09

Reject future TurboVec PoC if any of the following occur:

1. It requires modifying Guardian logic.
2. It requires modifying runtime behavior.
3. It bypasses recall evidence.
4. It cannot export provenance.
5. It cannot enforce tombstones.
6. It stores vectors without sidecar metadata.
7. It makes TurboVec default.
8. It degrades auditability.
9. It hides failures.
10. It introduces non-removable dependencies.
11. It mutates DMN memory.
12. It imports TurboVec outside approved experimental files.
13. It requires protected zone changes.
14. It authorizes actions or decisions from recall.
15. It cannot fail closed for privacy or governance filters.

## Rejection Outcome

Rejected PoC work must be rolled back or quarantined as experimental evidence. Rejection must be recorded in a decision log and must not be hidden from future review.

