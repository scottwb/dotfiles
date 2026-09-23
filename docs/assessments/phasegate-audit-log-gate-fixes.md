# Phase Gate: audit log gate fixes (findings 1 to 5)

Date: 2026-09-23
Auditor: phasegate (Fable 5.1, claude-fable-5-1)
Diff range: 0e3162e..4a74c0b on master (PR #6, merge 0bd14f7). The phase's own
commits are 532d502..1f07830: the plan, then a686aec, f14c9e0, a04c94d, 485f54a,
1f07830, one per fix-list item. The branch also carried 6fc83cf (the first gate's
report) and 5434692 (a settings.json permissions edit); neither is phase work.
Verdict: **PASS_WITH_FINDINGS**

## Summary

The phase promised to close items 1 to 5 of the 2026-09-23 gate on the audit
log generator, with item 6 folded into step 1: a rate table re-read from the
published pricing page, a sweep that survives any per-session exception, a
copyable index command nothing in a transcript can compose, an
unknown-versus-unpriced distinction derived from `provider_for`, and a
cost-less page that says so and can be repaired. Every one of those is
delivered and verified here against the live pricing page, the real transcript
store (707 files, 61 projects, read only), and synthetic malformed transcripts.
The suite is 428 tests green with no skips. Two findings keep this from a clean
PASS, and neither is a promise undelivered. High: the index's copyable command,
the very line step 3 hardened and pinned with a regression test, has never
parsed, because every real project directory name starts with a dash and
argparse reads `--project -Users-...` as a missing argument; the phase
inherited that from the batch and then locked it in. Medium: the sweep now
survives a transcript whose `usage` is a string or whose `timestamp` is not a
string, but `index.scan` calls the same `describe` with no guard, so
`--all --index` still finishes the sweep and then dies before writing the
index, which is the exact harm the first gate's finding 2 named. Both are a few
lines each.

## Test truthfulness

- `.claude/skills/audit-agent-conversation/run-tests` from the repo root:
  **Ran 428 tests, OK**, exit 0, on `/usr/bin/python3` 3.9.6. A clean `OK`
  with no `skipped=`; the greenthumb corpus and both fixture sessions are
  present, so every corpus-gated test ran. The noisy refusal, write-guard and
  help-text output is by design.
- 401 to 428: 27 tests added, none deleted, none weakened. Counted against the
  diff: 13 in `tests/test_cost.py`, 11 in `tests/test_cli.py`, 3 in
  `tests/test_index.py`. The one removal is the `CACHE_READ_EXCEPTIONS` dict in
  `test_cache_multiples_hold_for_every_model`, replaced by a read of the row's
  own `cache_read_multiple`, which is what item 6 asked for (judged below).
- Each step's test reproduces the defect the first gate demonstrated rather
  than a stand-in: a real corpus transcript with one `usage` turned into a
  string, the gate's verbatim `dddddddd-0000; echo PWNED #` id, the live
  `x-ai/grok-4.6` slug, and a two-sweep sequence over a cost-less page.
- The green suite lies in one place, the way a green suite can: the sweep's
  new tests feed it a transcript that fails in `load_session`, which the
  widened handler catches, and `test_the_index_is_still_built_after_a_failure`
  passes because `describe` tolerates that particular malformation. It does
  not tolerate a non-string timestamp, and nothing tests the index or the
  walking path against one (finding 2 below).
- `test_a_well_formed_session_keeps_its_unquoted_command` pins a string that
  argparse cannot parse (finding 1 below). The test proves the fix's blast
  radius was zero, which was its purpose; it also proves the line was already
  dead.
- `test_cache_multiples_hold_for_every_model` now checks each row against the
  multiple that row declares, so it is an internal-consistency check, not a
  check against the published rule. The pins in
  `test_cache_read_multiple_exceptions_come_from_the_table` and
  `test_cache_read_multiple_defaults_to_one_tenth` cover every row that exists
  today. Accepted as the intended shape (the data is the one source); a cheap
  strengthening is in the fix list.
- No `TODO`, `FIXME`, `HACK` or `XXX` markers in the skill, tests, wrapper or
  plan. No emdashes in any phase file. The plan file's only diff across the
  phase is 18 checkbox flips.

## Citation walk

Each plan step cites a fix-list item from
`docs/assessments/phasegate-audit-log-phase.md`; the central question is
whether the item is closed, not merely touched.

| Plan step | Satisfies | Status | Notes |
|---|---|---|---|
| Step 1: refresh the whole rate table | gate item 1 (high) | satisfied | Every row of `pricing.json` re-verified by me against `https://platform.claude.com/docs/en/about-claude/pricing` fetched today: Fable 5.1 and Mythos 5.1 at 10 / 12.50 / 20 / 0.25 / 50 (0.025x footnote), Fable 5 and Mythos 5 at 10 / 12.50 / 20 / 1 / 50, Opus 5.5 at 4 / 5 / 8 / 0.20 / 20 (0.05x footnote), Opus 5, 4.8, 4.7, 4.6, 4.5 at 5 / 6.25 / 10 / 0.50 / 25, Sonnet 5 at 2 / 2.50 / 4 / 0.20 / 10 with the page's own footnote that the $3 / $15 increase "will not occur", Sonnet 4.6 and 4.5 at 3 / 3.75 / 6 / 0.30 / 15, Haiku 4.5 at 1 / 1.25 / 2 / 0.10 / 5. The page's long-context section confirms no 1M premium, so every `[1m]` alias pricing off its base row is right. `verified` is `2026-09-23` and `source` names the page: both honest. `test_sonnet_5_rates` and `test_opus_5_5_rates` pin the two rows that mattered. Rendered the one live Opus 5.5 session (`82afa7be`, spruce): total $10.85, note reads "cache reads at 0.05x", no `cost:none` on its marker. |
| Step 1 (folded): `cache_read_multiple` into the data | gate item 6 (low) | satisfied | One source: the row in `pricing.json`. `cost.cache_read_multiple` (`cost.py:81-90`) reads it with a 0.1 default; `render.py:781` calls it for the page note (the division is gone) and `tests/test_cost.py` calls it for the table check. Aliases resolve first, so `claude-opus-5-5[1m]` reports 0.05. A Fable 5.1 page still says 0.025x, an Opus 5 page 0.1x (rendered). Nit: the header comment re-lists the exceptions in prose, which the first gate asked to delete; prose the code never reads, but a second statement of the fact all the same. |
| Step 2: sweep survives any per-session exception | gate item 2 (high) | satisfied for `render_one`; the finding's stated harm is only partly closed | `render_one` (`cli.py:1052-1074`) is one `try` around load, support check, describe, participants, render and write; `except Exception`, not `BaseException`, so Ctrl-C and `sys.exit` still stop the run. Verified with a usage-string transcript, a dict timestamp, an int timestamp: ERROR row, reason beneath, good session behind it rendered, tally printed, exit 4. The dict-timestamp case makes `describe` itself fail, and `render_failure` (`cli.py:1077-1106`) fell back to the filename stem and `?` participants rather than crashing: the row cannot become a second failure. Outside a sweep the failure is the long `error: could not render` message, exit 4, nothing written. But `index.scan` (`index.py:136`) and the walking path (`first_renderable` via `classify`, `cli.py:413-415`) call `describe` with no guard: finding 2. |
| Step 3: validate the copyable command | gate item 3 (medium), Security | satisfied | `UUID_RE` (`index.py:40`) gates the id, else the file stem through `shlex.quote`; the project name through `shlex.quote` (`index.py:73-104`). The gate's crafted id yields `audit-agent-conversation dddddddd-0000-0000-0000-000000000004 --project ...` with the injected text gone, asserted through `shlex.split(comments=True)`. Well-formed lines unchanged: the index built from the real store is byte-identical before and after the phase (610,530 bytes, `cmp` clean), all 707 stems are UUID-shaped and all 61 project names are `shlex.quote` fixed points (checked). Self-contained and byte-reproducible assertions still hold. The shell hole is closed; the line it protects has never worked: finding 1. |
| Step 4: unknown-versus-unpriced from `provider_for` | gate item 4 (medium) | satisfied | `unpriced_reason` (`cost.py:97-134`) tries the row, then the recorded `unpriced` map, then derives from `provider_for`; `is_unknown` (`cost.py:265-275`) is true only when that derivation returns None, which only a `claude-` prefix produces. No second list. `rates_for` raises `UnknownModel` for every rate-less id (verified for slugs, unknown providers, the empty string and `None`), so nothing prices at zero. Probed: `glm-4.7-flash` says "runs locally through Ollama"; `x-ai/grok-4.6` says routed via OpenRouter, no `pricing.json`, no `$` on its page; `claude-not-a-real-model` is unknown and warns; `mystery-model-9000` and an unlisted `llama3:8b` say provider unknown. Census of every `message.model` in the store: 20 distinct ids, 8 priced, 12 unpriced with an honest reason, zero flagged unknown; the three OpenRouter slugs the first gate named now read as routed. (The bare `opus` / `sonnet` / `fable` strings in 288 assistant records live in tool inputs, not `message.model`, and never reach `cost`.) |
| Step 5: cost-less pages say so and can be repaired | gate item 5 (medium) | satisfied | Marker line gains ` cost:none` only when unpriced (`render.py:918-921`); a priced page's marker is unchanged, and the only byte that differs on a priced page across the whole phase is the "checked 2026-09-23" date step 1 was supposed to change. `_PAGE_SESSION` still matches a `cost:none` line (group stops at the space; verified: `page_session_id` returns the id and `index.pages_by_session` links the page). Exercised end to end on a fake root: first sweep WROTE plus the warning naming `--force`; second sweep with the model still unknown, EXISTS `no cost figure; --force to repair` plus the same warning; third sweep with the model now priced, the repair line; `--force` rewrites the page and the marker loses `cost:none`; EXISTS stays exit 0 throughout. A permanently unpriced page stays quiet (`TestPermanentlyUnpricedPageIsNotNagged`). `page_head` reads 300 bytes with `errors="replace"` and returns `""` on `OSError`. |

Items 7 to 10 were deferred by the plan and are not defects of this phase.
Their descriptions in the first gate's report are still accurate, with two
updates: item 10's `%g` division no longer exists (`render.py:781` reads the
multiple; a zero input rate can no longer raise there), though the table test
still accepts an all-zero row; and item 9 is narrower than written, because
the new routed-slug test does assert no `$0.00`, while the unknown-model tests
in `tests/test_cli.py` still do not. Item 7 (`parse.py:49-57`) is untouched.
Item 8's cited SKILL.md lines are all still present (version header at line
15, "345 sessions" at 52, `--quiet` at 91, "quietly swapped" at 112).

