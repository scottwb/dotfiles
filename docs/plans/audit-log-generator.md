# Plan: Inter-Agent Conversation Audit Log Generator

## Execution Instructions

When executing this plan:

1. **Work step-by-step** - Complete each step fully before moving to the next
2. **Test-first within each step** - Write the failing test/scenario before the implementation, then make it pass
3. **Test after each step** - Run the test commands listed to verify the change works
4. **Commit after each step** - Use the provided commit message for each step
5. **Update documentation continuously** - After ANY change that affects them, update:
   - `.claude/skills/audit-log/SKILL.md` - User-facing skill documentation
   - `docs/plans/audit-log-generator.md` - Mark progress, update status
   - `docs/plans/development-roadmap.md` - Mark progress, update status
6. **Mark completion** - When all steps are done, move this item to "Completed" in the roadmap

**Constraints specific to this plan**, from the handoff that commissioned it:

- **Never merge this branch and never re-run `/yolo` after the build completes.**
  Re-running `/yolo` triggers its merge-and-wrap-up half. Run it once, to build.
- **Never write to `~/.claude/projects/`.** Transcripts are the only copy and are
  gitignored. The tool is read-only against them, always.
- **Do not touch the main checkout.** It holds unrelated uncommitted work. All
  work happens in the `../dotfiles-audit-log` worktree.
- The skill is **not live during development**, because `~/.claude` symlinks to
  the main checkout rather than the worktree. This is deliberate: nothing built
  here can affect a live session before review. Test the script by path.

---

## Summary

From any Claude Code session, run a skill and get a self-contained HTML audit log
page for a given session transcript, written to `~/.ai-staff-audit-log/`.

The page renders the opening prompt, the work log, the reply, derived side
effects, and a real cost breakdown. The work log is hidden by default so the page
opens as a readable dialog; one button reveals it. Markdown-bearing tool results
carry a raw/preview toggle whose both panes are rendered at build time, so no
markdown parser ships with the page.

This generalizes a one-off script that produced `~/donna-greenthumb.html` by hand
for a single Donna to Greenthumb exchange. That prototype is committed on this
branch at `inter-agent-prompt-audit-log-generator-prototype.py` as reference
material. Its parsing, cost math, markdown renderer, and CSS are worth keeping;
its hardcoded participant names, hardcoded side-effect prose, and module-level
path constants are exactly what this plan replaces.

## Decisions

Settled before planning. Steps cite these by ID.

| ID | Decision |
|---|---|
| **A1** | **Skill-owned implementation with a thin `bin/` wrapper.** Python modules under `.claude/skills/audit-log/scripts/`, plus `bin/audit-log` exec'ing into them. The skill is the unit of ownership; the wrapper exists so the CLI is usable without the skill. Scott's call 2026-08-15. |
| **A2** | **Flat output directory, chronological filenames**, `YYYYMMDD-HHMM-<from>-to-<to>-<slug>.html`, no session-id suffix. Plain `ls` sorts chronologically; `ls *-donna-to-*` filters by initiator. Scott's call 2026-08-15. |
| **A3** | **New roadmap thread, "AI Staff."** First tool *about* the agent fleet rather than part of it. Scott's call 2026-08-15. Already applied to the roadmap. |
| **A4** | **stdlib `unittest`, Python 3.9 baseline**, targeting Apple's stock `/usr/bin/python3`. Zero install, zero dependencies, no venv, no homebrew interpreter. Runtime stays stdlib-only, matching the prototype and the "minimize installation friction" rule. Scott's call 2026-08-15. Consequence: no `match` statements, no `X | Y` union syntax, no `tomllib`. `zoneinfo` IS available (3.9) and should be used instead of the prototype's hardcoded `-7` offset. |
| **A5** | **`--from` resolves through a project-directory map**, with a `--from` flag override and a default of `scott` for interactive sessions. Nothing in a transcript records the initiator, so this is a config question, not a parsing one. |
| **A6** | **Output goes to `~/.ai-staff-audit-log/`**, created if missing, never source controlled, never inside the dotfiles repo, never deleted from. Settled in the handoff, not reopened. |
| **A7** | **v1 refuses rather than half-renders.** Multi-turn, image-bearing, and oversized sessions exit non-zero with a clear message naming the specific unsupported condition and its magnitude. A clean refusal is a v1 deliverable; building the feature is not. |
| **A8** | **The prototype is deleted and the handoff is relocated** in the final step. Both were committed in `3116bde` first, so both survive in branch history. The repo root does not stay cluttered. |
| **A9** | **No model call in the render path, ever.** The optional `--annotate` enrichment pass is deferred entirely to follow-on work. Rendering is deterministic and byte-reproducible. |

