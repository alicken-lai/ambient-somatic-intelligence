# Independent review: captured-only backup verification and fixed diagnostics

Date: 2026-10-29. Reviewer: `/root/git_release_execution`.
Implementer: `/root/implementation_inventory`.
Scope: the exact frozen source/test graph named below, source inspection and the specified synthetic suite only. The reviewer did not author the changed helper or either new test module. The reviewer authored the unchanged backup bootstrap/caller integration; this review does not re-certify that authored component or its native execution.

## Conclusion

**ACCEPT for the limited source/synthetic scope, confidence 0.94.** No new blocking defect was found in the explicit captured-only mode or allowlisted coverage diagnostics. This is **not** formal G2 acceptance, authority to replay a real backup, proof of live-source coverage, migration/cutover readiness or Release approval. The original failed run remains failed and untouched by this review.

The confidence calculation is evidence 0.95 × 0.40, boundary/edge robustness 0.90 × 0.30, established-behavior alignment 0.95 × 0.20 and scope clarity 1.00 × 0.10 = 0.94. Mocked native boundaries and caller-managed execution conditions remain outside this acceptance.

## Frozen graph independently checked

All eleven graph hashes matched **before and after** the independent synthetic execution.

| File | SHA-256 |
|---|---|
| `scripts/hermes_encrypted_backup.py` | `88e0b110285331862ba741db75e3f9434343a778ceeaa23b59ec9af6b311c33e` |
| `tests/test_hermes_backup_coverage_diagnostics.py` | `9e973bcb8233eab625b69b3736540df44a712a635b4e8385e8bc6be118cffc86` |
| `tests/test_hermes_backup_captured.py` | `4a24a21deb0e85c94649cf3ccec18c63e5b7cb647d76f08bee95096c640b70cf` |
| Existing integration tests | `f0eb778efadb916cc3539ce6bfdb938ebd4e4d449d37011cbbc21a86ce360a88` |
| Existing codec tests | `86474b65070ecee64109fa0472e8071b95f7a7ddb44236542bd15fecbe5ab429` |
| Existing stream verifier | `f9eb5cf39cf6345b0e80ffd3f03d6d0caf841f7db01aa85f1086e1eb80ed4cd1` |
| Existing stream tests | `7d166dffd33359f301d3e846662065f0a43579a6cdea2533bf003b6e6e24954b` |
| Unchanged PS backup caller | `c7f038febc80198151f6fe16b37156fac38a135c87fa3b68c5ec5cbba014295b` |
| Unchanged isolated bootstrap | `7718999c2e8c9981349b39d11b7ae7005ea428e6ba0c6cbb259778734b19da93` |
| Existing bootstrap tests | `d506167a672c6e0c5a066735089170a98add65ef6228d6b47a94655faef535cb` |
| Backup requirements | `eb47723e89132567bc49e845f8c62bc1898db0448133c43d5968122e8e9cf412` |

The two full implementation packets were read. Final packet SHA-256: `05524f701ee58a8c68dae30b282ca72c655351cac7a926ca6cc9a4f86ed658fb`; preceding diagnostics packet SHA-256: `ba84e66a7451dc22ff1abc1bd01827026b5c89e9af987d9deae691f58dda87c7`. The intermediate helper freeze is historical, not the source certified by this review.

## Acceptance separation and source findings

The public `verify_run` interface still selects the original shared body with live checking enabled. The unchanged PS caller still invokes `verify-run`; it does not select or silently fall back to `verify-captured`. Added/mutated live inventory still raises the original failure before restore-root creation. Fixed diagnostics annotate errors without changing exception class/message or successful acceptance paths.

`verify_captured` alone explicitly selects captured-only behavior. The only historical-source path operation is constructing its `Path` object from the unchanged manifest. The live `exists()` call is short-circuited, and `inventory_home()` is not called. Manifest bytes and original source locators are not rewritten to exploit an existence-dependent branch.

Captured success uses `historical_capture_verified`, not plain `ok`. Successful API/CLI results and writable CLI failure reports explicitly declare:

```json
{"verification_scope":"historical_capture_only","historical_only":true,"historical_source_state":"captured_manifest_and_inventory_only","live_coverage":"UNKNOWN","live_source_observed":false,"point_in_time_coherence":"NOT_ESTABLISHED","gate_pass":false}
```

