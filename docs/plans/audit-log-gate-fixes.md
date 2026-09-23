# Plan: Audit log gate fixes (findings 1 to 5)

## Execution Instructions

When executing this plan:

1. **Work step-by-step** - Complete each step fully before moving to the next
2. **Test-first within each step** - Write the failing test before the implementation, then make it pass
3. **Test after each step** - Run the test commands listed to verify the change works
4. **Commit after each step** - Use the provided commit message for each step
5. **Update documentation continuously** - `SKILL.md` where behaviour it documents changes; this plan's checkboxes; the roadmap at completion
6. **Mark completion** - When all steps are done, move this item from "Next Immediate Step" to "Completed" in the roadmap

The whole suite is one command from the repo root:

```bash
.claude/skills/audit-agent-conversation/run-tests
```

It should stay at or above 401 tests and exit 0. Its output is noisy on purpose:
several tests exercise refusals, the write guard and the CLI help text, and that
output is not failure.

---

## Summary

The 2026-09-23 phase gate on the audit log generator returned
PASS_WITH_FINDINGS. This plan lands its fix list items 1 to 5: two high, three
medium. Items 6 to 10 are deliberately out of scope and stay in the gate report
at [phasegate-audit-log-phase.md](../assessments/phasegate-audit-log-phase.md).

Every step here fixes a defect the gate demonstrated against real data rather
than a hypothetical, so every step starts with a test that reproduces it.

## Requirements

- Sonnet 5 sessions cost out at the real published rate before any page is
  written for one.
- A single bad transcript cannot abort an `--all` sweep, at any stage of
  `render_one`, not only inside `render.page`.
- Nothing a transcript contains can compose a shell command in the index page's
  copy button.
- "Add rates to pricing.json" is said only about models that could have
  Anthropic list rates.
- A page written with its cost suppressed can be repaired later, and the
  operator is told how.

## Non-Goals

- Fix-list items 7 to 10 (per-message pricing by model, the SKILL.md
  documentation sweep, the extra unknown-model assertion, the nits). They stay
  in the gate report.
- Item 6 is the exception, folded into Step 1 rather than deferred: Scott asked
  on 2026-09-23 for the whole table refreshed against the published page with
  Opus 5.5 added, and Opus 5.5 is the second exception to the 0.1x cache-read
  rule, which is what item 6 was about.
- Multi-turn rendering and everything else v1 refuses.

## Implementation Steps

### Step 1: Refresh the whole rate table against the published page

Scott's call, 2026-09-23: do the whole table, not just the one wrong row, and
add Claude Opus 5.5, released 2026-09-22. Rates below were read from
`https://platform.claude.com/docs/en/about-claude/pricing` on 2026-09-23, not
from any cached copy.

- [x] Write the failing test first: in `tests/test_cost.py`, assert the rates
      for `claude-opus-5-5` (4.00 / 20.00 / 5.00 / 8.00 / 0.20) and the
      corrected `claude-sonnet-5` (2.00 / 10.00 / 2.50 / 4.00 / 0.20). Both
      fail today: Opus 5.5 is absent, Sonnet 5 carries Sonnet 4.6's numbers.
- [x] Write the failing test first: assert the cache-read multiple comes from
      the table rather than from a list inside the test, so a third exception
      cannot silently diverge from what the page renders.
- [x] Implement: add `claude-opus-5-5` ($4 / $20, cache $5 / $8 / $0.20, a
      0.05x cache read) plus its `[1m]` alias; correct `claude-sonnet-5` to
      $2 / $10 with cache $2.50 / $4 / $0.20; add the rows the table has never
      carried but the corpus can produce: `claude-mythos-5-1` (same as Fable
      5.1, 0.025x cache read), `claude-opus-4-5` and `claude-sonnet-4-5`.
- [x] Implement: carry each row's cache-read multiple as data
      (`cache_read_multiple`, defaulting to 0.1) so `pricing.json` states it
      once and the test and the page note both read it, instead of three
      copies of the same fact.