## Findings that shape the design

Verified by measurement on 2026-08-15 against the 28-file greenthumb corpus,
**not** taken on faith from the handoff. Three of these correct it.

### F1. One record per content block, and every record repeats the whole message's usage

This is the defect that cost real time to find, and the reason the golden test
exists. An assistant message with a thinking block, a text block, and two
`tool_use` blocks becomes four records, each carrying identical `output_tokens`,
`input_tokens`, and `cache_read_input_tokens`.

Measured on the reference session: naive per-record summation yields **41,302**
output tokens against a true **16,179**, a 2.5x overcount. The session is 27
assistant records but only **8 API calls** (the handoff says 26; the measured
count is 27, and the token figures are unaffected). Deduplicating on `message.id` before
summing usage is load-bearing.

### F2. The daily briefs carry TWO leading user records, and a naive turn count refuses all of them

**This corrects the handoff.** A slash-command session opens with a pair:

| Record | Shape | `parentUuid` | `isMeta` | Content |
|---|---|---|---|---|
| first | bare string | `null` | absent | `<command-message>exec-brief</command-message>...` |
| second | `[{type: text}]` | set | **`true`** | The expanded command body, ~2 KB of instructions |

A multi-turn detector that counts every non-`tool_result` user record sees **2
turns** on every one of the target sessions and refuses the entire corpus the
tool exists to render.

**`isMeta: true` is the discriminator.** Excluding `isMeta` records yields
exactly 1 turn on all 15 renderable sessions and 2 to 76 on the rest. The same
rule fixes the opening-prompt resolver: the opening prompt is the first `user`
record that is not `isMeta` and carries no `tool_result` blocks.

### F3. `agent-name` is absent from every session in the target corpus

**This corrects the handoff**, which described `agent-name` as solving half the
attribution problem for free. It does carry the agent's identity outright, and it
should be used when present, but it appears in only 4 of 28 files and **none of
them are the daily briefs**. Attribution for the target corpus must come from the
project-directory map and the `--to` flag (A5). `agent-name` is an optimization,
not the mechanism.

### F4. `ai-title` is absent from the daily briefs too

Present on the reference session (8 identical records, field name `aiTitle`) and
on most interactive sessions, but **not on the 12 `/exec-brief` briefs**. The
slug generator therefore needs a fallback chain, not a single source:
`custom-title`, then `ai-title`, then the unwrapped slash-command invocation
(`exec-brief-full`), then a date-derived last resort.

### F5. `queue-operation` carries the original prompt verbatim

Undocumented in the handoff. The first record of every session in this corpus is
`{"type": "queue-operation", "operation": "enqueue", "content": "..."}` holding
the prompt exactly as submitted, before any slash-command expansion. Useful as a
corroborating source and as the cleanest slug input.

### F6. The corpus splits cleanly at the refusal boundary

| Verdict | Count | Which |
|---|---|---|
| Renders | **15** | 12 `/exec-brief` briefs, the reference session, and 2 smaller SDK sessions |
| Refused, multi-turn | 13 | 2 to 76 turns |
| Refused, images | 8 | 1 to 33 image blocks each (handoff said 3 files; a top-level-only scan finds 4; counting images nested inside `tool_result` content, which need rendering too, finds 8) |
| Refused, oversized | 5 | 9.9 MB to 44.0 MB |

Refusals overlap; the largest session trips all three. The detector must report
every condition it found, not just the first.

### F7. Record types beyond the handoff's list