Its nested coverage `complete` is a mapping/completeness statement **against the caller-trusted captured ledger only**; state, basis and `source_remeasured=false` make that limitation explicit. It is not a coherent-point-in-time snapshot or fresh/live-source claim. Legacy HEB1 still needs explicit opt-in and independently supplied manifest-bound plaintext/ciphertext hashes and length; missing legacy inventory returns incomplete/UNKNOWN coverage, not invented completeness.

The shared payload body retains manifest-hash trust binding, contained references, sidecar pins, ACL metadata agreement, required file/DB mapping, HEB2 terminal authentication, report/manifest payload pins, source archive and patch/config parsing, remote/ignored-map integrity and actual in-memory SQLite integrity/schema/user-version checks. Fixed public coverage stage/subcodes are allowlisted; dynamic messages and secret-bearing paths are not emitted. Diagnostics distinguish coverage-manifest, captured-ledger and live-inventory failures; they are not claimed to classify every unrelated parser/crypto/native exception.

## Independent actual synthetic execution

The exact five-module command in the implementation packet was rerun with `ASI_RUN_LARGE_BACKUP_TEST=1` and the existing named dependency paths. The already-known workspace `Path.resolve` visibility restriction was handled by a scoped approved read escalation, not by removing a source guard. No actual private G2 run, production DB/config, live Hermes process or network was used.

- **84 tests, zero failures, zero errors, zero skips; 22.650 seconds; exit 0.**
- Exec session `99054`; retained tool receipts `0c0700`, `e66acf`, `ec8a49`.
- The suite includes the existing 50 codec/stream/synthetic integration cases, 15 diagnostic cases and 19 captured-only cases.
- New tests exercise absent/wrong inventory, required credential omission, contained-reference escapes, ACL metadata mismatch, wrong trusted manifest hash, actual final-frame `InvalidTag`, report-pin conflict, actual in-memory SQLite report mismatch, HEB1 opt-in/hash requirements and historical-only CLI success/failure scope.
- The no-live-probe test rejects historical-home `exists()` access and any `inventory_home` call. The full-mode drift negative actually reaches and rejects the live metadata difference before private restore-root creation.
- Windows ACL and DPAPI interfaces are mocked in these fixtures; those interfaces are not newly certified here. New synthetic temporary fixtures own their cleanup; no historical evidence was deleted.

The real large synthetic SQLite result was **75,894,784 bytes**, configured budget **536,870,912 bytes**, admission estimate **320,356,352 bytes**, Python tracemalloc peak **153,375,281 bytes**, process peak working set **282,103,808 bytes**, elapsed **1.156 seconds**. These are observations, not an OS-enforced hard memory bound or a production-backup result.

## Remaining execution conditions and preserved limitations

1. This library does not itself identify which directory is the original failed run versus a separately authorized isolated copy. A future execution driver must explicitly bind distinct exact roots, byte-identical artifact/key copies, private ACLs, contained references, a new report target and the new verifier source hash. It must not invoke the historical mode in the original evidence root merely because the API permits a path argument.
2. The old producer manifest/helper pin stays unchanged. Any new historical observation must separately identify this new verifier pin; do not replace the producer pin in historical manifests.
3. Native ACL/DPAPI execution and actual executable resolution remain separately scoped checks for a later real execution. This review did not perform them or approve a real replay.
4. The original full verifier already checked live inventory **only when the source exists**. That existing absent-source branch and `source_remeasured=false` are retained, not broadened by this patch. They must never be interpreted by a formal consumer as evidence of fresh/live coverage. The observed current-drift rejection is supported; an unqualified claim that every absent-source situation fails is not.
5. Captured-only authentication cannot establish capture-time coherence, current source coverage, writer closure, a fresh pre-cutover backup or restore-readiness of the live installation. Original G2 failure and the unknown exact historical `INVALID_INPUT` subcause remain preserved. Current drift reproduction does not rewrite that history.
6. Existing parent Git optional-index-refresh and read-only WAL coordination caveats belong to future actual backup planning; this captured verification source task invokes neither production Git nor a production DB connection.

No additional Gate threshold, reinstall requirement, universal OS attestation rule or new protocol criterion is introduced. Formal verifier assignment, all original G0–G6 obligations and any subsequent execution authorization remain with the coordinating workflow. **`gate_pass=false`; `release=false`.**