- [x] Implement: bump `verified` to 2026-09-23 and change `source` to name the
      published pricing page rather than the skill's cached table, which is
      what made the Sonnet 5 error possible.
- [x] Verify green: the whole suite, plus a rendered Fable 5.1 page still
      saying 0.025x and an Opus 5 page still saying 0.1x.

**Satisfies:** gate fix-list item 1 (high), and item 6 (low), which this
supersedes: with two published exceptions to the 0.1x rule (Fable 5.1 at
0.025x, Opus 5.5 at 0.05x), keeping the exception list in the test was the
thing about to break again.

**Rates as published on 2026-09-23** (input / output / 5m write / 1h write /
cache read, dollars per MTok):

| Model | In | Out | 5m | 1h | Read |
|---|---|---|---|---|---|
| `claude-fable-5-1`, `claude-mythos-5-1` | 10 | 50 | 12.50 | 20 | 0.25 |
| `claude-fable-5`, `claude-mythos-5` | 10 | 50 | 12.50 | 20 | 1.00 |
| `claude-opus-5-5` | 4 | 20 | 5.00 | 8 | 0.20 |
| `claude-opus-5`, `4-8`, `4-7`, `4-6`, `4-5` | 5 | 25 | 6.25 | 10 | 0.50 |
| `claude-sonnet-5` | 2 | 10 | 2.50 | 4 | 0.20 |
| `claude-sonnet-4-6`, `4-5` | 3 | 15 | 3.75 | 6 | 0.30 |
| `claude-haiku-4-5-20251001` | 1 | 5 | 1.25 | 2 | 0.10 |

The 1M context window carries no premium on any of them, so every `[1m]` alias
prices off its base row. Sonnet 5's $2 / $10 is the standard price: the $3 / $15
increase scheduled for 2026-09-01 was cancelled, which is exactly what the stale
row had copied.

**File(s):** `.claude/skills/audit-agent-conversation/scripts/auditlog/pricing.json`, `.claude/skills/audit-agent-conversation/scripts/auditlog/cost.py`, `.claude/skills/audit-agent-conversation/tests/test_cost.py`

**Test:**
```bash
.claude/skills/audit-agent-conversation/run-tests
```

**Commit message:** `Refresh the rate table and add Claude Opus 5.5`

---

### Step 2: Make a sweep survive any per-session exception

- [x] Write the failing test first: in `tests/test_cli.py`, put a genuinely
      malformed transcript in a temp project directory (a record whose `usage`
      is a string, which is what killed a real sweep) alongside a good one, run
      `--all` over that project, and assert the exit code reports failure, the
      good session still rendered, an aligned `ERROR` row names the bad one,
      and the tally line is printed. It fails today with a traceback and no
      tally.
- [x] Implement: widen the failure handling in `render_one` so parse, describe
      and participant resolution are covered by the same ERROR-row path that
      `render.page` already has, rather than escaping to the top level.
- [x] Verify green: the new test passes; the existing monkeypatched-renderer
      test still passes unchanged.

**Satisfies:** gate fix-list item 2 (high), and the batch's own stated intent
that a sweep "still finishes"; the literal step was met while the intent was
not.

**File(s):** `.claude/skills/audit-agent-conversation/scripts/auditlog/cli.py`, `.claude/skills/audit-agent-conversation/tests/test_cli.py`

**Test:**
```bash
.claude/skills/audit-agent-conversation/run-tests
```

**Commit message:** `Keep a sweep going when a session fails outside the render`

---

### Step 3: Validate what reaches the index's copyable command

- [x] Write the failing test first: in `tests/test_index.py`, build an index
      from a session whose id carries shell metacharacters
      (`dddddddd-0000; echo PWNED #`) and a project name that does the same, and
      assert the rendered command contains no unquoted metacharacter that would
      run: a non-UUID id falls back to the file stem, and the project name is
      quoted or rejected. It fails today, which the gate demonstrated verbatim.