`command_permissions` and `task_reminder` appear as `attachment` subtypes, and
neither is in the handoff's enumeration. This confirms the enumeration is
open-ended and that unknown types must be skipped without crashing rather than
matched exhaustively.

### F8. Golden figures reproduce exactly

All four fixture sessions reproduce the handoff's stated numbers to the cent
under `message.id` dedupe, which validates both the fixtures and the method.

## Requirements

- Deduplicate usage on `message.id`; never sum per record.
- Reproduce the Section 6 golden figures exactly for the reference session.
- Resolve the opening prompt whether `promptSource` is `sdk`, `None`, or absent.
- Unwrap slash-command XML to a readable invocation.
- Derive every side effect and stat tile from the transcript; hardcode nothing.
- Refuse multi-turn, image-bearing, and oversized sessions with a clear message
  and a non-zero exit, naming every condition found.
- Skip unknown record types without crashing; handle both string and list
  `message.content` everywhere.
- Emit one self-contained HTML file making zero external requests.
- Write to `~/.ai-staff-audit-log/`, creating it if absent, never overwriting
  without `--force`.
- Never write to `~/.claude/projects/`.
- Runtime is stdlib-only on Python 3.9.

---

## Implementation Steps

## Phase 1: Parser, session model, and the regression tests

### Step 1: Package skeleton and test harness

- [x] Write the failing test first: `tests/test_smoke.py` imports
      `auditlog.parse` and asserts the package's `__version__` is a string.
      Fails with `ModuleNotFoundError` before the package exists.
- [x] Implement: create `.claude/skills/audit-log/scripts/auditlog/__init__.py`
      with `__version__`, and empty `parse.py`, `render.py`, `resolve.py`,
      `cost.py`, `cli.py` modules
- [x] Implement: create `.claude/skills/audit-log/tests/` with a
      `conftest`-free layout (stdlib `unittest`, no pytest per A4)
- [x] Implement: add `.claude/skills/audit-log/run-tests`, an executable shell
      script running `python3 -m unittest discover -s tests -t . -v` from the
      skill directory, so the test command is one word and not a path puzzle
- [x] Implement: add a `FIXTURES` constant resolving `~/.claude/projects/` by
      absolute path, never by a worktree-relative path (Section 1 gotcha)
- [x] Verify green: run the test command below

**Satisfies:** A1 (skill-owned layout), A4 (stdlib unittest on 3.9)

