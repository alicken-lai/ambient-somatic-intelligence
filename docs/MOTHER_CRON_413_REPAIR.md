# Mother curiosity cron: bounded DMN context

The November 2026 `mother-daily-dmn-curiosity` failure occurred after a file
tool returned 55,514 characters. The subsequent HTTP 413 error body reported
27,682 requested tokens against the selected upstream's 7,000
input-token-per-minute (ITPM) limit. This is the upstream's reported input-rate
budget, not a measured model context-window size. The initial requests had
succeeded; the failure followed the large memory read. History compression
did not reduce the request.

The repair uses Hermes' existing pre-run script support. Install
`scripts/mother_dmn_snapshot.py` under the active Hermes home's `scripts/`
directory, then use `scripts/prepare_mother_cron_bounded.py` to propose the
single-job settings change. The proposal sets the script, replaces the prompt
with instructions to use the supplied snapshot, and restricts tools to `todo`.
It preserves provider/model, schedule, delivery, enabled state, other jobs,
and historical run/error fields. A proposal alone does not deploy anything.

The collector reads DMN without changing it. It selects at most five excerpts
from the preceding 24 hours, ordered by timestamp, with a 300-byte excerpt
limit and a hard 2,400-byte JSON output limit. JSON is ASCII-escaped for
Windows subprocess decoding. Missing files and empty recent windows have
explicit statuses. Oversized or malformed input records are counted and
skipped. It scans the file once with bounded memory. This is a partial sample,
not an exhaustive daily summary.

Common credential patterns and email addresses are redacted. Regex redaction
does not guarantee removal of arbitrary secrets or personal information; DMN
must not be used as a credential store. Memory excerpts are treated as data,
not execution instructions.

## Validation and deployment evidence (2026-11-10, Taipei)

- Nine offline regression cases passed on the installed Hermes Python 3.11.
- A synthetic deployment exercised DPAPI original-byte/security-descriptor
  backup recovery, exclusive write, exact readback and ACL preservation.
- Independent source review confirmed scheduler/script/toolset compatibility
  and the deployment recovery path.
- The live single-job update completed with encrypted original backup,
  unchanged ACL and unchanged unrelated fields. No gateway restart was needed.
- The installed scheduler assembled the actual bounded prompt offline with
  one tool, a 3,374-byte system prompt and a 3,040-byte user prompt; Hermes'
  rough estimate was 1,875 tokens. This estimate is not an upstream guarantee.
- One real FreeLLMAPI request using synthetic text returned HTTP 200 and
  reported 2,124 input tokens. Combined synthetic system/user message content
  was 7,197 bytes, excluding the JSON envelope, compared with 6,414 bytes of
  actual system/user message text in the offline probe. It did not exercise the
  complete scheduled agent/tool loop or Telegram delivery.
- Final installed collector readback: exit 0, 1,609 ASCII bytes, five excerpts.
  Collector SHA-256:
  `b31e01cc8643670d919252b36ff4840e053da6580968533c5108115630405e4b`.

The historical failed status is retained until a genuine scheduled execution
updates it. The next stored run is 2026-11-15 04:30 Asia/Taipei. Telegram
end-to-end success has not yet been observed after this repair. This repair
does not establish migration, cutover or Release gate completion.
