# Build: Inter-Agent Conversation Audit Log Generator

**This file is a handoff.** It was written at the end of a working session in
`~` (no repo context) on 2026-08-15, where a one-off HTML audit log was built by
hand for a single Donna to Greenthumb exchange. That one-off worked well enough
that it should become a real tool. Everything learned in that session is written
down below so you do not have to rediscover it.

**Read this whole file before doing anything.**

---

## 0. How to run this work

Follow the Servanda suite. In order:

1. **Ask clarifying questions first.** Section 9 lists the open decisions. Batch
   them into one round (use `AskUserQuestion` where it fits), get answers, then
   go. Scott intends to answer the questions and then walk away, so front-load
   everything you need. Do not trickle questions out over hours.
2. **`/roadmap`** to add this as an item. See Section 8 for where it fits.
3. **`/gameplan`** to produce the implementation plan. Plans live in
   `docs/plans/`. TDD-shaped, citation-tagged, per the command's contract.
4. **Create the worktree** (Section 1) and move into it.
5. **`/yolo`** to implement the plan autonomously on the feature branch.
6. **`/phasegate`** after each phase completes, per the plan's phase structure.
7. **Open a draft PR** and **stop**.

### Hard stops

These are the whole point of the exercise. Scott is going to be away while this
runs, and wants to come back to something he can review and test, not something
already landed.

- **Do NOT merge the branch.** Not into `master`, not anywhere.
- **Do NOT re-run `/yolo` after the build completes.** Re-running `/yolo` is
  what triggers its merge-and-wrap-up half. Run it once, to build. That is all.
- **Do NOT remove the worktree.** Leave it in place for Scott to test in.
- **Do NOT close or merge the PR.** Open it as a draft and leave it.
- **Do NOT touch the uncommitted work in the main checkout.** As of this
  writing `master` has modified `.claude/.gitignore`, `.claude/settings.json`,
  `.gitconfig`, `.zsh/aliases`, `.zsh/environment`, and an untracked
  `bin/wipe-docker-vm-file-cache.sh`. That is unrelated held work. Do not
  commit it, stash it, or otherwise disturb it. Working in a separate worktree
  keeps you clear of it automatically; just do not go back to the main checkout
  and start tidying.
- **Run this from a plain `claude` session.** Not `claude-glm`, `claude-gpt`, or
  anything else via `bin/claude-run`. Phase gates and security passes HALT under
  a routed session by design.

### Autonomy granted

The global `CLAUDE.md` rule is "never commit without explicit approval." **This
file is that approval, scoped:** commit freely and often on the feature branch.
Push the feature branch to `origin`. Never push to `master`, never merge.

---

## 1. Worktree and branch setup

The repo is `~/src/scottwb/dotfiles`, remote `git@github.com:scottwb/dotfiles.git`.
**The default branch is `master`, not `main`.**

There is an existing convention for worktrees here: sibling directories named
`dotfiles-<slug>`. `git worktree list` currently shows
`/Users/scottwb/src/scottwb/dotfiles-end-session` for `feature/end-session`.
Follow that shape:

```sh
cd ~/src/scottwb/dotfiles
git worktree add ../dotfiles-audit-log -b feature/audit-log master
cd ../dotfiles-audit-log
```

Branch from `master` HEAD, which cleanly excludes the held uncommitted work.

### A gotcha that will bite you if you miss it

`~/.claude` is a **symlink** to `~/src/scottwb/dotfiles/.claude`. It points at
the **main checkout**, not at your worktree.

Two consequences:

1. **Transcripts are not in your worktree.** `.claude/projects/` is gitignored
   (`.claude/.gitignore:3`), so it exists only in the main checkout. Always read
   transcripts from the absolute path `~/.claude/projects/`. Never from
   `<worktree>/.claude/projects/`, which will be empty.