**File(s):** `.claude/skills/audit-log/scripts/auditlog/*.py`,
`.claude/skills/audit-log/tests/test_smoke.py`,
`.claude/skills/audit-log/run-tests`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
python3 -c "import sys; assert sys.version_info[:2] >= (3,9)"
```

**Commit message:** `Scaffold the audit-log skill package and its test harness`

---

### Step 2: Rate table and cost math

- [x] Write the failing test first: `tests/test_cost.py` feeds the reference
      session's known token bundle (input 3,543 / cache_write_1h 89,150 /
      cache_write_5m 0 / cache_read 529,482 / output 16,179 / reasoning 9,316)
      and asserts input side `$1.1740`, output `$0.4045`, reasoning `$0.2329`,
      total `$1.5784`. Also asserts **reasoning is not added to the total**, by
      checking `total == input_side + output` exactly.
- [x] Implement: `pricing.json` keyed by model ID, with `claude-opus-5` at
      input $5.00, output $25.00, cache write 5m $6.25, cache write 1h $10.00,
      cache read $0.50 per million, plus a `verified` date field
- [x] Implement: `cost.py` loading the table and computing a cost breakdown from
      a token bundle, with an explicit `reasoning_is_subset_of_output = True`
      contract expressed in code rather than a comment
- [x] Implement: an unknown model ID raises a clear error naming the model and
      the file to add it to, rather than silently costing at zero
- [x] Verify green: run the test command below

**Satisfies:** Requirement "reproduce the golden figures", F8

**File(s):** `.claude/skills/audit-log/scripts/auditlog/cost.py`,
`.claude/skills/audit-log/scripts/auditlog/pricing.json`,
`.claude/skills/audit-log/tests/test_cost.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
```

**Commit message:** `Add the maintained rate table and cost math, with the golden cost test`

---

### Step 3: Record loading and the usage dedupe (THE regression test)

- [x] Write the failing test first: `tests/test_usage_dedupe.py` parses the
      reference session and asserts **8** API messages and the exact six token
      figures. A second test in the same file asserts that a deliberately naive
      per-record summation yields **41,302** output tokens, documenting the
      2.5x overcount the dedupe prevents. The first test fails against a naive
      implementation; the second is the guard that keeps the reason visible.
- [x] Implement: `parse.py` JSONL loader tolerating blank lines and skipping
      malformed lines with a counted warning rather than crashing
- [x] Implement: usage accumulation deduplicated on `message.id`, reading
      `input_tokens`, `cache_creation.ephemeral_1h_input_tokens`,
      `cache_creation.ephemeral_5m_input_tokens`, `cache_read_input_tokens`,
      `output_tokens`, and `output_tokens_details.thinking_tokens`
- [x] Implement: skip unknown record types by default; never match exhaustively
      (F7)
- [x] Verify green: run the test command below

**Satisfies:** F1, F7, Requirement "deduplicate usage on `message.id`"

**File(s):** `.claude/skills/audit-log/scripts/auditlog/parse.py`,
`.claude/skills/audit-log/tests/test_usage_dedupe.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
```

**Commit message:** `Deduplicate usage on message.id, with the golden token regression test`

---

### Step 4: Opening-prompt resolution and slash-command unwrapping (Defects 1 and 2)

- [x] Write the failing test first: `tests/test_opening_prompt.py` asserts three
      things, each failing against the prototype's behavior:
      (a) the reference session (`promptSource: "sdk"`) resolves its prompt;
      (b) a daily brief (`promptSource: None`) **also** resolves, where the
      prototype raises `TypeError` on `last_ts - first_ts`;
      (c) the `isMeta: true` command-expansion record is **not** chosen as the
      opening prompt.
      A fourth test asserts the XML unwraps to exactly `/exec-brief full`, not
      the literal `<command-message>` markup.
- [x] Implement: opening-prompt resolver selecting the first `user` record that
      is not `isMeta` and carries no `tool_result` blocks, preferring
      `parentUuid: null` when available, and working whether `promptSource` is
      `sdk`, `None`, or absent
- [x] Implement: slash-command unwrapper turning the XML triple into
      `/<name> <args>`, retaining the raw form on the model for the
      raw/preview affordance
- [x] Implement: retain the `isMeta` expansion body on the session model as the
      expanded command text, since it is the real instruction the agent acted on
      and is worth rendering behind a disclosure
- [x] Verify green: run the test command below

**Satisfies:** Defect 1, Defect 2, F2

**File(s):** `.claude/skills/audit-log/scripts/auditlog/parse.py`,
`.claude/skills/audit-log/tests/test_opening_prompt.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
```

**Commit message:** `Resolve the opening prompt regardless of promptSource, and unwrap slash commands`

---

### Step 5: Unsupported-case detection and honest refusal

- [x] Write the failing test first: `tests/test_refusal.py` walks the whole
      greenthumb corpus and asserts the split measured in F6: **15 renderable,
      13 refused**, with multi-turn counts of 2 to 76, image counts of 1/3/6/21
      across 4 files, and the 5 oversized files. A dedicated test asserts that
      **every one of the 12 `/exec-brief` briefs is renderable**, which is the
      test that fails if `isMeta` is not excluded from the turn count.
- [x] Implement: turn counter excluding `isMeta` records and `tool_result`-only
      user records (F2)
- [x] Implement: an `UnsupportedSession` exception carrying **all** conditions
      found, not just the first, each with its magnitude
- [x] Implement: a sidechain detector that records whether any `isSidechain`
      record was seen and warns rather than mis-rendering (none exist in this
      corpus, so this is a tripwire, not a feature)
- [x] Implement: refusal messages of the shape `this session has 44 user turns;
      multi-turn rendering is not implemented yet`, naming the condition and the
      number
- [x] Verify green: run the test command below

**Satisfies:** A7, F2, F6, Requirement "refuse ... naming every condition found"

**File(s):** `.claude/skills/audit-log/scripts/auditlog/parse.py`,
`.claude/skills/audit-log/tests/test_refusal.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
```

**Commit message:** `Detect unsupported sessions and refuse them cleanly, counting real turns only`

---

### Step 6: The normalized session model

- [x] Write the failing test first: `tests/test_session_model.py` asserts the
      reference session yields its known shape: the event sequence
      (thinking / say / tool), the tool-call count, a reply whose word count
      matches, and populated provenance (cwd, branch, model, effort, CLI
      version, permission mode). A parallel test asserts brief `9608087e` has a
      **1,356-word** reply, `bd35db69` **1,523**, and `d3a49460` **1,056**, the
      cheap smoke assertion that the reply extractor found the right block.
- [x] Write the failing test first: a graceful-degradation test feeding a
      synthetic transcript containing an unknown record type, a bare-string
      `message.content`, and a missing `agent-name`, asserting it parses without
      raising
- [x] Implement: session model with participants, provenance, timing, token
      bundle, ordered events, and the final reply
- [x] Implement: `tool_result` lookup by `tool_use_id`, handling both string and
      list `content` shapes
- [x] Implement: derived side effects, counted from observed tool calls, never
      hardcoded: git commits, file writes, file reads, external/MCP calls
      (Defect 3)
- [x] Implement: timestamps via `zoneinfo.ZoneInfo("America/Los_Angeles")`
      rather than the prototype's hardcoded `-7` offset, which is wrong half the
      year (A4)
- [x] Verify green: run the test command below

**Satisfies:** Defect 3 (the derived half), F3, F8, Requirement "skip unknown
record types"

**File(s):** `.claude/skills/audit-log/scripts/auditlog/parse.py`,
`.claude/skills/audit-log/tests/test_session_model.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
```

**Commit message:** `Build the normalized session model with derived side effects`

---

> **PHASE GATE: audit-log parser.** Run `/phasegate`. The phase promised a parser
> that reproduces the golden figures exactly, fixes all three prototype defects
> with tests that fail against the prototype's behavior, and refuses unsupported
> sessions rather than half-rendering them. Verify each claim against the tests,
> not the prose.

---

## Phase 2: Renderer

### Step 7: Port the markdown renderer

- [ ] Write the failing test first: `tests/test_markdown.py` covers headings,
      fenced code, tables with a delimiter row, **headerless pipe-row runs**
      (the grep-fragment case), `\|` escapes inside cells, ordered and unordered
      lists, blockquotes, strikethrough, inline code, bold, italic, and the
      line-number stripping for both `   12\t` (Read) and `12:` (grep -n)
      prefixes. Also asserts Obsidian `[[path|alias]]` resolves to `alias` and
      `[[path]]` to its basename.
- [ ] Implement: port `markdown()`, `_inline()`, `_cells()`, `_table()`,
      `dewiki()`, and `strip_line_numbers()` from the prototype into
      `markdown.py`, unchanged in behavior
- [ ] Implement: escape HTML before any inline substitution, as the prototype
      does, so tool output cannot inject markup
- [ ] Verify green: run the test command below

**Satisfies:** Section 7 "Markdown renderer notes", Requirement "stdlib-only"

**File(s):** `.claude/skills/audit-log/scripts/auditlog/markdown.py`,
`.claude/skills/audit-log/tests/test_markdown.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
```

**Commit message:** `Port the stdlib markdown renderer and its Obsidian handling`

---

### Step 8: Markdown-preview detection

- [ ] Write the failing test first: `tests/test_preview_detection.py` asserts a
      `Read` of a `.md` path is offered a preview; a `grep` of a `.md` path with
      markdown-shaped output is offered one; and **a `git commit` whose message
      contains the word "head" is NOT**, which is the false positive the
      command-check-alone approach produces. A corpus test asserts the reference
      session offers exactly **8** previews.
- [ ] Implement: `is_markdown_result()` requiring both a reader-command match
      plus a bare `.md` path argument **and** an output shape check (2+ pipe
      rows, or a heading, or 2+ bullets)
- [ ] Verify green: run the test command below

**Satisfies:** Section 7 "Detection heuristics worth copying", acceptance
criterion 4

**File(s):** `.claude/skills/audit-log/scripts/auditlog/markdown.py`,
`.claude/skills/audit-log/tests/test_preview_detection.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
```

**Commit message:** `Detect markdown-bearing tool results with both a command and an output check`

---

### Step 9: HTML renderer with derived stats and derived side effects

- [ ] Write the failing test first: `tests/test_render.py` renders the reference
      session and asserts: the work log ships with the `collapsed` class (hidden
      by default); there are 8 raw/preview toggle pairs; the stat grid shows the
      **derived** commit and external-call counts rather than a literal `1`; the
      side-effects section does **not** contain the string `051a130`; and the
      cost tiles carry the "of the output" reasoning label. Each of these fails
      against the prototype's hardcoded output.
- [ ] Implement: `render.py` producing masthead, provenance strip, 4x2 stat
      grid, collapsed cost breakdown, one color-coded card per participant,
      work log, reply banner, rendered reply, derived side-effects box, footer
- [ ] Implement: participant colors from `agent-color` when present, falling
      back to the violet-caller / green-agent default (F3)
- [ ] Implement: port the CSS and JS verbatim from the prototype, including the
      `prefers-color-scheme` dark handling and the build-time-rendered
      raw/preview panes whose handler only flips visibility
- [ ] Implement: side-effects prose generated from the derived counts, phrased
      honestly when empty ("no commits, 4 file reads, 1 external call")
- [ ] Verify green: run the test command below

**Satisfies:** Defect 3 (the rendering half), Section 7, acceptance criteria 3
and 4

**File(s):** `.claude/skills/audit-log/scripts/auditlog/render.py`,
`.claude/skills/audit-log/tests/test_render.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
```

**Commit message:** `Render the audit log page with derived stats and derived side effects`

---

### Step 10: Self-containment guarantee

- [ ] Write the failing test first: `tests/test_self_contained.py` renders a
      session and asserts the HTML contains no `http://`, no `https://`, no
      `//cdn`, no `<link rel="stylesheet"`, no `<script src=`, and no
      `@import`. Excludes hrefs appearing inside verbatim transcript content,
      which are data rather than page dependencies, by checking only the page
      chrome.
