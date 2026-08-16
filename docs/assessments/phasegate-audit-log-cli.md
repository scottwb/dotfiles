# Phase Gate: audit-log CLI (Phase 3, Steps 11-13)

Date: 2026-08-15
Auditor: phasegate (Fable 5, claude-fable-5)
Diff range: 6506959..887b7fa (commits c61467f, 5105d35, 887b7fa)
Verdict: FAIL

## Summary

The phase promised session resolution six ways, output into `~/.ai-staff-audit-log/`
with the A2 filename shape and no-overwrite protection, and a working command
runnable from anywhere. All of that is delivered and delivered well: all six
resolution modes verified against the real corpus, refusals write nothing and
truncate nothing, the slug surface is watertight against traversal and hostile
titles, and the wrapper works through symlink chains and preserves exit codes.
The verdict is FAIL on a single blocking finding: the safety property "never
write to `~/.claude/projects/`" is not enforced anywhere in the write path. A
constructible invocation (`-o <transcript path> --force`) overwrites a
transcript with HTML, and the tool's own error message coaches the user into
adding `--force`. The fix is a few lines; everything else in the phase is
sound.

Audit note: the worktree was under active development during this audit (a
builder session committed Step 14 and was mid-Step-15). The audit was therefore
performed against a pristine export of the phase boundary commit `887b7fa`,
attacked only in the scratchpad, with the live worktree used solely for
read-only verification. The in-flight Step 15 state (a red, untracked
`test_corpus_sweep.py` and additions to `pricing.json`) is Phase 4 work,
expected mid-step, and out of scope here; the v1 gate should verify it.

## Test truthfulness

- At the phase boundary (`887b7fa`), on stock `/usr/bin/python3` 3.9.6:
  **202 tests, all green** (one environmental error in the exported copy only,
  because `test_committed_with_mode_755` shells out to `git ls-files` and the
  export is not a repo; the same test passes in the real worktree).
- No skipped or pending tests added during the phase; `require_corpus` skips
  are a pre-existing, documented portability mechanism, not a dodge.
- No weakened or deleted tests; Phase 1 and 2 tests are intact and green:
  golden token figures (8 API messages, 16,179 output, naive 41,302 guard),
  golden cost figures to the cent, the 15/13 corpus split
  (`tests/test_refusal.py:110-113`), and the self-containment assertions.
- The Phase 4 in-progress `pricing.json` change only adds models; the
  `claude-opus-5` row the goldens depend on is unchanged.
- Gap worth noting: the suite never exercises the wrapper **through a
  symlink**, which is how it runs in real use (`bin/` is linked into `$HOME`).
  Verified manually here (absolute link, relative chain, from `/`): all pass.

## Citation walk

| Plan step | Satisfies | Status | Notes |
|---|---|---|---|
| 11 | Section 10 CLI shape (six resolution modes) | satisfied | All six verified live: explicit path, full UUID, prefix `9608087e`, `--project greenthumb`, `--latest` (and as default), `--date 2026-08-13`. Ambiguous prefix and unmatched project raise errors naming candidates (`tests/test_resolve.py:79-98`). Bare invocation from inside a project repo resolves via cwd. |
| 11 | Requirement "never write to `~/.claude/projects/`" | **partially satisfied** | `resolve.py` itself is strictly read-only (verified by grep, by the self-reading test at `tests/test_resolve.py:142-148`, and by the mtime-invariance test). But the requirement is a property of the tool, and `cli.py` can be pointed at a transcript. See finding 1. |
| 12 | A2 filename shape | satisfied | `20260813-0557-donna-to-greenthumb-<slug>.html` verified; filenames sort chronologically; initiator glob works (`tests/test_cli.py:85-110`). |
| 12 | A5 participant resolution | **partially satisfied** | Receiver chain (`--to`, `agent-name`, project map, last segment) is complete. Sender chain is not: the code comment at `cli.py:88-89` claims `--from`, then the project map, then the default, but the implementation (`cli.py:97`) skips the map entirely. See finding 2. |
| 12 | A6 output placement | satisfied | Default dir `~/.ai-staff-audit-log/`, created when missing (nested creation tested), never deleted from. |
| 12 | A7 refusal discipline | satisfied | Exit 3, message on stderr naming every condition with magnitude, nothing written, output directory not even created, pre-existing files never truncated (verified adversarially with `-o` at an existing file). |
| 12 | Acceptance 6 (honest refusal) | satisfied | As above, plus wrapper propagates the code. |
| 12 | Acceptance 9 (placement and no-overwrite) | satisfied | `--force` genuinely required on both the `--output-dir` and `-o` routes (both verified live, exit 6 without it, byte-identical file after the refusal). |
| 13 | A1 (skill-owned, thin wrapper) | satisfied | Wrapper is 34 lines of sh, exec-ing `python3 -m auditlog.cli`; all behavior lives in the skill package. |
| 13 | "Scripts work relative to script location" | satisfied | Resolves its own path, follows symlink chains without GNU `readlink -f`; verified via absolute symlink, relative chained symlink, and cwd `/`. |
| 13 | Acceptance 10 (runs from anywhere) | satisfied | Committed mode 100755 (`git ls-files -s` confirms), `--help` exits 0, refusal exit 3 and resolution-error exit 2 survive the `exec`. |

## Drift findings

