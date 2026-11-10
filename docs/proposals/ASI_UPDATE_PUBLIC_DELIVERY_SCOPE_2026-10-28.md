# ASI update public delivery scope — 2026-10-28

Updated 2026-10-29. This is a proposed public engineering-source scope, not a
staging receipt, commit, runtime Release, Gate assignment or replacement
protocol. The actual private G2 attempt ended FAIL; the later G3 synthetic
observations have limited independent ACCEPT while complete G3 remains
INCONCLUSIVE. Explicit captured-only verification has source/synthetic review;
its separate isolated-copy execution worker is still under review. No actual
captured-only replay or formal migration/cutover/Release is claimed here.

## Exact candidate files

| File | Purpose |
|---|---|
| [scripts/g0_bounded_capture.py](../../scripts/g0_bounded_capture.py) | Bounded capture helper; operational entry point disabled |
| [scripts/g0_writer_reconciliation.py](../../scripts/g0_writer_reconciliation.py) | Synthetic observation reconciliation |
| [scripts/g0_windows_snapshot.ps1](../../scripts/g0_windows_snapshot.ps1) | Windows snapshot source, with explicit UNKNOWN limits |
| [scripts/test_g0_bounded_capture.py](../../scripts/test_g0_bounded_capture.py) | Fake capture lifecycle regressions |
| [scripts/test_g0_windows_snapshot.ps1](../../scripts/test_g0_windows_snapshot.ps1) | Synthetic snapshot regressions |
| [tests/test_g0_writer_reconciliation.py](../../tests/test_g0_writer_reconciliation.py) | Synthetic reconciliation regressions |
| [scripts/hermes_encrypted_backup.py](../../scripts/hermes_encrypted_backup.py) | Versioned encrypted backup and verification |
| [scripts/hermes_heb2_stream_verify.py](../../scripts/hermes_heb2_stream_verify.py) | Authenticated HEB2 stream verification |
| [scripts/backup_hermes_for_upgrade.ps1](../../scripts/backup_hermes_for_upgrade.ps1) | Explicit HEB2 backup caller; full verification only, no captured fallback |
| [scripts/requirements-hermes-backup.txt](../../scripts/requirements-hermes-backup.txt) | Tested backup dependency versions |
| [tests/test_hermes_encrypted_backup_codec.py](../../tests/test_hermes_encrypted_backup_codec.py) | Framing and legacy pin regressions |
| [tests/test_hermes_heb2_stream_verify.py](../../tests/test_hermes_heb2_stream_verify.py) | Streaming authentication regressions |
| [tests/test_hermes_encrypted_backup_integration.py](../../tests/test_hermes_encrypted_backup_integration.py) | Synthetic SQLite, child and manifest integration |
| [scripts/hermes_backup_bootstrap.py](../../scripts/hermes_backup_bootstrap.py) | Explicit pinned isolated dependency bootstrap |
| [scripts/hermes_backup_preflight.py](../../scripts/hermes_backup_preflight.py) | Dependency/helper syntax and crypto/YAML preflight |
| [tests/test_hermes_backup_bootstrap.py](../../tests/test_hermes_backup_bootstrap.py) | Isolated import, pins and argv regressions |
| [scripts/test_backup_hermes_bootstrap.ps1](../../scripts/test_backup_hermes_bootstrap.ps1) | Fake-only six-route caller/preflight regressions |
| [scripts/test_backup_hermes_private_acl.ps1](../../scripts/test_backup_hermes_private_acl.ps1) | Fake-only new-run ACL and parent-preservation regressions |
| [tests/test_hermes_backup_coverage_diagnostics.py](../../tests/test_hermes_backup_coverage_diagnostics.py) | Fixed error stages and unchanged live-drift refusal |
| [tests/test_hermes_backup_captured.py](../../tests/test_hermes_backup_captured.py) | Explicit historical-only integrity and scope regressions |

The twenty source/test files above and these four public documents form the
exact **24-file candidate allowlist**:

- this delivery-scope file;
- [implementation status](ASI_UPDATE_IMPLEMENTATION_STATUS_2026-10-28.md);
- [G3 doctor read-only interpretation](ASI_G3_DOCTOR_READONLY_DIAGNOSIS_2026-10-29.md);
- [captured-only independent source/synthetic review](ASI_BACKUP_CAPTURED_VERIFICATION_INDEPENDENT_REVIEW01_2026-10-29.md).