- [ ] Implement: whatever inlining the assertion exposes as missing
- [ ] Implement: an explicit note in `render.py` that no network access may
      enter the render path (A9)
- [ ] Verify green: run the test command below, then confirm by loading a
      rendered page with the network disabled

**Satisfies:** A9, Requirement "zero external requests", acceptance criterion 8

**File(s):** `.claude/skills/audit-log/scripts/auditlog/render.py`,
`.claude/skills/audit-log/tests/test_self_contained.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
```

**Commit message:** `Assert the rendered page is self-contained and makes no external requests`

---

> **PHASE GATE: audit-log renderer.** Run `/phasegate`. The phase promised visual
> parity with `~/donna-greenthumb.html`, a working raw/preview toggle on the 8
> markdown-bearing results, and the elimination of every hardcoded claim. Open
> the rendered page and compare it to the reference before accepting.

---

## Phase 3: Session resolution, CLI, and output placement

### Step 11: Session resolution

- [ ] Write the failing test first: `tests/test_resolve.py` asserts resolution
      by full UUID, by UUID prefix (`9608087e`), by explicit `.jsonl` path, by
      `--project greenthumb` (substring match against the 42 project dirs), by
      `--latest`, and by `--date 2026-08-13`. Asserts an ambiguous prefix and an
      unmatched project each raise a clear error naming the candidates.
