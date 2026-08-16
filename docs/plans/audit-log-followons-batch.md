# Plan: Audit log follow-ons, unattended batch

## Execution Instructions

**RUN THIS UNATTENDED. Do not stop between steps to ask for approval.** Scott
is away and wants the whole batch done before he looks at anything. Work
straight through Steps 0 to 4, then report once.

### Branch: this plan runs where it already is

This plan belongs to the **existing `feature/audit-log` branch**, in the
worktree at `~/src/scottwb/dotfiles-audit-log`.

If you arrived via `/yolo`, this is **State 2 (resume)**: do NOT create a
branch, and do not treat the branch name as a mismatch. `/yolo`'s state check
matches a branch against a plan's filename stem, and `feature/audit-log` does
not contain `audit-log-followons-batch`; that is expected and is not a reason to
stop. The branch already carries 44 commits of the work this batch extends.

### Per step

1. **Test-first** - Write the failing test before the implementation, then make it pass
2. **Check the EXIT CODE, not the output** - An earlier session pushed a red suite because a `&&` chain keyed off `grep` matching the word FAILED:
   ```bash
   cd .claude/skills/audit-agent-conversation && ./run-tests > /tmp/t.log 2>&1
   echo "exit=$?"; grep -E "^(Ran|OK|FAILED)" /tmp/t.log
   ```
3. **Commit and push** - Use the provided commit message, then `git push origin feature/audit-log`
4. **Tick as you go** - This plan's checkboxes, `SKILL.md` for anything user-facing, and the matching roadmap follow-on
5. **Continue immediately** - No waiting, no confirmation

### When to stop early

Stop and report, leaving the work uncommitted, if:

- A step's tests still fail after three root-cause attempts. Do not note it and
  carry on; later steps built on a broken foundation compound the damage.
- A step turns out to need a decision this plan does not already make. Half-
  landed work is worse than a short batch. Say what you hit and why.

Otherwise finish the batch.

### Hard stops

**Do not merge. Do not run `/yolo`'s wrap-up half. Do not delete the branch or
the worktree. Do not close PR #4.** Scott reviews, tests, and merges himself.
Everything stays exactly where it is.

---

## Context

Everything below builds on work that is already committed, pushed, and
manually tested by Scott.

| | |
|---|---|
| Branch | `feature/audit-log`, 44 commits ahead of `master`, 0 behind |
| Worktree | `~/src/scottwb/dotfiles-audit-log` |
| PR | https://github.com/scottwb/dotfiles/pull/4 (draft, deliberately unmerged) |
| Suite | 343 tests, green on stock `/usr/bin/python3` (3.9.6) |
| Gates | Four Fable-tier reports in `docs/assessments/`, final verdict PASS |
| Scott's testing | Passed. Pages, CLI, refusals, safety rail, suite, docs. |

Read before starting:

- `docs/plans/audit-log-generator.md` for decisions **A1 to A12** and findings
  **F1 to F8**. A11 (nothing may write inside `~/.claude/projects/`) and A9 (no
  model call in the render path) are the two that constrain this batch.
- `docs/plans/development-roadmap.md`, the "Audit log generator follow-ons"
  item, which is the source of the four steps below.

---

## Step 0: Rebuild the output directory