All 24 candidates were observed as untracked and non-ignored; no existing
tracked user modification is included. `README.md` is explicitly excluded and
will be updated only after a formal Release. The isolated-copy worker and its
new tests are not in this allowlist while their independent review is pending.
Existing unrelated tracked changes,
runtime health/state, memory, raw logs, frozen experiments, original private
plans, databases, backup payloads and credential surfaces are outside this
public scope. The older standalone SQLite helper and inspection script are
not dependencies of this active source graph and are omitted.

## Verification evidence index

Detailed immutable reports remain in the local evidence archive. The public
summary records their hashes without publishing sensitive/raw evidence or
creating links to files absent from this public package.

| Report | SHA-256 | Supported result |
|---|---|---|
| G0 bounded capture independent review 03 | `51819532a2b86947009cb3e60a9e8ff80eca23fb6e684339ceb7480f5d60f162` | 23/23 fake tests; conditional for adapter integration |
| G0 writer reconciliation independent review 02 | `dcdec5398a1baafc872654a7c303fb78406fca5487097824e6d205aa2fb07b95` | 13/13 fake tests; observation reconciliation only |
| G0 Windows snapshot independent review 03 | `a14bdaf050d292a5dd476349e06e4d133db4ab50ffa197e924380ceb34b7a705` | 16 synthetic assertions; no host-state finding |
| Active HEB2 independent review, 2026-10-28 | `5866ad2fbfda06b94ed411b3126e8436f1eb8bd1925b95a97fcc037bbd60cb71` | BLOCKED: 39 existing tests pass; two additional negative checks expose gaps |
| Active HEB2 independent review 02, 2026-10-28 | `b6dd2550aab521cc4456477c62b87cfe2a8e0f797f2c2be5c98fd9f339292464` | ACCEPT for source/synthetic scope: 46/46 and three independent ledger negatives; no operational G2 PASS |
| ACL/witness static review, 2026-10-28 | `21f2be07ddd53962537cac0f50bcc6b1b38f24b006678970dd135b0ea7d9b517` | Limited static acceptance of repaired parent/witness handling |
| Bootstrap/caller independent review 02 | `3145ddb7ed5617138ed7ad5792904a625f8ef89dd9081e6cad00d3276fa0df69` | Limited caller/isolated dependency source and synthetic acceptance |
| G3 bounded independent review, 2026-10-29 | `f30704d144f2df2a61e412aa696fc073ce0662218444fdc90709da759108070b` | Actual three-child synthetic evidence accepted at 0.94; complete G3 INCONCLUSIVE |
| G3 doctor interpretation | `c6644979f63598227b780d0eb4605a48df7272fc2eb28faf2536b498aaf0a7fb` | Empty-fixture issue and bounded denials explained; no new Gate criterion |
| Captured-only independent review | `75c1bddf266cf9679b3d981014494a859ae9b500caafbc40ec2d1262e57c3d81` | 84/84 independent synthetic tests; historical scope only, live coverage UNKNOWN |

The original HEB2 BLOCK applies to its original graph. Review02 closes those
two findings in the separately pinned manifest/v4 graph; it does not erase
the original negative results. G0 has now completed its limited authorized
read-only collection and awaits independent disposition. Earlier Guardian
BLOCK records and missing historical source bytes remain in the audit.
Formal G0/G2–G6 results cannot be inferred from component tests or collection
completion.

## Historical findings and actual current outcome

The original manifest/v4 review used helper
`9708748d0af668d6725b8e9cde46a4cb0323e486faa0eca96c2ca033c14cf25f`
and caller `6d6b9a9dbc579e7532d492ee8f09c501cd3205bec105b85f8cfe72ec356997bf`.
Later analysis found that caller could alter an existing backup parent's ACL
before rejecting an existing RunId, and witness cleanup was insufficiently
scoped. Those historical findings remain valid for those versions.

The repaired graph preserves the existing parent, atomically creates only a
new private run and retains empty, identity-tracked ACL witnesses. It includes
the implemented pinned bootstrap/preflight and reviewed caller integration;
the old bootstrap-not-implemented and parent-repair-pending descriptions are
superseded, not erased from the local audit.