- [ ] Implement: `resolve.py` with cwd-to-project-dir mapping (slashes to
      dashes), the six resolution modes, and `--latest` as the default within a
      project
- [ ] Implement: read-only access throughout; never open a transcript for write
- [ ] Verify green: run the test command below

**Satisfies:** Section 10 CLI shape, Requirement "never write to
`~/.claude/projects/`"

**File(s):** `.claude/skills/audit-log/scripts/auditlog/resolve.py`,
`.claude/skills/audit-log/tests/test_resolve.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
```

**Commit message:** `Resolve sessions by uuid, prefix, path, project, date, or latest`

---

### Step 12: CLI, participant resolution, and output naming

- [ ] Write the failing test first: `tests/test_cli.py` asserts the filename for
      brief `9608087e` matches `20260813-0557-donna-to-greenthumb-<slug>.html`;
      that a second run without `--force` exits non-zero and does not overwrite;
      that `--force` does overwrite; that `--stdout` writes HTML to stdout and
      creates no file; and that the output directory is created when absent.
      A slug test asserts the F4 fallback chain: `custom-title`, then
      `ai-title`, then the slash-command invocation, then the date.
- [ ] Implement: `cli.py` with the full argument surface from the handoff's
      Section 10
- [ ] Implement: participant resolution per A5: `--to` from `agent-name` /
      `custom-title` when present, else the project map, else the project
      directory's last segment; `--from` from the project map, else `scott`