### The two discretion calls, judged

**Widening step 1 from "fix the Sonnet 5 row" to a full table refresh with
new models.** Right. The first gate's own item 1 said "re-check every row
against the live page, not the skill's cache", the plan records Scott asking
for the whole table plus Opus 5.5 on the day, and the refresh is what
surfaced the second cache-read exception that made item 6 worth doing now
rather than later. Every added figure is correct against the page. The one
soft claim is "rows the corpus can produce": the census shows no
`claude-mythos-5-1`, `claude-opus-4-5` or `claude-sonnet-4-5` session in the
store today, so "can" means "could", which is harmless and cheap.

**Editing SKILL.md and the `pricing.json` comment block inside commits whose
subjects are about code.** Right. The plan's execution instruction 5 says to
update SKILL.md where the behaviour it documents changes, and both commit
bodies (485f54a, 1f07830) name the doc edit and why. The alternative, a
trailing docs commit, leaves an intermediate commit in which the comment
describes the old definition of "unknown" while the code implements the new
one, which is documentation rot with a commit hash on it. Subject lines
describe the behaviour, bodies disclose the documentation: that is the right
division.

## Drift findings

- **High** | `scripts/auditlog/index.py:102-104` (`Entry.command`) | The
  copyable command is `audit-agent-conversation <id> --project <dirname>`,
  and every real project directory name starts with a dash
  (`-Users-scottwb-src-...`, `-Volumes-Spruce-spruce`). argparse classifies a
  dash-led token as an option, so `bin/audit-agent-conversation 0000... --project
  -Users-scottwb-src-scottwb-greenthumb` exits 2 with `error: argument
  --project: expected one argument`; `--project=-Users-scottwb-src-scottwb-greenthumb`
  resolves the project correctly. Reproduced today against the real wrapper.
  The pre-phase index emits the identical string, so this is inherited from
  the batch, not introduced here; but step 3 rewrote exactly this line, the
  commit says "no existing line moves", and
  `test_a_well_formed_session_keeps_its_unquoted_command` now pins the
  unparseable form. Every `TO DO` row the index has ever offered, including
  the three in the real index today, hands the reader a command that cannot
  run, and SKILL.md tells them to paste it. | Fix: emit `--project=%s` with
  the value still through `shlex.quote`; retarget the regression test; add a
  test that feeds the emitted argv to `cli.build_parser().parse_args` (no
  I/O) so the line is proven to parse, not only to split.