An actual new private backup attempt then produced its encrypted objects and
manifest, but its complete restore precheck ended **FAIL / INVALID_INPUT**.
Two individual SQLite online backups and encrypted in-memory restore smoke
checks succeeded; that partial success does not turn the whole run into a G2
PASS. The original exact ValueError text was not retained. Later reproduction
of source drift is not proof of that historical failure's precise cause.
Original backups, failure receipts, manifest bytes and producer pins remain
unchanged. No migration or formal cutover is claimed.

The current helper is
`88e0b110285331862ba741db75e3f9434343a778ceeaa23b59ec9af6b311c33e`;
the caller is `c7f038febc80198151f6fe16b37156fac38a135c87fa3b68c5ec5cbba014295b`.
The new helper adds fixed coverage diagnostics and a separate explicit
`verify-captured` entry point. Its successful or failed reports identify
historical-only scope, `live_coverage=UNKNOWN`,
`point_in_time_coherence=NOT_ESTABLISHED` and `gate_pass=false`. Original full
`verify-run` still rejects observed live drift; there is no silent fallback.
The 84-test source/synthetic review does not approve real replay execution.

The separate copy worker and its exact private execution plan remain under
review. Any future observation must use a separately approved new isolated
copy/report, byte-identical trusted artifacts, private ACLs and a separately
bound new verifier pin. Never replace a historical producer pin or use
captured-only success as fresh pre-cutover backup/readiness evidence.

## Test entry points and dependencies

From the repository root, use a supported Python with the dependencies in the
requirements file already available. Dependency installation is a separate
operation. The independently tested environment used Python 3.12.14, SQLite
3.53.1, cryptography 50.0.1 and PyYAML 6.0.3. The old Hermes launcher has not
been certified by these tests.

```powershell
python -I -S -B scripts/test_g0_bounded_capture.py
python -I -S -B tests/test_g0_writer_reconciliation.py
& '.\scripts\test_g0_windows_snapshot.ps1'
& '.\scripts\test_backup_hermes_private_acl.ps1'
& '.\scripts\test_backup_hermes_bootstrap.ps1'
python -I -B -c "import sys,unittest; sys.path.insert(0,'.'); names=['tests.test_hermes_encrypted_backup_codec','tests.test_hermes_heb2_stream_verify','tests.test_hermes_encrypted_backup_integration','tests.test_hermes_backup_coverage_diagnostics','tests.test_hermes_backup_captured']; r=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromNames(names)); raise SystemExit(not r.wasSuccessful())"
python -I -B -c "import sys,unittest; sys.path.insert(0,'.'); r=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromName('tests.test_hermes_backup_bootstrap')); raise SystemExit(not r.wasSuccessful())"
```

The integration suite creates its own synthetic fixtures below `.staging`.
Set `ASI_RUN_LARGE_BACKUP_TEST=1` in the test process to include its explicit
75 MB capacity case. The original independent run did include this case.
The bootstrap's optional real-dependency smoke needs explicit local package
paths and hashes through its documented `ASI_BACKUP_BOOTSTRAP_*` test inputs;
without them that case is skipped, not falsely reported as tested. Actual
backup execution separately requires explicit interpreter/helper/package pins.
PowerShell fake-provider tests do not call production/native backup APIs.
PowerShell 7 is the tested host; no execution-policy change is prescribed.

Repository license: [Apache-2.0](../../LICENSE). Installed distribution
metadata identifies cryptography as `Apache-2.0 OR BSD-3-Clause` and PyYAML as
`MIT`. The proposed package declares dependency versions and does not vendor
those third-party packages or Hermes upstream source.

## Public-content checks

The expanded 24-candidate preparation scan found no common provider/GitHub/
AWS token, literal bearer credential or private-key marker, and no actual
user-home/NAS/mapped-book absolute path. Test-only synthetic path strings are
not real host locators. This is a bounded content scan, not a proof of universal
secret absence. Repeat the scan against final bytes and review the exact
staged diff before committing. Do not stage broad logs/memory/telemetry or use
`git add -A`. No staging, commit, push or Release is performed by this document.