`~/.ai-staff-audit-log/` holds several generations of pages. Two naming changes
landed after most of them were written (`ai-title` preferred over
`custom-title`, and receivers named from the session's `cwd`), and because both
changed FILENAMES, re-rendering wrote new files instead of replacing the old
ones. The directory currently holds 84 pages named `...-to-workspace-...` and 83
named `...-to-faw-...` for the same sessions.

- [x] Test-first: n/a (operational, no product code changes)
- [x] Confirm with `ls ~/.ai-staff-audit-log | wc -l` and note the count
- [x] `rm -rf ~/.ai-staff-audit-log`
- [x] `./bin/audit-agent-conversation --all --force`
- [x] Confirm no page's `<h1>` names a stale participant:
      `grep -l '<h1>.*workspace</h1>' ~/.ai-staff-audit-log/*.html` returns nothing
- [x] Confirm the three Lumbergh sessions that the filename-collision bug had
      dropped are now present (the sweep should report more written than the
      old directory had distinct names)

**Satisfies:** cleanup, and a precondition for Step 3: an index of a directory
holding three generations of naming would index fiction.

**File(s):** none tracked. This changes only `~/.ai-staff-audit-log/`.

**Commit message:** n/a, nothing tracked changes. Do not commit this step.

---

## Step 1: Provider and model in the stats strip

Show what actually served the conversation, not just the model:
`Anthropic / claude-fable-5`, `Ollama / glm-4.7-flash`,
`OpenRouter / gpt-5.6-sol`.

**Measured, do not re-litigate:** transcripts record NO provider, base URL, or
endpoint. Every top-level field on real routed sessions was checked. Provider
must be inferred from the model id, which `pricing.json` already does to decide
what is unpriced. **Which Ollama host served a session is not recoverable** and
must not be guessed; say the provider and stop.

- [x] Write the failing test first: `tests/test_provider.py` asserts
      `claude-*` maps to Anthropic, `glm-4.7-flash` and `qwen3:30b-a3b` to
      Ollama, `openai/*` to OpenRouter, `<synthetic>` to the harness itself,
      and an unknown model to something honest rather than a guess
- [x] Implement: a `provider_for(model)` in `cost.py` or a new small module,
      driven by the same table that already knows which models are unpriced
- [x] Implement: surface it in the rendered page's provenance strip beside the
      model
- [x] Write the failing test first: the rendered reference page names both the
      provider and the model
- [x] Verify green

**Satisfies:** roadmap follow-on 1 (tier "Do first")

**File(s):** `scripts/auditlog/cost.py` (or a new `provider.py`),
`scripts/auditlog/pricing.json`, `scripts/auditlog/render.py`, `tests/`

**Commit message:** `Name the provider alongside the model`

---

## Step 2: Work log as an aligned table, with per-step duration

Scott's spec, from 2026-08-16:

> the "+" on the right becomes a rotating right-or-down arrow for
> expand/collapse, then the timestamp, then the badge - and we should have a
> badge for the ones that are blockquote-italic style thinking-out-loud
> responses so that every kind of row here has a badge - and since we are going
> table-like layout alignment-wise the badges are all the same width or
> otherwise all align left and the next "column" is left-aligned tool, then the
> main content like "Read rules.md" and the sub-content like "Opened a file"
> that you already have there....then right-floated/justified last columns

**Build the layout and the duration. Do NOT build tokens or tokens/sec.** See
"Not in this batch" below; that half has no honest answer yet.

Durations are free and unambiguous: a tool call's wall clock is the gap between
the record carrying its `tool_use` block and the record carrying the matching
`tool_result`. Measured on a real brief this yields 0.00s to 0.66s per call. A
reasoning step's duration is the gap to the previous record.

- [ ] Write the failing test first: the session model exposes a duration per
      tool event, and the reference session's values are sane (non-negative,
      and the sum does not exceed the session's wall clock)
- [ ] Implement: per-event duration in `parse.py`
- [ ] Write the failing test first: every work-log row carries a badge,
      including narration rows, and the rendered page contains a duration cell
      per tool row
- [ ] Implement: the row layout in `render.py` and its CSS, with the disclosure
      arrow rotating on open
- [ ] Verify green, then render the reference session and look at it

**Satisfies:** roadmap follow-on 2 (tier "Do first"), duration half only

**File(s):** `scripts/auditlog/parse.py`, `scripts/auditlog/render.py`, `tests/`

**Commit message:** `Lay the work log out as rows with a duration column`

---

## Step 3: Index page of every conversation there is to render

The largest item in this batch. Scott's spec, from 2026-08-16: an index of what
EXISTS to render, not of what has been rendered.

- Scans the project directories and lists every conversation across the fleet,
  newest first.
- Marks each row generated or not. Generated rows link to their page.
- **Ungenerated rows expand** to show the command that would produce them, with
  a copy button that puts just the prompt on the clipboard. Paste it into a
  Claude session, refresh the index, and the row becomes a link.
- **Deliberately not a web app.** Nothing on the page executes anything. The
  copy button is a clipboard write; the generating happens in a session the
  user drives. It stays a static file with no server, no auth, and no path from
  the index back to the transcript store. A row that generates itself on click
  is a different product and is parked.

Most of the scan already exists: `cli.classify()` returns a support report and a
`Description` for any transcript, cheaply, and `sweep_candidates()` already
walks every project with an optional time window.

- [ ] Write the failing test first: the index lists both renderable and
      unsupported sessions, marks which have pages on disk, and links only
      those
- [ ] Implement: `index.py` producing a single self-contained HTML page
- [ ] Write the failing test first: the page makes zero external requests and
      contains no `<script src>`, matching `test_self_contained.py`'s rules
- [ ] Write the failing test first: an ungenerated row carries a copy-able
      command naming that session
- [ ] Implement: the `--index` flag (or an `index` subcommand) writing to
      `~/.ai-staff-audit-log/index.html`, subject to the same
      `check_destination` guard as every other write
- [ ] Verify green, then open the index and click through to a page

**Satisfies:** roadmap follow-on 3 (tier "Do first")

**File(s):** `scripts/auditlog/index.py`, `scripts/auditlog/cli.py`, `tests/`

**Commit message:** `Add an index of every conversation there is to render`

---

## Step 4: Emit ERROR rows during a sweep

The red marker is defined and nothing uses it. During `--all`, a render failure
is counted in the tally but never appears as a row, so the one outcome a reader
most needs to see is the one that stays invisible.

- [ ] Write the failing test first: a sweep containing a session that fails to
      render emits an `ERROR` row naming it, and still finishes the sweep
- [ ] Implement: emit the row from `render_one`'s failure path when
      `args.all`, the same way refusals already emit a `SKIPPED` row
- [ ] Verify green

**Satisfies:** closes a dead affordance introduced with the marker set

**File(s):** `scripts/auditlog/cli.py`, `tests/`

**Commit message:** `Show failures as rows during a sweep, not just in the tally`

---

## Not in this batch, and why

Do not build these. Each was considered and deferred for a stated reason; a
fresh session that "helpfully" adds one is undoing a decision.

| Item | Why not |
|---|---|
| **Per-step tokens and tokens/sec** | **No honest answer exists yet.** Token counts are per API message, and one message's usage covers up to 8 work-log rows (measured). There is no per-tool-call token count in the data, so dividing invents a number, which is precisely the error the golden test exists to catch. Three options are written up in the roadmap. Scott decides. |
| **Multi-turn rendering** | Structural, changes the whole page shape, wants design conversation |
| **Image blocks** | Thumbnail vs placeholder vs size cap is a taste call |
| **Scale and size budget** | Needs threshold numbers Scott will have opinions about |
| **Subscription-share cost** | Blocked on a number that does not exist publicly: Anthropic publishes no monthly token allotment, so the divisor must be chosen, not derived |
| **OpenRouter pricing** | Current rates cannot be verified offline; guessing them produces confidently wrong money |
| **Retention policy** | What to keep and for how long is Scott's call |
| **`--annotate`** | Deferred by design, and puts a model near the render path against A9 |
| **`--all` allowlist/blocklist** | Decision-free but solves no current pain: 42 projects sweep in 3 seconds. Adding config surface now is inventory |
| **Fleet dashboard** | Parked, likely post-Smykowski |
| **Recovering reasoning text** | Research only, explicitly not a build |

---

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `scripts/auditlog/cost.py` or `provider.py` | 1 |
| `scripts/auditlog/pricing.json` | 1 |
| `scripts/auditlog/parse.py` | 2 |
| `scripts/auditlog/render.py` | 1, 2 |
| `scripts/auditlog/index.py` | 3 |
| `scripts/auditlog/cli.py` | 3, 4 |
| `tests/*.py` | 1, 2, 3, 4 |
| `SKILL.md` | 1, 2, 3 |
| `docs/plans/development-roadmap.md` | 1, 2, 3 |

## When the batch is done

Report ONCE, at the end, with:

- What landed, step by step, with commit hashes
- **What Scott should look at with his own eyes.** Steps 2 and 3 are visual;
  only he can say they look right. Give him the exact commands and file paths.
- Anything stopped rather than finished, and why
- The suite count and its exit status

Then stop. The merge is Scott's.