- [x] Implement: a UUID-shape check on `sessionId` with a file-stem fallback,
      and `shlex.quote` (or a character allowlist) on the project name, in
      `index.py`.
- [x] Verify green: the new test passes, the existing index tests still pass,
      and the page stays byte-reproducible.

**Satisfies:** gate fix-list item 3 (medium), Security section. The HTML side
is escaped; the shell side was not, and the page's own instruction is to paste
that line into a terminal.

**File(s):** `.claude/skills/audit-agent-conversation/scripts/auditlog/index.py`, `.claude/skills/audit-agent-conversation/tests/test_index.py`

**Test:**
```bash
.claude/skills/audit-agent-conversation/run-tests
```

**Commit message:** `Quote what a transcript contributes to the copy button`

---

### Step 4: Derive unknown-versus-unpriced from what provider_for knows

- [ ] Write the failing test first: in `tests/test_cost.py`, assert that a
      routed slug the table does not list (`x-ai/grok-4.6`) computes as
      unpriced, is NOT flagged `unknown`, and gives a reason naming a routed
      backend rather than telling the reader to add rates; and that an
      Anthropic-prefixed miss (`claude-not-a-real-model`) still is flagged
      `unknown` and still says `pricing.json`. The slug half fails today.
- [ ] Implement: have `is_unknown` consult `provider_for`, so only models that
      could carry Anthropic list rates warn about the table; everything else is
      unpriced with an honest reason.
- [ ] Verify green: new tests pass; the CLI warning test and the missing-model
      page test still pass.

**Satisfies:** gate fix-list item 4 (medium). Three live OpenRouter models in
the store currently get told to add list rates that deliberately do not exist,
contradicting the batch's own decision to carry no OpenRouter pricing.

**File(s):** `.claude/skills/audit-agent-conversation/scripts/auditlog/cost.py`, `.claude/skills/audit-agent-conversation/tests/test_cost.py`

**Test:**
```bash
.claude/skills/audit-agent-conversation/run-tests
```

**Commit message:** `Only warn about the rate table for models it could price`

---

### Step 5: Stop cost-less pages persisting silently

- [ ] Write the failing test first: in `tests/test_cli.py`, assert the
      missing-model warning names `--force` as the way to replace the page once
      the model is priced, and that a second sweep over an already-written
      cost-suppressed page still says so rather than reporting a bare `EXISTS`.
      It fails today: the warning never mentions `--force`.
- [ ] Implement: name `--force` in the warning, and carry the
      suppressed-cost fact into the row a later run prints for that page, so a
      sweep can be told what to repair.
- [ ] Verify green: new tests pass; the existing EXISTS-is-not-an-error test
      still passes unchanged.

**Satisfies:** gate fix-list item 5 (medium). One renderable `claude-opus-5-5`
session is the first live instance; without this, its page is wrong forever and
silently.

**File(s):** `.claude/skills/audit-agent-conversation/scripts/auditlog/cli.py`, `.claude/skills/audit-agent-conversation/tests/test_cli.py`

**Test:**
```bash
.claude/skills/audit-agent-conversation/run-tests
```

**Commit message:** `Say how to repair a page written without a cost figure`

---

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `scripts/auditlog/pricing.json` | 1 |
| `scripts/auditlog/cli.py` | 2, 5 |
| `scripts/auditlog/index.py` | 3 |
| `scripts/auditlog/cost.py` | 4 |
| `tests/test_cost.py` | 1, 4 |
| `tests/test_cli.py` | 2, 5 |
| `tests/test_index.py` | 3 |

All paths are relative to `.claude/skills/audit-agent-conversation/`.

## After this plan

The gate's items 6 to 10 remain open in
[phasegate-audit-log-phase.md](../assessments/phasegate-audit-log-phase.md). A
second gate runs over these five fixes once they are merged.