- [ ] Implement: `participants.json` holding the project-directory map, seeded
      with the known fleet (`donna-smithers` to `donna`, `greenthumb` to
      `greenthumb`, `lumbergh`, `timercue`, `smykowski`, `argus`)
- [ ] Implement: output written under `~/.ai-staff-audit-log/` (A6), directory
      created if missing, never overwritten without `--force`, and never deleted
      from
- [ ] Implement: refusals surface as a clear message on stderr and a non-zero
      exit, with no file written (A7)
- [ ] Verify green: run the test command below

**Satisfies:** A2, A5, A6, A7, acceptance criteria 6 and 9

**File(s):** `.claude/skills/audit-log/scripts/auditlog/cli.py`,
`.claude/skills/audit-log/scripts/auditlog/participants.json`,
`.claude/skills/audit-log/tests/test_cli.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
```

**Commit message:** `Add the CLI, participant resolution, and output placement`

---

### Step 13: The `bin/audit-log` wrapper

- [ ] Write the failing test first: `tests/test_wrapper.py` asserts
      `bin/audit-log --help` exits 0 and that the wrapper is executable
      (`os.access(path, os.X_OK)`), per the "make executables actually
      executable" rule.
- [ ] Implement: `bin/audit-log`, a short shell script resolving its own
      location (not cwd) and exec'ing the CLI module
- [ ] Implement: `chmod +x`, committed as mode 100755
- [ ] Verify green: run the test command below

**Satisfies:** A1, "Prefer scripts that work relative to script location, not
cwd", acceptance criterion 10

