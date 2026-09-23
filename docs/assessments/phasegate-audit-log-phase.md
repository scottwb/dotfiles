# Phase Gate: audit log generator (v1 plus the follow-on batch)

Date: 2026-09-23
Auditor: phasegate (Fable 5.1, claude-fable-5-1)
Diff range: e8dffbb..0e3162e (merge base of PR #4 to HEAD on master)
Un-gated slice concentrated on: 0a0318a..cda8e05 (everything after the four 2026-08-15 reports)
Verdict: **PASS_WITH_FINDINGS**

## Summary

The phase promised a skill and CLI that turn one Claude Code transcript into a
self-contained audit page with honest, derived figures, then a follow-on batch
adding provider naming, an aligned work log with per-step durations, an index
of every session there is to render, and ERROR rows during a sweep. All of it
is delivered and merged (PR #4, 55 commits), the suite is 401 tests green with
zero skips on stock 3.9.6, and the four earlier gates' findings all stay fixed.
The three post-report commits from 2026-09-23 are correct in direction: Fable
5.1's rates match the live pricing page to the cent, and rendering a model
missing from the rate table with the cost suppressed is the right call for an
audit tool, executed with one classification flaw. Two high findings keep this
from a clean PASS, and both are about the thing the plan says matters most, a
confidently wrong figure: `pricing.json` carries Sonnet 5 at $3 / $15 when the
list price is $2 / $10 (a scheduled increase Anthropic cancelled; 12 renderable
sessions in the store would price 1.5x too high, none published yet), and the
`--all` sweep aborts with a traceback when any exception escapes the parse
stage, so the batch's "still finishes the sweep" promise holds only for the
render stage. Neither is a core promise undelivered; both are a few lines to
fix. No critical finding, so the gate passes with findings.

## Test truthfulness

- `.claude/skills/audit-agent-conversation/run-tests` from the repo root:
  **Ran 401 tests, OK**, exit 0, on `/usr/bin/python3` 3.9.6. A clean `OK`,
  not `OK (skipped=N)`: the greenthumb corpus and the Fable 5.1 fixture session
  `017f2581` are both present, so every corpus-gated test ran. The noisy
  refusal, write-guard, and help-text output is expected and is not failure.
- Test count across the un-gated slice: 274 at the v1 gate (0a0318a), 343 at
  the end of the middle band (73322d1), 394 after the batch (6e68263), 401 at
  HEAD.
- **18 test functions were deleted across the slice.** Each deletion was paired
  with a behaviour change and a replacement test, not a dodge: the table layout
  rewrites (3865207, 623af13, 9f74865), "existing page is a skip" (334ebc8,
  replaced by `test_second_run_does_not_overwrite` plus `test_force_overwrites`
  in `tests/test_cli.py`), "walk within a date" (1f2e35f, replaced by
  `test_a_date_walks_within_that_day` and `test_a_date_never_walks_off_its_day`),
  "ai-title beats custom-title" (623af13, `test_ai_title_beats_custom_title`),
  the corpus census (606ebe7, see below), and the unknown-model change
  (8386572, judged below).
- **606ebe7 relaxed the hard 15/13 corpus split** that the v1 gate called
  load-bearing. Justified: the greenthumb directory grows nightly, so an
  absolute count is an environmental tripwire, not a test. The replacement
  still pins every named fixture to its side of the boundary, asserts every
  image-bearing file is refused, and asserts every refusal states a reason.
  Coverage of the property survived; only the snapshot went.
- **The ERROR-row feature is tested only through a monkeypatched
  `render.page`** (`tests/test_cli.py` `TestSweepErrorRows`). No test feeds the
  sweep a transcript that actually fails, which is exactly the gap that lets
  finding 2 pass green: the guard covers the one call site the test exercises.
- **`tests/test_corpus_sweep.py` no longer goes red on a model missing from the
  rate table.** The commissioning brief describes that coupling as current; it
  was true until 8386572 and is not now, because an unknown model exits 0.
  That is the right shape (the test's own docstring forbids environmental
  reds), but it means nothing at the test tier says whether `pricing.json`
  covers the fleet. The stderr warning is now the only signal.
- No `TODO`, `FIXME`, `HACK`, or `XXX` markers in the skill, the tests, or the
  wrapper. No emdashes in any phase file.

### The two 2026-09-23 judgment calls, scrutinised

**(a) A model missing from the rate table renders with cost suppressed plus a
CLI warning, instead of failing the page.** Correct, with two execution
defects. Correct because the token counts are real and the page states plainly
that the money is missing and why; because the warning survives `--quiet` and
`--stdout`; because `rates_for` still raises so nothing can quietly price at
zero; and because the alternative (16 Greenthumb sessions unrenderable until a
data edit) blocked a whole page over one figure. Verified adversarially: a
`claude-opus-5-5` page and an `x-ai/grok-4.6` page rendered with zero `$`
characters anywhere in the document and the warning printed on both. The
defects are findings 4 and 5: the "unknown" classification ignores what
`provider_for` already knows, so a routed OpenRouter model is nagged to "add
its list rates" against the batch's own decision; and a page rendered while a
model is unknown stays cost-less forever, because `--all` reports it as
EXISTS and the warning never says to re-render.

**(b) `test_a_genuinely_unknown_model_still_raises` was replaced rather than
kept.** Correctly followed a changed requirement; coverage was not weakened.
Keeping a test that asserts `compute()` raises would have contradicted the new
contract. The property it protected ("never a silent zero") survives in three
places: `test_unknown_model_raises_a_useful_error` still pins `rates_for`
raising with a message naming `pricing.json`; the replacement asserts
`priced is False`, `unknown is True`, the reason names `pricing.json`, and the
token counts are intact; and `TestModelMissingFromTheRateTable` in
`tests/test_cli.py` proves the page is written and the warning appears under
`--quiet`. The one missing lock: neither new test asserts the absence of a
dollar figure (`assertNotIn("$0.00", ...)`) the way the unpriced test does. My
check shows the property holds; the assertion is just not written (finding 11).

## Citation walk

Steps from `docs/plans/audit-log-followons-batch.md`, then the three late
commits, then the middle band mapped to roadmap follow-ons. The v1 plan's 15
steps and decisions A1 to A12 were walked by the four earlier reports and are
re-verified here only where later work touched them.

| Plan step | Satisfies | Status | Notes |
|---|---|---|---|
| Batch 0: rebuild output dir | precondition for Step 3 | satisfied | `~/.ai-staff-audit-log/` holds 164 pages plus `index.html`; zero `-to-workspace-` names and zero `<h1>` naming `workspace`; the 89 `-to-faw-` pages are the current mapped receiver, not a stale generation. |
| Batch 1: provider and model in the strip | roadmap follow-on 1 | satisfied | `cost.provider_for` (`cost.py:82-111`) is driven by the `providers` map plus the `claude-` prefix and `org/model` slug rules; `render.provider_and_model` (`render.py:234-246`) says `provider unknown` rather than guessing; no Ollama host is ever named. `tests/test_provider.py` covers every branch including the unknown case. But see finding 4: the same knowledge is not used by `cost.is_unknown`. |
| Batch 2: work log as aligned rows with duration | roadmap follow-on 2, duration half | satisfied | `parse.index_tool_result_times` / `previous_stamps` (`parse.py:596-631`) make every duration a subtraction of two stamps in the file; a call with no result is `None`, shown as a dash (`render.step_duration`). Six-column grid, `SAY` badge on narration, rotating arrow (`render.py:441-454`). `tests/test_durations.py` pins the synthetic 2.5s / 3s / 1s figures and the reference session's sanity bounds. Tokens per step are absent, as decided. |
| Batch 3: index of every session | roadmap follow-on 3 | satisfied, with a security finding | `index.scan` lists renderable and unsupported sessions, matches pages by the marker each page declares rather than by filename, sorts by start time with mtime as tie-break, and `write_index` goes through `check_destination` on both directory and target before any write (`cli.py:690-695`, proven by `test_refuses_to_write_inside_the_transcript_store`). Zero external requests, byte-reproducible, foreign `index.html` refused without `--force`. The copyable command is built from raw transcript fields: finding 3. |
| Batch 4: ERROR rows during a sweep | closes a dead affordance | partially satisfied | A `render.page` exception becomes an aligned `ERROR` row and the sweep continues (`cli.py:1030-1045`, verified). Any exception raised earlier in `render_one` (parse, describe, participants) is uncaught and aborts the whole run: finding 2. The plan's literal step is met; its stated intent ("still finishes the sweep") is not. |
| b4c48a4 Price Fable 5.1 | rate-table maintenance | satisfied | $10 / $50, cache writes $12.50 / $20, cache reads $0.25 (0.025x): matches the live pricing page exactly; 1M context carries no premium, so the `[1m]` alias is right. 113 sessions in the store run on it. `verified` date not bumped: finding 7. |
| 8386572 Render a missing model | A7 spirit (honest page over no page) | satisfied with findings | Judged above. Findings 4, 5, 11. |
| cda8e05 Cache-read multiple from the model's own rates | page honesty | satisfied | `render.py:778-781` divides the session's own rates; unpriced pages never reach the division. Tested on a real Fable 5.1 session (0.025x) and the Opus 5 reference (0.1x). A priced entry with a zero input rate would raise `ZeroDivisionError`, and the cache-multiples test passes an all-zero row: nit 12. |
| Middle band: `--all`, `--today`, `--week`, table output, `-v`, markers, sender/receiver, slug naming, name-clash disambiguation, path-tail `--project` (0a0318a..73322d1) | roadmap follow-ons and Scott's 2026-08-16 direction; v1 fix-list items 2 and 4 | satisfied | Never gated before. `disambiguate` (`cli.py:468-489`) closes the silent-drop of same-name sessions. `resolve.find_project` handles the parent-repository case and errors on ambiguity with the candidates named. The v1 fix list's wrapper-through-symlink test (`tests/test_wrapper.py:72-112`) and `agent_color` wiring (`render.AGENT_COLORS`, `TestAgentColor`) both landed in 0a0318a. The `--date` semantics changed to walking within the day; the code and tests agree, SKILL.md does not: finding 9. |
| v1 A9 (no model call, deterministic) | | still satisfied | `TestNoNetworkInTheRenderPath` bans the imports; the index adds none. Byte-reproducibility asserted for both page and index. |
| v1 A11 (transcript store unwritable, `--force`-proof) | | still satisfied | Write path unchanged since the v1 gate; `write_index` reuses the same guard. Re-checked by the write-safety suite (11 tests) plus the index refusal test. |
| v1 A12 (entrypoint-based sender) | | still satisfied | `resolve_participants` (`cli.py:154-190`) unchanged in substance; `Description` can stand in for a session so skip rows attribute the same way. |

## Drift findings

- **High** | `scripts/auditlog/pricing.json` `claude-sonnet-5` entry | The table
  prices Sonnet 5 at $3.00 / $15.00 with cache rates $3.75 / $6.00 / $0.30.
  The live pricing page (fetched 2026-09-23) lists Sonnet 5 at **$2.00 /
  $10.00**, cache $2.50 / $4.00 / $0.20, with a footnote that the $3 / $15
  figure was a scheduled September 1 increase that "will not occur". The entry
  arrived in 8996b64 with a commit message saying rates were "verified against
  the claude-api skill"; that skill's own table lists Sonnet 5 at $2 / $10, so
  the row was Sonnet 4.6's rates copied across, and the verification claim was
  false for this model on the day it was made. Blast radius: 17 sessions in the
  store have Sonnet 5 as their majority model, **12 are renderable by v1** (9
  in facet-admin-workspace, 3 in greenthumb), and every one would carry a total
  1.5x too high. None has been rendered yet (0 of the 164 published pages name
  Sonnet 5), so nothing wrong has been published; the next `--all` changes
  that. No test pins the rate, so the fix is a data edit. | Fix: set the five
  Sonnet 5 figures to the list price, bump `verified`, and re-check every row
  against the live page rather than the skill's cache while there.
- **High** | `scripts/auditlog/cli.py:1027-1045` (`render_one` under `--all`)
  | The ERROR-row guard wraps only `render.page`. `parse.load_session`,
  `parse.describe`, and `resolve_participants` run outside it, so an exception
  in any of them propagates through `run_sweep` and `main` as a traceback: the
  tally never prints, later candidates are never visited, and under
  `--all --index` the index is never built. Demonstrated in a fake projects
  tree with one transcript whose `message.usage` is a string:
  `accumulate_usage` (`parse.py:111`) raised `AttributeError`, the sweep died
  after two of six sessions. Garbage timestamps and a dict `content` did
  degrade gracefully, so the parser's tolerance is broad; the missing piece is
  that the sweep treats a parse failure as fatal when the batch plan says a
  failed session is "a row like any other outcome". Acceptance criterion 7
  ("graceful degradation on unknown types and missing fields") is the v1
  citation this weakens. | Fix: in the sweep path, wrap everything after
  `check_supported` (or the whole of `render_one`) in the same handler that
  emits the ERROR row, and add a test that feeds the sweep a genuinely
  malformed transcript rather than a monkeypatched renderer.
- **Medium** | `scripts/auditlog/index.py:65-76` (`Entry.command`) and
  `index.py:306-310` | The copyable command interpolates the transcript's
  `sessionId` and the project directory name raw and unquoted, and the page
  tells the reader to paste it into a terminal. A transcript whose `sessionId`
  is `dddddddd-0000; echo PWNED #` produced the copy payload
  `audit-agent-conversation dddddddd-0000; echo PWNED # --project ...`
  verbatim (reproduced in the scratchpad). The HTML side is safe (both
  `data-copy` and the visible `<code>` are escaped); the shell side is not.
  Exposure needs a crafted transcript in the store, which Claude Code itself
  will not write, but the earlier gates treated hostile transcript content as
  in scope and this is the first place a transcript field reaches a shell.
  Related edge: that session's page can never be matched by the index, because
  `_PAGE_SESSION` (`cli.py:452`) stops at the first character outside
  `[0-9a-fA-F-]`, so the row stays `TO DO` with the injected command forever. |
  Fix: accept a `sessionId` only when it matches the UUID shape the marker
  regex already encodes, else fall back to the transcript's file stem; pass the
  project name through `shlex.quote` (stdlib, 3.9-safe) or reject names outside
  `[A-Za-z0-9._-]`; test both.
- **Medium** | `scripts/auditlog/cost.py:211-239` (`is_unknown`, `compute`) |
  "Unknown" means "in neither list", but `provider_for` in the same module
  already knows an `org/model` slug is OpenRouter and a `claude-` prefix is
  Anthropic. Because `is_unknown` does not consult it, a routed model that is
  not hand-listed gets the Anthropic treatment: the page says it "is not in
  this tool's rate table yet; add its list rates to pricing.json" and the CLI
  warns to do so. Three such models are live in the store (`x-ai/grok-4.6`,
  `z-ai/glm-5.3`, `z-ai/glm-5.3-flash`, none renderable today), and the batch
  plan's "Not in this batch" table says OpenRouter rates are deliberately not
  carried, so the nag asks for something the design refuses. Two functions
  deriving "is this Anthropic" differently is the hand-maintained-pair shape
  the repo rules warn about. | Fix: derive unpriced-ness from
  `provider_for`: a slug is "reached through a routed non-Anthropic backend"
  without an entry, an unknown provider is unpriced with reason unknown, and
  only an Anthropic-prefixed miss is flagged `unknown` and warned about. Unit
  test each.
- **Medium** | `scripts/auditlog/cli.py:980-992` and the EXISTS path at
  `cli.py:1081-1088` | A page rendered while its model was unknown is a durable
  artifact with no cost figure. Once `pricing.json` is fixed, `--all` reports
  that page as EXISTS and never repairs it; the warning tells the reader to add
  rates but not to re-render with `--force`; and the EXISTS path emits no
  warning at all, so the second sweep is silent about it. The `claude-opus-5-5`
  session `82afa7be` (spruce, renderable, 142k output tokens) is the first live
  instance waiting to happen. | Fix: make the warning name `--force`; consider
  having the sweep treat a page whose head carries a suppressed-cost marker as
  stale when its model is now priced.
- **Low** | `scripts/auditlog/parse.py:49-57` (`Usage.model`) | Every token in
  a session is priced at the majority model's rate. 20 transcripts in the store
  carry two real models (one at 752 / 837 records between Fable 5 at $10 / $50
  and Opus 4.8 at $5 / $25). None is renderable by v1 today, so no wrong
  figure is reachable, which is why this is low; the multi-turn follow-on will
  make them renderable and this becomes high on that day. The data supports the
  right answer exactly: usage is already deduplicated per `message.id`, and
  each message names its model, so per-message pricing invents nothing. | Fix:
  accumulate tokens per model and sum the priced components; show the split in
  the cost table. Plan it alongside multi-turn.
- **Low** | `scripts/auditlog/pricing.json` `verified` | Still `2026-08-15`
  after Fable 5.1 was added on 2026-09-14, so every Fable 5.1 page says its
  rates were "checked 2026-08-15", a month before the entry existed. The
  field's whole purpose is that sentence. | Fix: bump on every rate edit;
  today's live check supports `2026-09-23`.
- **Low** | `scripts/auditlog/pricing.json`, `tests/test_cost.py:98-100`,
  `pricing.json` header comment | Opus 5.5 is a published model ($4 / $5 / $8
  / $0.20 / $20, cache reads 0.05x) with one renderable session in the store;
  add it. Doing so needs a third copy of the cache-read exception: the test's
  `CACHE_READ_EXCEPTIONS` dict, the header comment's "except claude-fable-5-1
  at 0.025x", and the data itself. | Fix: let each entry carry its own
  `cache_read_multiple` (default 0.1) and have the test derive from that;
  delete the comment's exception clause.
- **Low** | `SKILL.md` | Documentation rot from the middle band: lines 515-519
  say `--date` "means that session, so an unsupported one is refused rather
  than quietly swapped", but 1f2e35f made `--date` walk within the day and
  `test_a_date_walks_within_that_day` asserts it; the sample output at lines
  505-509 is the pre-table format; `--quiet` is described as suppressing "the
  summary line" where `--help` says the WROTE row; `-v` and `--no-header` are
  missing from the options table; "345 sessions across 42 projects" is a
  snapshot (707 files today); the version header still reads 1.0.0
  (2026-08-15) through a batch that changed the page and the CLI. | Fix: one
  pass over SKILL.md against `--help` and the tests.
- **Low** | `tests/test_cost.py:146-156`, `tests/test_cli.py:685-694` | The
  unknown-model tests assert the note and the warning but never assert the
  absence of a dollar figure, which is the property the change exists to
  protect. Verified true by inspection of two rendered pages (zero `$`). |
  Fix: add `assertNotIn("$0.00", ...)` and a no-`$`-in-tiles check, matching
  `test_unpriced_page_shows_no_dollar_figure`.
- **Nit** | `scripts/auditlog/render.py:780` | `%g` of
  `cache_read / input` raises `ZeroDivisionError` for a priced entry whose
  input rate is 0, and `test_cache_multiples_hold_for_every_model` accepts an
  all-zero row (0 == 0 x 0.1). Contrived; guard the division or reject a zero
  input rate in the table test.
- **Nit (persisting from v1)** | `tests/test_self_contained.py:47` | The
  mdpane stripper is still non-greedy. Cosmetic, cannot mask a dependency.
- **Informational (persisting from v1, accepted)** | `cli.py:1068-1103` |
  Residual parent-directory-swap TOCTOU between the realpath check and the
  `mkstemp`. Same threat-model reasoning as the v1 gate: a same-user attacker
  who can win it can already delete transcripts. No change.

Positive drift notes: no scope leakage outside the skill, `bin/`, `docs/`,
and the roadmap; runtime imports remain `argparse, datetime, errno, html,
json, os, re, sys, tempfile` plus function-local `zoneinfo`; the index adds
no JavaScript that reaches outside the page (`navigator.clipboard.writeText`
and an `execCommand('copy')` fallback only); `check_destination` is applied
to the index write exactly as to a page write.

## Security

Triage: **hit**. The slice touches file writes into a user directory (index
plus pages), parsing of transcript content that the earlier gates treated as
untrusted, HTML emission of that content in a new page (the index), and, new
this phase, construction of a shell command from transcript fields for the
reader to paste. Full review of the touched areas:

- **Transcript store is never written.** Re-verified: `write_index` and
  `render_one` both call `check_destination` on directory and target before
  `makedirs` or `mkstemp`; `--force` is not consulted by the guard; the index
  refusal test proves exit 7 with nothing created. The adversarial sweeps in
  this audit ran against a fake tree in the scratchpad; the real store was
  read only (`test_no_transcript_was_modified_by_the_sweep` also green).
- **Self-containment holds for both page kinds.** The index asserts the full
  dependency-pattern list plus no `http://` or `https://` anywhere, with no
  stripping, so it is the strongest form of the check.
- **HTML injection: closed on the index.** Every transcript-derived string
  reaching `index.py` markup goes through `html.escape` (`quote=True` on
  attributes: `data-text`, `data-copy`, `href`). Page-side escaping is
  unchanged since the v1 gate.
- **Shell injection via the copy button: OPEN.** Finding 3 above, with a
  reproduction. Severity medium because it needs a crafted transcript in the
  store and a reader who pastes without looking; the fix is a regex the code
  already has.
- **Denial of the whole sweep by one malformed file: OPEN.** Finding 2. Not an
  escalation, but a single transcript can stop the "what have my agents been
  doing" run and the index build.
- Path traversal via crafted data: closed (slugify plus timestamp prefix,
  unchanged). Symlinked targets: `os.replace` clobbers the link, unchanged.
  Secrets, subprocess, network: none in the runtime modules.

## Fix list (seeds the next planning session)

1. **Correct the Sonnet 5 rates** (high, `pricing.json`): $2.00 / $10.00,
   cache $2.50 / $4.00 / $0.20; bump `verified`; re-check every row against
   the live pricing page, not the skill's cache. Do this before the next
   `--all`.
2. **Make the sweep survive any per-session exception** (high,
   `cli.py:1027-1045`): widen the ERROR-row handler to cover parse, describe,
   and participant resolution; test with a real malformed transcript.
3. **Validate what goes into the index's copyable command** (medium,
   `index.py:65-76`): UUID-shape check on `sessionId` with a file-stem
   fallback, `shlex.quote` or a character allowlist on the project name;
   tests for both.
4. **Derive unknown-vs-unpriced from `provider_for`** (medium,
   `cost.py:211-239`): only Anthropic-prefixed misses warn "add rates"; slugs
   are routed backends; unknown providers are unpriced with reason unknown.
5. **Stop stale cost-less pages from persisting silently** (medium,
   `cli.py:980-992`): the warning names `--force`; consider marking suppressed-
   cost pages so a later sweep can repair them once the model is priced.
6. **Bump `verified` on every rate edit, and add Opus 5.5** (low): $4 / $5 /
   $8 / $0.20 / $20 with a 0.05x cache read; move the cache-read exception into
   the data (`cache_read_multiple`) so the test and the comment stop carrying
   copies.
7. **Price per message by model** (low now, high once multi-turn lands,
   `parse.py:49-57`): accumulate tokens per model and sum priced components.
8. **One documentation pass over SKILL.md** (low): `--date` semantics, the old
   sample output, `--quiet`, `-v`, `--no-header`, the corpus snapshot figure,
   the version header.
9. **Lock the no-dollar-figure property in the unknown-model tests** (low).
10. Nits: guard the `%g` division against a zero input rate; anchor the mdpane
    stripper; the accepted TOCTOU stays accepted.

## Gate handling

Verdict PASS_WITH_FINDINGS. No roadmap `PHASE GATE:` item exists for this
phase, so no checkbox is ticked. This report is the only file the gate writes.
Recommend a `/gameplan` session for items 1 to 5 before the audit-log
follow-ons resume; item 1 is a one-line data edit worth landing on its own.
