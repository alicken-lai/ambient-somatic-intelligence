# G3 doctor: read-only interpretation of the retained synthetic run

Date: 2026-10-29. Analyst: `/root/git_release_execution`.
Scope: the actual 2026-10-28 `g3-existing-stage-20261028-01` evidence for the retained Hermes **v0.21.2**, commit `939e45c91d751fadd94dcd1b873ac3cb44846213`. This is an append-only diagnostic note, not a new execution, criteria revision, Gate PASS or Release decision.

## Outcome

The single doctor issue is **missing `.env` in the deliberately credential-empty synthetic fixture**. It is an honest finding, not evidence that the five required Python packages are missing or that the staged launcher failed. No production configuration, database, service or network change is needed merely to remove this synthetic finding. Do not fabricate an `.env`, credential, authentication response or healthy doctor summary, and do not enable `--fix`/`--live` to obtain a cleaner result.

The exact pinned source explains the apparently successful exit: `hermes_cli/doctor_config.py` lines 133–164 append the missing-`.env` setup issue when neither home nor project provides that file. `doctor.py` lines 140–181 prints accumulated `Finding` issues but does not map their count to a nonzero exit. Consequently **exit 0 is command termination, not zero issues or service health**. Both the issue and exit remain part of the original evidence.

## Findings and their significance

| Observation | Meaning within this fixture | What it does not establish |
|---|---|---|
| Missing `.env`; absent config using defaults | Expected consequence of a genuine fresh, empty synthetic home; one recorded issue | Production credentials/config are absent, broken or restored correctly |
| OAuth not logged in; OpenRouter not configured; no GitHub token/Skills Hub initialization | No fixture credentials or prior user state were provided | Real authentication, token refresh, connectivity or Skills Hub health |
| Optional Telegram/Discord packages and git/rg/Docker/Node warnings; disabled/unavailable toolsets | Finite environment deliberately omits optional dependencies and tool executables | A new requirement to install every optional feature for G3 |
| OpenAI SDK, Rich, python-dotenv, PyYAML and HTTPX checks succeed | These five source-declared required package imports succeeded under the intended staged interpreter | Complete package provenance, every plugin contract or production readiness |
| “Running 40 connectivity checks” | Size of the probe list; unconfigured providers return skip/not-configured results | Forty completed network requests or successful API connectivity |

The source marks Telegram/Discord as optional in `doctor_platform.py` and warns without adding their absence to the issue list. `doctor_tools.py` distinguishes optional tool absence and enabled API-key-dependent toolsets. The source's ordinary connectivity section can issue HTTP requests when configured, even without `--live`; the current run's finite credential-empty environment and retained guard are therefore important. No network allowance is proposed here.

## Exact bounded denial interpretation

The doctor audit records four denied opens, one denied hostname event and one denied socket construction. Hashes of the known public Windows-resolved Linux probe paths independently match the retained target tokens:

- `/proc/1/cgroup` twice: `config._is_container` and `hermes_constants._detect_container`;
- `/proc/self/mountinfo`: `hermes_constants._root_mount_has_marker`;
- `/proc/1/comm`: `service_manager._s6_running`.

These are Linux/container/service capability probes, not evidence of a production secret/config/database read. Their `OSError` handling degrades to the source's non-container/non-s6 path. The original denial records remain; no access-rule relaxation or rerun to reduce their count is warranted.

`socket.gethostname` comes from `platform` local host identification. It is distinct from outbound connectivity, although the original conservative hook denies both socket event classes. The one `socket.__new__` originates in the retained urllib3 `util/connection.py` `_has_ipv6("::1")` import-time capability probe. The constructor is denied before its loopback bind can execute. This does not certify IPv6 availability or actual provider connectivity. Hook coverage retains its documented pre-sitecustomize `.pth` and native-operation limitations; no whole-OS claim is made.

The one exact `ALLOW_ABSENT_GH_LOOKUP` is the genuine missing executable lookup for `gh auth status --json authenticated`, after bounded fresh absence checks. It is not a fabricated executable or authentication result.

## Original protocol and minimal next steps

The original G3 protocol requires the intended isolated interpreter/environment and launcher to run import/startup, version and doctor checks, with production targets unchanged and installation/provenance evidence. It does **not** require every optional warning to disappear. The original finite attribution criteria explicitly preserve the empty-home `.env` finding and instrumented diagnostic effects; affected live/configured checks remain unestablished rather than silently waived.

No source or production repair is recommended just to remove these fixture warnings. If additional semantic regression evidence is useful, the smallest separate tests would be fake-only unit tests that:

1. require the missing-`.env` issue to remain visible and assert no `touch`, `mkdir` or `chmod` action without `--fix`;
2. confirm that the source's printed summary/issues and process-exit semantics are distinct;
3. distinguish optional missing-package warnings from required missing-package issues.

Such tests would assert expected failures/warnings using in-memory fakes; they would not create credentials, `.env` contents or a replacement doctor result used as runtime evidence. They are optional clarifying regressions, **not new Gate criteria**, and were not executed by this note. Actual configuration/session/Guardian/MCP behavior stays in the original named G2/G4/G5 isolated-preservation and contract checks, not in a synthetic doctor summary.

## Evidence integrity references

The existing independent bounded review is `logs/asi_update_verification/asi-release-20261027-01/g3-existing-stage-20261028-01/G3_INDEPENDENT_BOUNDED_REVIEW01_2026-10-29.md`, SHA-256 `f30704d144f2df2a61e412aa696fc073ce0662218444fdc90709da759108070b`.

- Actual doctor stdout SHA-256: `77e35e454b65dcf2952ad651c26fe8685a54e495ee9c6a77029416d96bf4bbbe`.
- Frozen runner SHA-256: `b9056b4bab60c55e154189afd344f2a30f5c18e9d7bfa57fb57dbbd9a2ebc78f`.
- Guard SHA-256: `cb2855a13cfb94da95797fcdc502800662858c73b9b2a561b06ec4359fb4b43f`.
- Original bounded criteria SHA-256: `dfd2a944a67090f2f4f77c7b7135e7a88f0608670f5298cef6220b4705d76ed0`.
- Original full protocol SHA-256: `a434deb5362c72f61120b2997e642ad46f3f0bc453a462dbf2f148581787b34c`.

No original artifact, criteria, audit or failed result was modified. Full G3 remains INCONCLUSIVE in this analysis; `gate_pass=false`, `release=false`.