**File(s):** `bin/audit-log`, `.claude/skills/audit-log/tests/test_wrapper.py`

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
git ls-files -s ../../../bin/audit-log   # expect mode 100755
```

**Commit message:** `Add the bin/audit-log wrapper`

---

> **PHASE GATE: audit-log CLI.** Run `/phasegate`. The phase promised session
> resolution, correct output placement with no-overwrite protection, and a
> working command. Verify by generating a real page into
> `~/.ai-staff-audit-log/` and re-running to confirm the refusal.

---

## Phase 4: Skill, corpus sweep, and cleanup

### Step 14: The skill wrapper and its documentation

- [ ] Test-first: n/a (documentation only, no runtime behavior)
- [ ] Implement: `.claude/skills/audit-log/SKILL.md` with frontmatter naming and
      describing the skill, usage covering the common invocations, the output
      location, and an explicit statement of what v1 refuses and why
- [ ] Implement: document the Section 1 caveat, that the skill is not invocable
      as `/audit-log` until this branch merges, and that the script is tested by
      path until then
- [ ] Implement: no emdashes anywhere in the docs, per the global writing rule
- [ ] Verify: re-read the file and confirm every documented flag exists in
      `cli.py`

**Satisfies:** A1, acceptance criterion 10

**File(s):** `.claude/skills/audit-log/SKILL.md`

**Test:**
```bash
grep -c '—' .claude/skills/audit-log/SKILL.md   # expect 0
```

**Commit message:** `Document the audit-log skill`

---

### Step 15: Corpus sweep, acceptance run, and repo cleanup

- [ ] Write the failing test first: `tests/test_corpus_sweep.py` renders **all
      15 renderable sessions** end to end and asserts each produces a
      non-trivial page, and that all 13 unsupported sessions refuse with a
      non-zero status and no file written. This is acceptance criterion 5 as an
      executable test rather than a manual check.
- [ ] Implement: whatever the sweep exposes
- [ ] Implement: generate sample pages for the reference session and three daily
      briefs into `~/.ai-staff-audit-log/` for Scott to review
- [ ] Implement: delete `inter-agent-prompt-audit-log-generator-prototype.py`
      and move `inter-agent-prompt-audit-log-generator-prompt.md` to
      `docs/plans/audit-log-handoff.md` (A8); both remain in history at `3116bde`
- [ ] Implement: update this plan's status and the roadmap item
- [ ] Verify green: run the test command below

**Satisfies:** A8, acceptance criteria 5, 6, and 7

**File(s):** `.claude/skills/audit-log/tests/test_corpus_sweep.py`,
`docs/plans/audit-log-handoff.md`, `docs/plans/development-roadmap.md`,
deletion of the two root files

**Test:**
```bash
cd .claude/skills/audit-log && ./run-tests
ls ~/.ai-staff-audit-log/
git status --short   # expect the two root files gone
```

**Commit message:** `Sweep the full corpus, retire the prototype, and relocate the handoff`

---

> **PHASE GATE: audit-log v1.** Run `/phasegate`. Then push the branch and open a
> **draft** PR. Do not merge, do not re-run `/yolo`, do not remove the worktree.

---

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `.claude/skills/audit-log/scripts/auditlog/__init__.py` | 1 |
| `.claude/skills/audit-log/scripts/auditlog/parse.py` | 1, 3, 4, 5, 6 |
| `.claude/skills/audit-log/scripts/auditlog/cost.py` | 1, 2 |
| `.claude/skills/audit-log/scripts/auditlog/pricing.json` | 2 |
| `.claude/skills/audit-log/scripts/auditlog/markdown.py` | 7, 8 |
| `.claude/skills/audit-log/scripts/auditlog/render.py` | 1, 9, 10 |
| `.claude/skills/audit-log/scripts/auditlog/resolve.py` | 1, 11 |
| `.claude/skills/audit-log/scripts/auditlog/cli.py` | 1, 12 |
| `.claude/skills/audit-log/scripts/auditlog/participants.json` | 12 |
| `.claude/skills/audit-log/run-tests` | 1 |
| `.claude/skills/audit-log/SKILL.md` | 14 |
| `.claude/skills/audit-log/tests/*.py` | 1-13, 15 |
| `bin/audit-log` | 13 |
| `docs/plans/development-roadmap.md` | 15 |
| `docs/plans/audit-log-handoff.md` | 15 |

## Acceptance Criteria

Blocking the PR, from the handoff's Section 11, each mapped to the step that
proves it:

| # | Criterion | Proven by |
|---|---|---|
| 1 | Golden numbers exact | Steps 2, 3 |
| 2 | Daily-brief fixtures match | Steps 2, 6 |
| 3 | All three defects fixed, with tests that fail against the prototype | Steps 4, 5, 9 |
| 4 | Visual parity with the reference page | Steps 8, 9 |
| 5 | Corpus sweep renders every supported session | Step 15 |
| 6 | Honest refusal on multi-turn, images, and scale | Steps 5, 12 |
| 7 | Graceful degradation on unknown types and missing fields | Steps 3, 6 |
| 8 | Self-contained output | Step 10 |
| 9 | Correct output placement and no-overwrite | Step 12 |
| 10 | CLI runs from the worktree against any project dir | Steps 13, 15 |

Explicitly NOT blocking: multi-turn rendering, image rendering, the scale case
and size budget, the index page, the `--annotate` pass, and retention. Criterion
6 covers them for v1 by refusing cleanly. All are recorded in the roadmap under
"Audit log generator follow-ons".