- **Medium** | `scripts/auditlog/parse.py:351-358` (`parse_timestamp`),
  `scripts/auditlog/index.py:136` (`scan`), `scripts/auditlog/cli.py:413-415`
  (`classify`, via `first_renderable`) | A `timestamp` that is not a string
  (a dict or an int) raises `AttributeError: 'dict' object has no attribute
  'replace'` inside `describe`. `render_one` absorbs it now, so `--all` prints
  the ERROR row and finishes, but `index.scan` and the walking path call
  `classify` unguarded: `--all --index` finishes the sweep and then dies with
  a traceback before writing the index, and a bare `audit-agent-conversation
  --project X` dies on the same file. Demonstrated on a fake root with one
  such transcript beside a good one; a garbage *string* timestamp degrades
  fine on all three paths, so the trigger is type, not value. The plan's
  requirement ("any stage of `render_one`") is met; the first gate's finding
  2 named "under `--all --index` the index is never built" as the harm, and
  that harm survives one call site over. | Fix: make `parse_timestamp` return
  None for non-strings; wrap the per-candidate body of `index.scan` and
  `first_renderable` so a transcript that cannot be described becomes an
  unreadable `Entry` / skip row rather than a traceback; test both paths with
  a dict timestamp.
- **Low** | `scripts/auditlog/pricing.json` `aliases` | The `[1m]` aliases
  are hand-listed for five rows. `claude-opus-4-6[1m]`,
  `claude-sonnet-4-6[1m]` and the rest classify as unknown and warn "add its
  list rates" although their base rows are priced and the page confirms no
  1M premium on any model. Nothing in the store carries such an id today, so
  no wrong page is reachable. A list that must agree with another list is the
  hand-maintained-pair shape the repo rules warn about. | Fix: strip a
  trailing `[1m]` in `cost._resolve` and delete the five alias entries; keep
  `claude-haiku-4-5`.