2. **Your skill will not be live until the branch merges.** A skill you add at
   `<worktree>/.claude/skills/audit-log/` is not visible to `~/.claude/skills/`.
   So `/audit-log` will not be an invocable slash command during development.
   **This is good.** It means nothing you build can affect Scott's live sessions
   before he reviews it. Do acceptance testing by invoking the script directly
   from the worktree path. Do not try to work around this by symlinking or
   copying into the main checkout.

### Confirmed: no collision with other work in flight

Checked 2026-08-15. You are clear to work in isolation:

- **`feature/end-session`** (the other worktree, at `../dotfiles-end-session`)
  touches only `.claude/CLAUDE.md`, `.claude/COMMANDS.md`,
  `.claude/commands/end-session.md`, and `.claude/docs/servanda.md`. Nothing in
  `.claude/skills/`, nothing in `bin/`, no Python.
- **The held changes on `master`** are `.claude/.gitignore`,
  `.claude/settings.json`, `.gitconfig`, `.zsh/aliases`, `.zsh/environment`,
  plus untracked `bin/wipe-docker-vm-file-cache.sh`. No overlap either.
- **Transcripts are branch-independent.** They are read by absolute path through
  the `~/.claude` symlink and are gitignored, so no branch or worktree state
  affects the tool's input.

**Two files to coordinate on if you touch them**, since others already have
changes staged against them: `.claude/settings.json` (a held one-line change on
`master`) and `.claude/COMMANDS.md` (`feature/end-session` adds to it). A new
skill should need neither. If you conclude you do need one, say so in the PR
body rather than quietly editing it.

---

## 2. What the tool needs to do

**Goal:** from any Claude Code session (most likely Donna, or a no-repo-context
session, or one of the staff repos), run a skill and get a self-contained HTML
audit log page for a given session transcript, written to a well-organized
folder outside any repo.

**Output location: `~/.ai-staff-audit-log/`.** Decided, not open for debate:

- Create it if missing.
- **Never source controlled.** Not a git repo, no `git init`, no remote.
- **Never inside the dotfiles repo.** Plain `~`, outside any working tree.
- No `.gitignore` needed, because it is not inside a repo in the first place.
- Nothing in the dotfiles repo should reference its *contents*, only its path.

### v1 scope: the near-term goal is a small one

The actual near-term need is modest: render a handful of Donna-to-agent
conversations well enough to share. The reusable skill is the durable half, but
it must not be blocked on the hard cases, none of which the target corpus has.

**In scope for v1 (blocking the PR):**

- Single-turn SDK sessions, which is what every Donna-to-agent brief is.
- The 13-brief corpus in Section 5 rendering correctly, with correct
  attribution, titles, and cost figures.
- The three prototype defects in Section 5.1, fixed properly.
- Output naming and writing into `~/.ai-staff-audit-log/`.
- Session resolution and the CLI.
- The skill wrapper and its docs.

**Explicitly deferred (must NOT block the PR):**

- Multi-turn rendering (sessions with many user turns).
- Image blocks.
- The 46 MB scale case and the output size budget.
- Index page, annotation pass, retention policy.