- **Critical** | `cli.py:189-210` | **The safety property is unenforced: the CLI
  will write into `~/.claude/projects/` when told to.** Demonstrated on a
  scratchpad copy of a transcript (never on a real one):
  `audit-agent-conversation <session> -o <copy>.jsonl` refuses with exit 6 and
  leaves the file byte-identical, but the refusal message is "Pass `--force` to
  overwrite it.", and re-running with `--force` replaced the transcript copy
  with the rendered HTML. The realistic accident chain is short: a user who
  mistakes `-o` for the input argument and passes a transcript path gets an
  error that coaches them into `--force`, and the only copy of a session is
  gone. Related edges of the same hole: `--output-dir` pointed inside the
  projects tree happily writes an `.html` there (verified against a mimic
  directory); `os.makedirs` at `cli.py:197` will create new directories under
  the projects root; and `open(target, "w")` follows a symlink, so a
  planted link in the output directory whose name matches the predictable
  A2 filename would redirect a `--force` write into a transcript. Suggested
  fix: after computing `target`, refuse (regardless of `--force`) when
  `os.path.realpath(target)` is under `os.path.realpath(resolve.PROJECTS_ROOT)`,
  and add the corresponding test. This closes every variant above in one place.
- **Medium** | `cli.py:83-98` | Sender attribution silently defaults wrong for
  agent-initiated sessions. `resolve_participants` uses `--from`, else
  `default_sender` ("scott"); the docstring's "then the project map" step does
  not exist in the code, and Step 12's checkbox claims it does. Consequence,
  reproduced live: rendering brief `9608087e` (initiated by Donna) without
  `--from` produces `20260813-0557-scott-to-greenthumb-...` and a page whose
  masthead attributes the exchange to scott. For an audit-log tool, a
  confidently wrong initiator is worse than an "unknown". A5 scoped the
  `scott` default to *interactive* sessions; `session.entrypoint` is available
  (`sdk-cli` vs `cli`) and unused here. Suggested fix: for non-interactive
  entrypoints with no `--from` and no map hit, either require `--from` or
  label the sender `unknown`, and align the docstring with the code.
- **Medium** | `resolve.py:132-134` | `_by_date` comment says "the message says
  so rather than picking silently", but no message is emitted: several sessions
  on one day silently resolve to the newest. This is not hypothetical: 8 dates
  in the greenthumb corpus carry 2-4 sessions each. The non-`--quiet` summary
  line names only the output path, not the resolved session id, so the user
  cannot tell which of the day's sessions was rendered. Suggested fix: emit the
  promised notice naming the chosen session and the count, or make multi-match
  an error listing candidates, consistent with prefix ambiguity.
- **Low** | `cli.py:209-210` | Non-atomic write. `open(target, "w")` truncates
  before writing, so an interrupted `--force` run destroys the previous good
  page and leaves a partial file (the exists-check-then-open pair is also a
  trivial same-user TOCTOU). Suggested fix: write to a temp file in the target
  directory and `os.replace` it into place; this also fixes the symlink edge
  of finding 1 as a side effect.
- **Nit** | `resolve.py:162-193` | `resolve()` accepts a `latest` keyword and
  never reads it; latest-as-default makes it vestigial. Drop it or assert it.

Positive drift notes: no TODO/FIXME/HACK markers introduced; no emdashes in any
Phase 3 file; runtime imports are exactly `argparse, datetime, errno, html,
json, os, re, sys` plus a function-local `zoneinfo` (all stdlib, all 3.9-safe,
suite green on stock 3.9.6); no network, no subprocess in the runtime modules
(`subprocess` appears only in `test_wrapper.py`, legitimately); no model call
anywhere in the render path (A9 holds).

Filename safety verified adversarially: `slugify` reduces traversal sequences,
absolute paths, null bytes, RTL-override characters, and 500-character titles
to bounded `[a-z0-9-]` slugs; empty and all-punctuation input falls back to
`session`; the leading timestamp makes a leading dash impossible; worst-case
filename length is ~204 bytes, under every filesystem limit. Hostile
participant names and `agent-name` values are both slugified in filenames and
`html.escape`d at every render interpolation (`render.py:777-783`), so a
crafted transcript cannot steer the output path or inject markup.

`--date` provenance verified: a transcript copy with its mtime forced to
2026-01-01 still resolves under its record-timestamp date 2026-08-13 and does
not match `--date 2026-01-01` (record timestamp wins, as required).

## Security

Triage: **hit.** The phase touches file handling, path construction from
partially untrusted data (transcript titles, `agent-name`), and an overwrite
privilege flag. Full review performed with an adversarial mindset; results are
the findings above. Injection into the page: closed (everything escaped). Path
traversal via crafted data: closed (`slugify` plus timestamp prefix). Path
misdirection via explicit flags: **open** (finding 1, critical). Symlink
following at the write site: open as an edge of finding 1. No secrets, no
subprocess, no network surface.

## Fix list (seeds the next planning session)

1. **Guard the write path against `~/.claude/projects/`** (critical,
   `cli.py:189-210`): refuse any `target` or `--output-dir` whose realpath
   falls under the realpath of `resolve.PROJECTS_ROOT`, `--force`
   notwithstanding, with a test that proves both the `-o` and `--output-dir`
   routes refuse. Consider an atomic temp-write plus `os.replace` in the same
   change (also resolves fix 4).
2. **Honest sender attribution** (medium, `cli.py:83-98`): stop defaulting
   non-interactive sessions to `scott`; use `session.entrypoint` to require
   `--from` or label the sender `unknown`, and make the docstring match the
   code.
3. **Surface the multi-session `--date` pick** (medium, `resolve.py:132-134`):
   emit the promised notice (or error with candidates), and include the
   resolved session id in the CLI summary line.
4. **Atomic output write** (low, `cli.py:209`): temp file + `os.replace`.
5. **Drop or honor the unused `latest` parameter** (nit, `resolve.py:162`).
6. For the v1 gate: add a suite test that invokes the wrapper through a
   symlink, since that is its real-world shape, and re-verify the in-flight
   Step 15 corpus sweep once committed (it was red mid-step during this audit,
   with 11 sessions failing on unpriced models, and `pricing.json` was being
   extended to address exactly that).