- **Low** | `tests/test_cost.py` `test_cache_multiples_hold_for_every_model` |
  Checks each row against its own declared multiple, so a future row whose
  `cache_read_multiple` and `cache_read` are wrong together passes; it also
  still accepts an all-zero row (first gate, item 10). Accepted as the
  intended one-source shape. | Fix: assert an explicit
  `cache_read_multiple` is never 0.1 (explicit means exception) and that
  `input` is positive; both are one line each.
- **Low** | `SKILL.md:139-145` | The new EXISTS / repair paragraph was
  inserted mid-paragraph, so "The receiver is the agent's own `agent-name`
  when the transcript carries one..." (about the RECEIVER column) now reads
  as a continuation of the repair advice. | Fix: fold into item 8's SKILL.md
  pass.
- **Nit** | `pricing.json` `_comment` | Re-lists the cache-read exceptions
  in prose ("Fable 5.1 and Mythos 5.1 at 0.025x, Opus 5.5 at 0.05x") after
  the first gate asked for the exception clause deleted. Prose the code never
  reads, but a second statement of a fact the rows carry.
- **Nit** | commit f14c9e0 message, `cli.py:1091-1093` | "Single-session
  behaviour and every exit code are unchanged": a single-session parse
  failure was an uncaught traceback (exit 1) and is now `error: could not
  render`, exit 4. An improvement, pinned by
  `test_outside_a_sweep_the_failure_is_the_long_message_and_exit_4`, but the
  claim is loose. Also, the plan's "Files Modified" table omits `render.py`
  (steps 1 and 5) and `SKILL.md` (step 5).
- **Nit** | `cli.py:456` (`_PAGE_COST_NONE`) | A cost-less page whose
  session id carries a non-hex character cannot match, so it reads as priced
  and never gets repair advice. Same limitation `_PAGE_SESSION` already has
  for the index, crafted-id only.