Deferred does not mean ignored. The parser should **detect** these cases and
fail loudly with a clear message ("this session has 44 user turns; multi-turn
rendering is not implemented yet") rather than silently emitting a wrong or
truncated page. A clean, honest refusal is a v1 requirement. Building the
feature is not.

**Filename shape** must sort chronologically by default and allow easy skimming
by initiating agent. Recommended:

```
YYYYMMDD-HHMM-<from>-to-<to>-<slug>.html
20260815-1546-donna-to-greenthumb-spurge-offensive-vs-lawn-pass-4.html
```

Plain `ls` gives chronological order; `ls *-donna-to-*` filters by initiator.
Confirm the exact shape in Section 9 before building it, but the directory
itself is settled.

---

## 3. Reference material that already exists

| Thing | Where | What it is |
|---|---|---|
| **Worked example output** | `~/donna-greenthumb.html` | The rendered target. Open it in a browser first. This is the visual and functional bar to hit. Do not delete it. |
| **Prototype generator** | `~/src/scottwb/dotfiles/inter-agent-prompt-audit-log-generator-prototype.py` | The actual script that produced that HTML. ~850 lines, stdlib only. Working code, hardcoded to one session. |
| **Reference transcript** | `~/.claude/projects/-Users-scottwb-src-scottwb-greenthumb/0a5df9e2-3dc1-4bee-9013-e38e709b4cb1.jsonl` | The session the example was built from. 65 records, 428 KB. |
| **Corpus** | `~/.claude/projects/-Users-scottwb-src-scottwb-greenthumb/` | 28 transcripts, 3 KB to 46 MB. See Section 5. |

The prototype is a **reference implementation to port and generalize**, not
code to ship as-is. It is monolithic, its participant names are hardcoded, and
its "side effects" prose is hand-written for that one session. Its parsing,
cost math, markdown renderer, and CSS are all worth keeping.

Both `inter-agent-prompt-audit-log-generator-prompt.md` (this file) and the
prototype `.py` sit untracked at the repo root. **Relocate or delete both as
part of this work** so the repo root does not stay cluttered. The plan should
say which.

---

## 4. Transcript format: everything learned the hard way

Transcripts are JSONL at
`~/.claude/projects/<cwd-path-with-slashes-as-dashes>/<session-uuid>.jsonl`.
Example: cwd `/Users/scottwb/src/scottwb/greenthumb` maps to directory
`-Users-scottwb-src-scottwb-greenthumb`. There are 42 such project dirs.

### 4.1 THE critical bug, which cost real time to find

**Claude Code writes one record per content block, and every record repeats the
entire message's `usage` object.**

An assistant message with a thinking block, a text block, and two tool_use
blocks becomes **four records**, each carrying the same `output_tokens`,
`input_tokens`, `cache_read_input_tokens`, and so on.

Summing usage per record inflates every token count. In the reference session
this produced 41,302 output tokens where the truth was 16,179, a 2.5x overcount.
The first published version of the example HTML had this bug.

**Always deduplicate on `message.id` before summing usage.** The reference
session is 26 assistant records but only **8 API calls**.

Make this a regression test. See Section 6.

### 4.2 Record types

Seen across the 28 files in the greenthumb project alone:

`ai-title`, `agent-color`, `agent-name`, `assistant`, `attachment`,
`bridge-session`, `custom-title`, `file-history-delta`,
`file-history-snapshot`, `last-prompt`, `mode`, `permission-mode`,
`queue-operation`, `system`, `user`

Assume this list is incomplete across the other 41 project dirs. **Unknown
record types must be skipped gracefully, never crash.**

Useful ones:

- **`agent-name`** / **`agent-color`** / **`custom-title`**: carry the agent's
  identity outright, e.g. `{"type":"agent-name","agentName":"Greenthumb"}` with
  `agentColor: "green"`. Present in 4 of 28 files. **Use these when present**;
  they solve half the attribution problem for free.
- **`ai-title`**: a generated title, e.g. "Commit pending files and prioritize
  Saturday afternoon tasks". Ideal source for the filename slug and the page
  subtitle. Present in most files.
- **`last-prompt`**, `mode`, `permission-mode`, `queue-operation`,
  `bridge-session`, `file-history-*`: metadata, mostly skippable for v1.
  `file-history-*` could later power a "what changed on disk" view.

### 4.3 Message record shape

`user` and `assistant` records carry `message` plus this metadata, which is
where the provenance strip in the example comes from:

`cwd`, `gitBranch`, `version` (CLI version), `sessionId`, `uuid`, `parentUuid`,
`timestamp` (UTC ISO 8601), `promptSource`, `entrypoint`, `permissionMode`,
`userType`, `isSidechain`, `effort` (on assistant records)

**`message.content` is either a bare string or a list of blocks.** Handle both.
Bare strings are common (91 occurrences in one large file).

Block types observed: `text`, `thinking`, `tool_use`, `tool_result`, `image`.

### 4.4 Thinking blocks are empty

Thinking blocks arrive as `{"type":"thinking","thinking":"","signature":"<long
base64>"}`. **The reasoning text is never stored.** Only the encrypted
signature survives on disk.

The token count IS available, via `usage.output_tokens_details.thinking_tokens`.
The example page renders a collapsed "Reasoned privately" row showing the token
count and a truncated signature, with a note explaining why there is no text.
Do not imply the content is recoverable.

### 4.5 Usage fields

```
input_tokens
cache_creation_input_tokens
cache_read_input_tokens
cache_creation.ephemeral_1h_input_tokens
cache_creation.ephemeral_5m_input_tokens
output_tokens
output_tokens_details.thinking_tokens
```

**The 1h vs 5m split matters** because they bill at different multiples. The
reference session used the 1-hour TTL exclusively.

### 4.6 Tool result quirks

- `tool_result.content` is a string, or a list of `{"type":"text"}` blocks.
- **`Read` output has `   12\t` line-number prefixes** (spaces, number, tab).
- **`grep -n` output has `12:` prefixes** (number, colon).
- Both must be stripped to recover raw file content for the markdown preview.

### 4.7 Slash-command prompts

A prompt invoked as a slash command arrives as XML in the user content:

```
<command-message>exec-brief</command-message>
<command-name>/exec-brief</command-name>
<command-args>full</command-args>
```

Unwrap this to something readable like `/exec-brief full` rather than dumping
the tags.

### 4.8 Attachment records

`attachment` records carry `deferred_tools_delta`, `agent_listing_delta`,
`skill_listing`, `read_truncation_notice`. These are harness plumbing. The
example page skips them entirely, which was the right call. `read_truncation_notice`
may be worth surfacing later since it explains a partial file read.

---

## 5. Corpus survey: what actually varies

Run against all 28 files in the greenthumb project. Findings that shape the design:

**There is a ready-made corpus of exactly the target use case.** Thirteen of the
28 are the same shape: ~0.4 MB, 31 to 40 records, identical record type sets,
zero sidechains, `entrypoint: sdk-cli`, all firing at 12:57 UTC (5:57am Pacific)
daily, all opening with `/exec-brief full`. These are Donna's daily briefs to
Greenthumb, Aug 5 through Aug 15. **The prototype renders them today with no
changes.** Use them as the primary test corpus.

**Zero sidechains across all 28 files.** `isSidechain` is never true here. So
subagent thread rendering is NOT needed for v1. Do not build it. Do make the
parser record whether any sidechain records were seen, so it can warn rather
than silently mis-render if one shows up.

**What breaks on the larger sessions:**

| Issue | Reality | Implication |
|---|---|---|
| **Multi-turn** | Up to 70 user turns (`ac5e6a1e`, 46 MB); several in the 11 to 44 range | The prototype's "one prompt, one reply" framing collapses. Needs repeating turn groups: user turn, work log, assistant reply. **This is the single biggest structural change.** |
| **Images** | `image` blocks in 3 files (3, 6, and 21 of them) | Base64 inline will balloon the page. Needs thumbnailing, a size cap, or a placeholder chip. |
| **Size** | Largest is 46 MB of JSONL | Embedding every tool result verbatim yields an unopenable page. Needs a per-result truncation threshold and an overall budget. The prototype currently sets its cap to effectively unlimited, which is fine at 0.4 MB and catastrophic at 46 MB. |
| **String content** | 91 bare-string contents in one file | Handle both shapes everywhere. |

---

## 5.1 Verified defects in the prototype

These were found by actually running the prototype against three of the daily
briefs on 2026-08-15, not by reading the code. **Fix all three properly in the
real implementation.** Do not patch the prototype; it is reference material.

### Defect 1: prompt detection is too narrow (crashes)

The prototype locates the opening prompt with:

```python
if t == "user" and r.get("promptSource") == "sdk":
```

The daily briefs have **`promptSource: None`**, so `first_ts` is never set and
the run dies at `duration = last_ts - first_ts` with:

```
TypeError: unsupported operand type(s) for -: 'datetime.datetime' and 'NoneType'
```

All 13 briefs crash this way. Widening the condition to "the first `user`
record whose content is a bare string" made all three test sessions render.
That widening is a demonstration, not the right fix. **The real fix** is a
proper opening-prompt resolver: the first `user` record that is a genuine
human or caller turn, meaning it has no `tool_result` blocks and, ideally,
`parentUuid: null`. Cover both `promptSource` present and absent. Add a
regression test per shape.

### Defect 2: slash-command prompts render as raw XML

The briefs open as `/exec-brief full`, but the page shows the literal markup:

```
<command-message>exec-brief</command-message><command-name>/exec-brief</command-name>...
```

Unwrap it to a readable invocation. Render `/exec-brief full` as the prompt,
and keep the raw form available behind the same raw/preview affordance used
elsewhere if it seems worth it. See Section 4.7.

### Defect 3: hardcoded content leaks across sessions

Several things in the prototype are hardcoded to the one session it was written
for and render as **confidently wrong** on any other transcript:

| Hardcoded | Must become |
|---|---|
| The entire "Side effects on the real world" prose, which still cites commit `051a130` | Derived from the transcript: enumerate commits, file writes, and external calls actually observed |
| The `1 git commit` stat tile | Counted from the session's tool calls |
| The `1 external API call` stat tile | Counted from MCP and server-tool calls |
| Participant names `Donna` and `Greenthumb` | From `agent-name` / `custom-title` when present, else CLI flags, else a config map |
| `SRC` and `OUT` module constants | CLI arguments |

Wrong-but-plausible output is worse than no output. A derived side-effects
section that says "no commits, 4 file reads, 1 external call" is correct and
useful; the current one silently claims a commit that never happened.

### These were verified working after the Defect 1 widening

All three rendered with correct titles, dates, participants, durations, and
costs. Use them as fixtures.

---

## 6. Cost model

Pricing must live in a **maintained JSON rate table**, not in code, because it
goes stale. Keyed by model ID.

Claude Opus 5 (`claude-opus-5`), verified 2026-08-15 against the `claude-api`
skill, dollars per million tokens:

| Component | Rate | Basis |
|---|---|---|
| Input | $5.00 | base |
| Output | $25.00 | base |
| Cache write, 5-minute TTL | $6.25 | 1.25x base input |
| Cache write, 1-hour TTL | $10.00 | 2x base input |
| Cache read | $0.50 | 0.1x base input |

**Reasoning tokens are a subset of output tokens.** Never add them to the total.
The example page shows the reasoning cost with the label "of the output" and
says so explicitly in the breakdown, because otherwise the tiles look like they
should sum to more than the total.

**Say plainly that nothing was billed.** These sessions run on a Claude
subscription. The figure is what identical traffic would cost through the public
API at list rates. The example page states this in the cost note. Keep that.

### Golden regression test

The reference session
(`0a5df9e2-3dc1-4bee-9013-e38e709b4cb1.jsonl`) must produce **exactly** these
numbers. Any deviation means the dedupe broke.

```
api_messages       8
input              3,543
cache_write_1h    89,150
cache_write_5m         0
cache_read       529,482
output            16,179
reasoning          9,316   (subset of output)

input side total   $1.1740
output             $0.4045
reasoning          $0.2329  (inside output, not additive)
TOTAL              $1.5784
```

Write this test first, per the TDD rule in `CLAUDE.md`. It must fail against a
naive per-record summation and pass against the deduped one.

### Additional fixtures: three daily briefs

Verified 2026-08-15 with the Defect 1 widening applied. These lock in the
corpus path, and their much larger cache-write share is a useful contrast with
the reference session.

| Session | Date | Duration | Cache write 1h | Cache read | Output | Reasoning | Total |
|---|---|---:|---:|---:|---:|---:|---:|
| `9608087e` | Aug 13 | 1m 56s | 115,009 | 166,240 | 8,733 | 4,285 | $1.4516 |
| `bd35db69` | Aug 14 | 2m 08s | 112,076 | 166,053 | 9,519 | 4,712 | $1.4418 |
| `d3a49460` | Aug 15 | 2m 00s | 111,755 | 160,873 | 8,713 | 4,750 | $1.4158 |

Reply lengths were 1,356 / 1,523 / 1,056 words respectively, which is a cheap
smoke assertion that the reply extractor found the right block.

Note `input_tokens` is 5 or 6 on these, versus 3,543 on the reference session.
Nearly everything is cache traffic. Do not write a test that assumes fresh
input is a meaningful share of the total.

---

## 7. Rendering: what the example does, and what to keep

Open `~/donna-greenthumb.html` before designing anything. Feature list:

**Structure**
- Masthead: "Conversation Audit Log", "Donna -> Greenthumb", full date and time
  in Pacific.
- Provenance strip: channel, repo and branch, session UUID, model and effort and
  CLI version, permission mode.
- Stat grid, 4 by 2: wall clock, tool calls, input tokens, output tokens,
  reasoning tokens, total cost, git commits, external API calls. Token and cost
  tiles carry a small italic amber cost subline.
- Collapsed cost breakdown strip under the grid.
- One card per participant, color-coded (violet for the caller, green for the
  agent). Use `agent-color` from the transcript when present.
- Work log between the prompt and the reply.
- "Reply returned to Donna on stdout" banner, then the full reply as rendered
  markdown.
- "Side effects on the real world" box.
- Footer stating the log is verbatim and explaining the thinking-block situation.

**Interaction**
- **Work log hidden by default.** Page opens showing just the dialog. One
  "Show work" button toggles it.
- Expand all / Collapse all buttons appear **only** in show-work mode.
- Every tool call and reasoning step is an individually collapsible row.
- Tool rows are labeled in plain English ("Wrote a git commit", "Fetched the
  7-day forecast for the property", "Read work-plan.md, lines 146 to 290") with
  the verbatim command and full output underneath.
- **Raw / Preview toggle on markdown tool results.** Both panes are rendered at
  build time and shipped as sibling divs; the click handler only flips
  visibility. **No markdown parser ships with the page.** Preview mode strips
  line-number prefixes, renders tables as real tables, and resolves Obsidian
  wikilinks (`[[path\|alias]]` becomes the alias). This is the feature that
  makes tracker-file reads legible; keep it.

**Constraints**
- Single self-contained HTML file. No external requests, no CDN, no fonts.
- Light and dark theme aware via `prefers-color-scheme`.
- Responsive; wide tables scroll inside their own container.
- Verbatim: tool commands and outputs are never paraphrased. Only the labels are
  human-written.

**Markdown renderer notes:** the prototype has a ~120 line stdlib markdown
renderer handling headings, fenced code, tables (including headerless pipe-row
runs from grep fragments, and `\|` escapes inside cells), lists, blockquotes,
strikethrough, and inline code and bold and italic. It works. Porting it is
cheaper than adding a dependency, and it keeps the tool stdlib-only.

**Detection heuristics worth copying:** deciding whether a tool result gets a
markdown preview needs both a command check (a reader command like grep, sed,
cat, head, tail, plus a bare `.md` path argument) **and** an output check (the
output actually looks like markdown: 2+ pipe rows, or a heading, or 2+ bullets).
The command check alone false-positives, because a `git commit` message
containing the phrase "that head needs inspection" matches `\bhead\b`.

---

## 8. Roadmap placement

The roadmap is `docs/plans/development-roadmap.md`. It organizes by **thread**,
and the current threads are Servanda, Shell, Tools, Terminal and editors, and
Machine setup.

This work does not fit cleanly into any of them. It is a Claude Code skill plus
a Python CLI, about inter-agent observability. Candidates:

- **Tools**, since `bin/` is "~90 scripts" and this is another one.
- **Servanda**, since `.claude/` is Servanda's scope and a skill lives there.
- **A new thread**, something like "AI Staff" or "Observability", since Scott has
  a fleet of named agents (Donna, Greenthumb, Lumbergh, TimerCue, Smykowski,
  Argus) and this is the first tool *about* that fleet rather than part of it.

Recommendation: a new thread. See the question in Section 9. Note the layout
convention stated at the top of the roadmap: runtime files that a tool loads go
in their dotfile locations (`.claude/`, `bin/`); dev artifacts about the work
(roadmap, plans, gate reports) go in `docs/`, which is never symlinked into
`$HOME`.

Also relevant, from Scott's memory notes: **a Servanda rename is agreed but not
executed** (to `implement-*` / `plan-feature`). That is a separate pending item.
**Do not do it as part of this work.**

---

## 9. Clarifying questions to ask before building

Ask these up front, together, in one round. Recommendations included so Scott
can accept the defaults quickly and then leave.

**Already decided, do not re-ask:**

- Output goes to `~/.ai-staff-audit-log/`, never source controlled, never inside
  the dotfiles repo. (Section 2)
- v1 scope is the single-turn brief corpus. Multi-turn, images, 46 MB scale,
  index page, annotation pass, and retention are all deferred and must not
  block the PR. (Section 2)
- Do not merge, do not re-run `/yolo`, do not remove the worktree. (Section 0)

**Still open:**

1. **Where does the implementation live?** Recommend: skill-owned at
   `.claude/skills/audit-log/` with the Python under `scripts/`, plus a thin
   `bin/audit-log` wrapper for direct CLI use. Alternative: implementation in
   `bin/` with the skill as a shell-out.
2. **Confirm the filename scheme.**
   `YYYYMMDD-HHMM-<from>-to-<to>-<slug>.html`, flat directory. Alternative:
   per-agent subdirectories, which groups better but breaks cross-agent
   chronological skimming.
3. **Which roadmap thread?** Recommend a new "AI Staff" thread, since this is
   the first tool *about* the agent fleet rather than part of it.
4. **How is `--from` resolved** when the transcript does not name the caller?
   `agent-name` gives the callee, but nothing records the initiator. Recommend:
   a small config map from project directory to agent name, with a `--from`
   flag override, defaulting to `scott` for interactive sessions.
5. **Anything else you need** to work unattended. Ask now, not in an hour.

---

## 10. Design guidance

### Deterministic core, optional model-assisted enrichment

The overwhelming majority of this is a deterministic script. Parsing, dedupe,
cost math, markdown rendering, layout, and the raw/preview toggle involve no
judgment at all.

Three things genuinely benefit from a model, and **all three are optional
enrichment, not load-bearing**:

1. Human-readable one-liners for arbitrary tool calls. A regex table covers
   maybe 80% and falls back to "Ran a shell command", which is acceptable.
2. The "Side effects on the real world" prose. A script can enumerate this
   mechanically as a table (N commits, N file writes, N external calls).
3. Participant names when `agent-name` is absent.

**If this is built, quarantine it.** An `--annotate` pass should write a sidecar
`<session-id>.annotations.json` next to the output. Then rebuilds are instant,
free, and byte-reproducible, and the page renders completely without it. Do not
put a model call in the render path.

### Suggested module split

- `parse.py`: JSONL to a normalized session model. All the Section 4 knowledge
  lives here. Pure, testable, no HTML.
- `render.py`: session model to HTML. All the Section 7 work.
- `resolve.py`: session selection. Project name to project dir, plus latest, by
  date, by UUID prefix.
- `pricing.json`: the rate table.
- `cli.py`: argument handling, output naming, writing to `~/.ai-staff-audit-log/`.
- `annotate.py`: optional, deferred.

### CLI shape

```
audit-log [SESSION]            # UUID, UUID prefix, or path to a .jsonl
          [--project NAME]     # resolves ~/.claude/projects/*NAME*
          [--latest]           # most recent session in the project (default)
          [--date YYYY-MM-DD]
          [--from NAME] [--to NAME]
          [-o PATH]            # override output path
          [--stdout]           # write HTML to stdout instead
          [--force]            # allow overwrite
```

Bare invocation inside a repo should default to the latest session for that cwd.
Invoked from Donna or a no-context session, `--project` is the usual entry point.

### Safety requirements, non-negotiable

- **Read-only against `~/.claude/projects/`.** Never write, move, or delete a
  transcript. These are the only copy and they are gitignored.
- **Never overwrite an existing output** without `--force`.
- **No network access** in the render path.
- Create `~/.ai-staff-audit-log/` if missing; never delete from it.
- Fail loudly on an unparseable transcript. Do not emit a half-page that looks
  complete.

---

## 11. Acceptance criteria

The plan should turn these into explicit, testable steps.

### Blocking the PR

1. **Golden numbers.** The reference session produces exactly the Section 6
   figures. Test written first, failing against per-record summation.
2. **Daily-brief fixtures.** The three sessions in Section 6 produce their
   stated durations, token splits, totals, and reply word counts.
3. **Defects fixed.** All three Section 5.1 defects, each with a regression test
   that fails against the prototype's behavior.
4. **Visual parity.** The reference session renders to something equivalent to
   `~/donna-greenthumb.html`: work log hidden by default, raw/preview toggle
   working on the 8 markdown-bearing tool results, cost tiles populated.
5. **Corpus sweep.** All 13 daily briefs render without error, and spot-checking
   3 shows correct attribution, titles, and costs.
6. **Honest refusal.** A multi-turn session, an image-bearing session, and the
   46 MB session each exit with a clear unsupported-case message and a non-zero
   status. **No half-rendered page, no silent truncation.** This is the v1
   substitute for actually supporting them.
7. **Graceful degradation.** Unknown record types, missing `agent-name`, and
   bare string content all render without crashing.
8. **Self-contained.** The output makes zero external requests. Verify by
   loading with the network disabled.
9. **Correct output placement.** Files land in `~/.ai-staff-audit-log/` with the
   agreed naming, no overwrite without `--force`, and the directory is created
   if absent.
10. **Invocation.** The CLI runs from the worktree against any project dir.
    Note the Section 1 caveat: the skill cannot be tested as `/audit-log` until
    the branch merges, so test the script directly.

### Explicitly NOT blocking

Multi-turn rendering, image rendering, the 46 MB scale case and size budget, the
index page, the annotation pass, and retention. Criterion 6 covers them for v1
by refusing cleanly. Record them in the roadmap as follow-on work.

### Suggested phases

1. Parser, normalized session model, golden test, and the three defect
   regression tests.
2. Renderer port, plus derived side-effects and derived stat tiles.
3. CLI, session resolution, output naming and placement.
4. Skill wrapper and docs.

Run `/phasegate` after each.

---

## 12. Final deliverable

When the build and gates are done:

1. Push `feature/audit-log` to `origin`.
2. Open a **draft** PR against `master` with `gh pr create --draft`. Body should
   summarize what was built, what was tested, and exactly how Scott can test it
   himself from the worktree.
3. **Stop.** Report back with: the worktree path, the branch name, the PR URL,
   the paths of any generated sample HTML files for review, and the one command
   he needs to run to try it.

Leave the worktree, the branch, and the PR all in place.