- **Informational (persisting)** | `parse.py:49-57` majority-model pricing
  (item 7), `tests/test_self_contained.py:47` non-greedy stripper (item 10),
  the accepted mkstemp TOCTOU: all unchanged, all still accurately described.

Positive drift notes: no product change outside `scripts/auditlog/` and
`SKILL.md`; runtime imports gained only `re` and `shlex` in `index.py`, both
stdlib; the transcript store was read only throughout this audit (every
sweep ran against a fake root or `--stdout`), and
`test_no_transcript_was_modified_by_the_sweep` is green.

## Security

Triage: **hit**. The phase composes a shell command from transcript-derived
strings (step 3), widens an exception handler around parsing of untrusted
transcript content (step 2), and adds a short read of every page in the
output directory (step 5). Full review of the touched areas:

- **Shell composition: closed.** The id reaches the line only when it
  matches `UUID_RE` (hex and dashes, nothing to quote); otherwise the file
  stem through `shlex.quote`, which single-quotes anything outside
  `[A-Za-z0-9@%+=:,./-]` and leaves a newline inert inside the quotes. The
  project name goes through the same. HTML side unchanged and still escaped
  (`data-copy` with `quote=True`). Reproduced the first gate's payload:
  `; echo PWNED #` no longer appears in the copied text. The line's own
  parse failure (finding 1) is a functional defect, not a security one.
- **Widened handler: no new hole.** `except Exception` only; the `mkstemp`
  block cleans its staging file under `BaseException` before re-raising, so
  the outer catch can never leave a half-written page; `UnsafeDestination`
  is caught inside and still exits 7 before any write; `check_destination`
  is unchanged. Nothing is swallowed silently: the exception text is printed
  beneath the row.
- **Denial of the whole run by one file: partly open.** `--all` is closed;
  `--all --index` and the walking path are not (finding 2). Not an
  escalation; a single crafted or corrupt transcript still stops the index.
- **Page-head read: safe.** 300 bytes, `errors="replace"`, `OSError` to
  `""`; the marker regexes are anchored on the tool's own prefix.
- **Terminal control characters (informational, pre-existing shape).** The
  report rows pass transcript titles and, new this phase, exception text
  through `fit()`, which collapses whitespace but not `ESC`. A transcript
  could put a terminal escape on stderr. Low likelihood, same trust model
  as the earlier gates; worth a `\x1b` strip in `fit` some day.
- Transcript store never written; symlinked targets; path traversal;
  secrets; network: all unchanged since the first gate and re-checked by the
  write-safety and self-containment suites.

## Fix list (seeds the next planning session)

1. **Make the index's copyable command parse** (high, `index.py:102-104`):
   emit `--project=%s` with the quoted value; retarget
   `test_a_well_formed_session_keeps_its_unquoted_command`; add a test that
   runs the emitted argv through `cli.build_parser().parse_args`.
2. **Guard the describe stage on the index and walking paths** (medium,
   `index.py:136`, `cli.py:413-415`, `parse.py:351-358`): `parse_timestamp`
   returns None for non-strings; `index.scan` and `first_renderable` turn a
   transcript that cannot be described into an unreadable row; test
   `--index` and `--project` with a dict timestamp.
3. **Derive the `[1m]` alias** (low, `cost._resolve`, `pricing.json`): strip
   the suffix, delete the five entries.
4. **Strengthen the cache-multiple test** (low, `tests/test_cost.py`):
   explicit multiple is never 0.1; `input` is positive. Closes the remaining
   half of the first gate's item 10 nit.
5. **Carry forward items 7, 8 and 9** from the first gate, with item 8 now
   also covering the mid-paragraph insert at `SKILL.md:139-145`.
6. Nits: drop the prose exception list from the `pricing.json` comment; the
   `_PAGE_COST_NONE` crafted-id edge; an `ESC` strip in `fit`.

## Gate handling

Verdict PASS_WITH_FINDINGS. No roadmap `PHASE GATE:` item exists for this
phase, so no checkbox is ticked; this report is the only file the gate writes.
Item 1 is small enough to land on its own before the next `--index` is
shared with anyone; item 2 belongs in the same plan. Recommend a `/gameplan`
session for items 1 and 2, and not resuming the audit-log follow-ons until
item 1 is in, since the index is the follow-ons' front door.
