# Development Roadmap: scottwb/dotfiles

Repo-wide roadmap for `~/src/scottwb/dotfiles`. Work here spans several
independent threads, so every item names its thread. Run workflow commands from
the repo root; plans live beside this file in `docs/plans/`.

Layout convention: runtime files that a tool loads live in their dotfile
locations (`.claude/`, `.zsh/`, `bin/`); dev artifacts about the work (this
roadmap, plans, acceptance checklists, `docs/assessments/` gate reports) live in
`docs/`, which is deliberately never symlinked into `$HOME`.

## Threads

| Thread | Scope |
|---|---|
| **Servanda** | The workflow command kit: `.claude/commands/`, `.claude/COMMANDS.md`, `.claude/CLAUDE.md`, `.claude/settings.json` |
| **Shell** | `.zshrc`, `.zsh/` (aliases, prompts, OS dispatch, env) |
| **Tools** | `bin/` (~90 scripts) |
| **Terminal & editors** | `.tmux.conf`, `.tmux/`, `.vimrc`, `.vim/`, `.emacs.d/`, `themes/` |
| **Machine setup** | `.gitconfig`, install story in `README.md`, `linux/`, ignore hygiene |
| **AI Staff** | Tooling *about* the agent fleet: observability, audit, and provenance for Donna, Greenthumb, Lumbergh, TimerCue, Smykowski, Argus |

**AI Staff** is new as of 2026-08-15. The other threads are all about Scott's own working environment; this one is about the fleet of named agents that now runs inside it. The distinction that earned it a thread: Servanda is the kit the agents are *governed by*, and `bin/` is full of tools the agents *use*, but nothing until now was a tool for looking *at* what the agents did. Its first item is the conversation audit log below. Runtime lives in the usual dotfile locations (`.claude/skills/`, `bin/`); generated output deliberately does not live in this repo at all.

**Servanda** is Scott's workflow command kit for Claude Code (from "pacta sunt servanda": agreements must be kept; the kit is the enforcement half). Code lives in this repo at `.claude/` (commands in `.claude/commands/`, contracts in `.claude/COMMANDS.md`), symlinked from `~/.claude`. Plans live here in `docs/plans/`. The kit is internal (not shared, not a product); it may get its own repo someday. It is the dominant thread at the moment, so most items below are tagged Servanda; that is a snapshot of current attention, not the repo's permanent shape.

---

## Next Immediate Step

### `/shift-change`: write it down, clock out, next session comes in

**Thread:** Tools (Patchbay), plus one command file in Servanda's `.claude/commands/`

**Goal:** One command that does what Scott does by hand before exiting a session, then restarts it clean. It runs [`/end-session`](#end-session-write-it-down-then-exit-2026-10-31) (so everything perishable outside the repo is recorded and committed, then Claude exits) with a restart signal instead of a stop signal, and the launcher traps that exit and starts a **new** session (no `--resume`, no `-c`) under the same agent name, route, model, flags and Remote Control. Two payoffs:

- **Restart to update.** A relaunch runs whatever `claude` is on disk now, so the session picks up a Claude Code update. Seen 2026-10-18: the CLI was at 2.1.302 while a long-running Donna session was still on 2.1.296.
- **Clear context without losing the session's identity.** Plain `/clear` handles the context half, but it messes up the agent name and the Remote Control sessions (Scott, 2026-10-19), which is the whole reason this is not just `/write-that-down` plus `/clear`. A fresh `CLAUDE.md` comes along for free; it is a side effect, not the goal.

**Named for the staffing model** (Scott, 2026-10-19): the outgoing session writes everything down for the next one and clocks out, and the next one comes in fresh at the same post. Working name before that was `/reload`, which wrongly implied the same session coming back.

**Not wanted: resuming the previous conversation.** The repo is the memory. Anything worth carrying over is written down before the restart, and the new session starts empty. (Corrected 2026-10-19. The first version of this item resumed by session id and called `CLAUDE.md` reloading the point; both were wrong.)

**References:**
- [Building a reload command for Claude Code](https://www.panozzaj.com/blog/2026/02/07/building-a-reload-command-for-claude-code/) (panozzaj, 2026-02-07). The mechanism to start from: the command body is `` !`kill -HUP $PPID` `` (the `!` makes it deterministic; asking the model to run it was not), Claude exits 129, and a wrapper loop relaunches on 129 and passes any other exit code through. The post relaunches with `-c`; this item deliberately does not.
- [adrrr/persistent-handoff](https://github.com/adrrr/persistent-handoff). The other carry-over model: a `SessionStart` hook reads back a per-project "where I am / next action" file the agent rewrites at milestones. Not adopted, because the rule here is that the repo carries what matters. Revisit only if fresh sessions keep having to re-ask what was in flight.

**Why it lives in `pbay` (decided 2026-10-18, narrowed 2026-10-19).** The relaunch has to reproduce the original launch, and only the launcher knows what that was. A routed session relaunched as plain `claude` comes back on Anthropic under a different model with no warning. An agent relaunched without its `--name` and `--remote-control` comes back as a different agent, which is the exact `/clear` problem this exists to avoid. Once `pbay` is the one front door, the relaunch loop lives in `claude-run` behind it, the one place that knows both the route and Claude's exit behaviour. Plain bare `claude` stays untouched, per Patchbay's standing rule.

**Built in Patchbay's `agent` first, as an interim (Scott, 2026-11-03).** Scott wants to save, exit and restart often, so the loop goes into `agent` now and moves into `claude-run` at the [`pbay` merge](https://github.com/facetdigital/patchbay/blob/main/docs/plans/development-roadmap.md#pbay-one-launcher-merge-agent-and-claude-run). Not permanent: `agent` is headed for being only an alias. Until the merge, routed `claude-run` sessions have no loop, and `/shift-change` refuses in them like any unwrapped session.

**Design points for the plan:**
- **Strip resume flags on relaunch.** If the original launch had `--resume <x>`, `-r`, `-c` or `--continue`, replaying the same arguments would resume. The loop replays everything except those. `claude-run`'s own usage example launches with `--resume`, so this is not hypothetical.
- **Two signals, two exit codes.** `/end-session` sends SIGTERM (exit 143) and the loop stops; `/shift-change` sends SIGHUP (exit 129) and the loop relaunches. Any other exit code passes through. **Fallback** if Claude Code turns out to exit with the same code for both: `/shift-change` writes a mode file keyed to the launcher's PID before signalling, and the loop reads it.
- **Never restart over an unrecorded session.** Inherited from `/end-session`: `/write-that-down` has to finish, or report nothing to record, before the signal. If it fails or stops to ask a question, `/shift-change` stops there and the session stays up. This pulls against the post's lesson that model-driven steps are unreliable, so split it: the model does the write-down, and the signal itself is the fixed `bin/claude-end-session` helper from `/end-session`, extended to send SIGHUP. Not the post's `!` line: `!` lines run when the command expands, before the write-down.
- **Refuse in an unwrapped session.** In plain `claude` there is no loop to bring the session back. The launcher with the loop (`agent` now, `pbay` after the merge) exports a marker, and `/shift-change` checks for it before doing anything, write-down included, and declines with an explanation when it is absent, pointing at `/end-session`.
- **Trigger phrases** ("new context and restart", "get the harness update", "shift change") are in the `/end-session` item's table, with the same rule: explicit runs, implied asks first in one line.

**Verify first; the post is eight months and many CLI versions old** (now on 2.1.302):
- SIGHUP still produces exit 129, distinct from SIGTERM's 143. The SIGTERM half is done: 143, clean transcript and Remote Control close, and `$PPID` is the Claude process (verified 2026-10-25 on 2.1.310 for `/end-session`). SIGHUP is still to check.
- **Remote Control across a relaunch.** Does the new process come back as the same Remote Control session, still reachable from the phone, or as a new one that leaves a dead entry behind? This is the half of the `/clear` problem most likely to need real work.
- **Agent name and peer messaging.** The same `--name` should give the same name, but the PID and messaging socket change. Check that peers reach the new session by name, and that Claude Code's dedupe of same-named live sessions does not rename it to a variant because the old process has not fully exited.
- `claude respawn` (new since the post) restarts *background* sessions onto the current binary, which is the update half for those. It does not cover interactive tmux sessions, and it has no write-down step.

**Possible follow-on, not in scope:** a shift change for the whole fleet onto a new version. Sending `kill -HUP` to every PID `claude-ps` lists would skip each session's write-down, so this would have to deliver `/shift-change` into each session rather than signal it.

**Sequencing:** right after [Move Patchbay into its own repo](#move-patchbay-into-its-own-repo-2026-11-07), so the loop is written in Patchbay's copy of `agent`; its `/end-session` dependency is met (shipped 2026-10-31). Before the `pbay` merge, which moves the loop to its permanent home. Ahead of the Patchbay team release, which is on hold anyway; the team gets `/shift-change` with the merge.

**Plan:** none yet; next step is `/gameplan shift-change`.

**Status:** Queued 2026-10-18 as `/reload`; goal corrected and renamed 2026-10-19. Not planned.

---

## Upcoming

Ordered by priority. The Terminal & editors thread has nothing queued;
new items for it go here with a **Thread:** tag like everything else.

### Fork `claude-ps` for the public as `facetdigital/claude-ps`

**Thread:** Tools (Patchbay)

**Goal:** `claude-ps`, the `ps` for Claude Code sessions, becomes a small standalone open-source tool for anyone running lots of Claude Code sessions, orchestrated however they like. It works with Scott's launchers but does not require them and does not know they exist: a session started by `agent` or `claude-run` is just a Claude Code session to it. (Scott, 2026-11-03.)

**This is a fork point, not an upstream.** Today's script splits in two. This fork is tweaked for public use. The other copy moves into Patchbay and becomes [`pbay ps`](https://github.com/facetdigital/patchbay/blob/main/docs/plans/development-roadmap.md#pbay-ps-sessions-across-harnesses), which lists only `pbay`-started sessions, of any harness. Neither depends on the other and nothing keeps them in sync; a fix worth having in both is ported by hand. (Scott, 2026-11-03.) Why not keep `claude-ps` as the upstream with `pbay ps` wrapping its `--json`: once `pbay ps` covers other harnesses, a Claude-only upstream is the wrong base.

**Decided:**
- **Generic and Claude-only.** No Patchbay references. The script's marked "Patchbay enricher" section (`detect_route`, `resolve_route_alias`, the launcher cases) stays in Patchbay's copy, and the usage examples lose their agent names.
- **Private for months, and maybe squashed before it goes public** (Scott, 2026-11-03). Fresh history. Old Facet things and references are okay to start with, as long as they are loosely coupled and cheap to strip at the squash. Nothing that paints the tool into a corner.
- **Keep the [LinkedIn post](#write-up-claude-ps-linkedin-post) current** whenever this fork's plan or columns change (Scott, 2026-11-03).
- **The helper filter cannot name Scott's scripts.** Today's filter hides `claude-end-session`, the route selftest and the other scaffolding by name. The public fork needs a generic rule, or none; decide at plan time.
- **macOS only.** Linux support is a later roadmap item in the new repo (containers are the likely way to test it).
- **Slackline's release conventions** (`~/src/facetdigital/slackline`): `VERSION` is the number of record, tests keep every copy of the version and the README's install URL equal to it, and the release steps live in `CONTRIBUTING.md` (tag `vX.Y.Z`, a GitHub release with the files attached). No release workflow in GitHub Actions; tests only.
- **The repo:** a casual, friendly README, MIT licence, `CLAUDE.md`, an install script, tests (bats and shellcheck), and `--version`.

**Sequencing:** independent of the Patchbay chain; it blocks nothing and nothing blocks it. Fork from wherever the script lives at the time: dotfiles before the move, Patchbay after.

**Run interactively.** Creating a GitHub repo is an outward-facing step.

**Plan:** none yet; next step is `/gameplan claude-ps-oss`.

**Status:** Queued 2026-10-20; re-cut as a fork 2026-11-03. Not planned.

### Audit log generator follow-ons

**Thread:** AI Staff

**Goal:** Everything v1 deliberately refuses or leaves out.

**Status:** The first tier landed 2026-09-23 with the v1 merge (PR #4):
provider and model in the stats strip, the work log as an aligned table with
per-step durations, the index page, and error rows during a sweep. Everything
below that is still queued, and none of it blocks using the tool.
[audit-log-followons-batch.md](audit-log-followons-batch.md) records why each
remaining item was NOT in that batch.

Ordered for value, not for size: cheap changes that improve **inspecting
agent-to-agent conversations** come first, then work that makes more sessions
renderable at all, then anything needing a decision before it can be built, then
research. Each tier is meant to be finishable without leaving half-built work
behind.

#### Do first: cheap, low risk, immediate inspection value

1. **Provider and model in the stats strip.** ~~Show what actually served the
   conversation, not just the model: `OpenRouter / gpt-5.6-sol`,
   `Ollama / glm-4.7-flash`, `Anthropic / claude-fable-5`. Today the page names
   the model and leaves you to infer the rest.~~ **Done 2026-08-16** in the
   unattended batch: `provider_for()` in `cost.py`, driven by a `providers`
   map in `pricing.json`, and the provenance strip's Model row now reads
   `Anthropic / claude-opus-5`. Unknown models say `provider unknown`.

   **Measured 2026-08-16: transcripts record no provider, base URL, or
   endpoint at all.** Checked every top-level record field on real routed
   sessions; there is nothing to read. Provider has to be inferred from the
   model id, which the pricing table already does to decide what is unpriced,
   so this is mostly wiring plus a stats tile. Consequence worth accepting up
   front: **which Ollama host is not recoverable.** localhost versus an IP
   versus a hosted endpoint is not in the file, so it would need either a
   config map or a change to what Claude Code records. Show the provider now
   and leave the host for later rather than guessing it.

2. **Work log as an aligned table, with per-step duration.** ~~Make the log read
   as columns rather than a stack: the `+` becomes a rotating arrow, then
   timestamp, then a badge, then the label and its sub-label, with duration
   right-aligned at the end. Narration rows (the italic blockquote ones) get a
   badge of their own so every row has one and the columns actually line up.~~
   **Done 2026-08-16** in the unattended batch, duration half only: six-column
   grid rows (arrow, time, badge, tool, label + sub-label, duration), a `SAY`
   badge on narration rows, and `Event.duration` in `parse.py`. Tokens per
   step remain item 5 below, undecided.

   **Durations are free.** A tool call's wall clock is the gap between the
   record emitting the `tool_use` and the record carrying its `tool_result`;
   measured on a real brief, that yields 0.00s to 0.66s per call. No new
   parsing, no ambiguity. Pure presentation plus arithmetic, so it is cheap to
   build and cheap to verify.

3. **An index page of every conversation there is to render**, not just the
   ones already rendered. **Done 2026-08-16** in the unattended batch:
   `--index` writes `~/.ai-staff-audit-log/index.html` from `index.py`, with
   `PAGE` / `TO DO` / `V1 CAN'T` rows, copy-able commands on the `TO DO`
   ones, and `--all --index` to sweep then rebuild. The rest of this entry is
   the spec it was built to. Scans the project directories, lists every
   agent-to-agent conversation across the fleet newest first, and marks each row
   as generated or not. Generated rows link to their page. **Ungenerated rows
   expand to show the command that would produce them**, with a copy button that
   puts just the prompt on the clipboard: paste it into a Claude session,
   refresh the index, and the row becomes a link.

   Deliberately not a web app. Nothing on the page executes anything; the copy
   button is a clipboard write and the generating happens in a session the user
   drives. That keeps it a static file like every other page this tool
   produces, with no server, no auth, and no way for the index itself to touch
   the transcript store. A row that generates itself on click is a different
   product and is parked far below.

   Most of the scanning already exists: the `--latest` walk classifies sessions
   newest-first and produces exactly the per-session summary a row needs.
   Scott's call 2026-08-16, chosen over the cheaper "index of what you happened
   to render", because the question worth answering is what the agents did, not
   what has been rendered so far.

#### Next: makes more sessions renderable, or more honest

4. **Multi-turn rendering.** The single biggest structural change: the
   one-prompt-one-reply framing collapses and needs repeating turn groups.
   Sessions run to 76 real user turns. Deliberately not first, because the
   agent-to-agent briefs this tool exists for are single-turn and already
   render; this is what unlocks *interactive* sessions, which is half the
   corpus but not the immediate need.

5. **Per-step tokens and tokens per second.** The other half of the table
   above, split out because it is not cheap and not obvious.

   **The blocker is attribution, and it is the same trap as F1.** Token counts
   are per API message, and one message's content is spread across many rows:
   measured on a brief, a single message's usage covers 8 content blocks.
   There is no per-tool-call token count in the data. Dividing a message's
   tokens across its rows would invent a number, which is exactly the error the
   golden test exists to prevent. Options, none free: attribute the whole
   message's tokens to the message's first row and leave the rest blank; group
   rows visually by API call and put the figure on the group; or show tokens
   per second only at the message level. **Decide before building.**

6. **Image blocks.** Present in 8 of the 30 surveyed transcripts once those
   nested inside tool results are counted. Needs thumbnailing or a placeholder
   chip; base64 inline would balloon the page.

7. **Scale and an output size budget.** The largest transcript is 44 MB and v1
   refuses above 8 MB. Needs a per-result truncation threshold and an overall
   budget.

#### Queued, cheap, no decision needed

**A project allowlist or blocklist for `--all`.** A bare `--all` currently
sweeps every project directory, which today is 42 of them and only some are
agent-to-agent staff comms; the rest are ordinary interactive work that gets
skipped anyway. Sweeping them all is fine at this size (345 sessions, under
three seconds, and the skips are one line each), so this is deliberately not
urgent. It becomes worth doing when the noise outgrows the signal: an
`all_projects` allowlist in `participants.json`, or a blocklist, with a flag to
override. Scott's call 2026-08-16: do them all for now, add the filter later.

#### Needs a decision before it can be built

8. **Cost as a share of the subscription, alongside list price.** These
   sessions run on a Claude subscription, so the current figure is what the
   traffic *would* cost through the public API. The more useful number is what
   share of the month it actually consumed: if a plan costs $200 and covers N
   tokens, a conversation using 10% of N cost $20 of the bill. Show both: the
   subscription share and the pay-as-you-go price side by side. In API mode
   there is no share to show, so the page stays as it is today.

   **N is Scott's measured average** (decided 2026-10-31, asked directly): the divisor comes from his own observed monthly token usage, not a figure set in config or a modelled cap. Anthropic publishes no monthly allotment, so a measured average is the only number grounded in real use. Ready to build; how the average is measured is a plan-time detail.

9. **Real pricing for OpenRouter and other providers.** Extend the rate table
   past Anthropic so routed sessions cost out properly instead of rendering
   with the figures suppressed. OpenRouter publishes per-model pricing and
   returns generation cost, though the transcript captures only token counts,
   so this likely means a second rate table rather than live data. Ollama and
   other local runtimes stay genuinely unpriced, which the page already handles.

10. **No retention policy.** Generated pages are kept forever in `~/.ai-staff-audit-log/`, a local folder outside any repo (never this public one), so nothing prunes it and nothing needs building (Scott, 2026-10-31, asked directly).

11. **The `--annotate` pass.** Optional model-assisted enrichment: tool-call
    one-liners for tools the regex table does not know, side-effect prose, and
    participant names where nothing records them. Quarantined to a sidecar JSON
    file so rebuilds stay instant, free, and byte-reproducible. Deliberately
    never in the render path.

#### Far out

13. **A fleet dashboard.** The index above answers "what conversations exist and
    which are rendered". A dashboard is the bigger thing: activity across every
    agent over time, spend, failure rates, which agents talk to which. Likely
    waits for the Smykowski integration and may belong there rather than here,
    since by then the interesting questions are about the fleet rather than
    about any one conversation. Recorded so it is not rediscovered as a new
    idea. Scott's call 2026-08-16: far later, explicitly not now.

#### Research, not scheduled

12. **Can reasoning text be recovered at all?** Today the page shows a token
    count and a truncated signature and says plainly that the content is not
    recoverable, because Claude Code stores only the signed, encrypted block.
    The question is whether anything could be captured at streaming time
    instead, before it is discarded, and what that would cost: it would mean
    intercepting the API stream rather than reading the transcript, which is a
    different architecture and a different trust posture. Scope this as a
    written finding first, not a build. Expect the answer to be that it is
    possible only by standing between the harness and the API, which is a much
    bigger thing than an audit log page. **Research and write up; do not start
    building.**

### Acceptance-test the Servanda kit

**Thread:** Servanda

**Goal:** Walk Tiers 0 through 4 of the kit's manual test plan. The suite is now baselined and its review fixes applied, so there is finally something real to test against, and it has had **zero** acceptance testing so far.

**Plan:** [command-kit-overhaul.md](command-kit-overhaul.md)

**Status:** Unblocked as of 2026-07-30. Both prerequisites landed: the suite baseline and the review fixes. **Tier 0 agreed 2026-09-02, deferred to a later day:** the answer was "sure but not today", so offer it opportunistically rather than asking again for permission.

Deliberately opportunistic. Tier 0 is about five minutes and needs no project; run it first. Tiers 1 through 3 need one real small feature in a low-stakes repo. Tier 4 needs a genuine phase boundary with a `PHASE GATE:` marker. Per the plan's own philosophy: no throwaway sandbox, test each behavior the next time real hobby-grade work offers the opportunity.

**The route-launcher plan above IS that opportunity.** It is a real, low-stakes, ten-step feature in this repo with a normal plan file, which is exactly what Tiers 1 through 3 need. Running it through `/booyah` or `/yolo` acceptance-tests the kit and ships the feature in one pass, which is why it now sits ahead of this item rather than behind it. Tier 4 still needs a genuine phase boundary and is unaffected.

**Ordering decision (2026-07-29):** test BEFORE the rename, even though the rename touches every command the checklist names. The rename is a mechanical layer on top; verifying behavior first is cheaper than verifying a spec that is about to be renamed. Accept that a name sweep of the checklist follows the rename.

**Worth doing early, while testing:** confirm `ANTHROPIC_DEFAULT_FABLE_MODEL` is actually honored, not merely present in the CLI binary. `strings` proved the name exists; nothing has proved the behavior. Gates are the wrong place to discover that assumption was wrong. Note the route-launcher plan's Gate A now covers this directly.

### Command Suite Rename (verb-scope grammar + /implement-phase)

**Thread:** Servanda

**Goal:** Rename /gameplan, /booyah, /yolo, /beastmode to /plan-feature, /implement-step, /implement-feature, /implement-roadmap; add net-new /implement-phase; record the hierarchy, delegation-decision rule, and trust-substitution ladder in COMMANDS.md.

**Plan:** [command-suite-rename.md](command-suite-rename.md)

**Status:** Ready to implement. AWAITING SCOTT'S EXPLICIT GO. Do not auto-start. Blocked on the batch landing above (the plan header's pre-step); acceptance testing should also come first per the ordering decision above. **Hold reaffirmed 2026-09-02:** asked directly and the answer was "not yet"; do not ask again until he raises it or the acceptance testing above is done.

### Upstream doc-lifecycle skill suite (incubating in timercue)

**Thread:** Servanda

**Goal:** Extend the kit upstream of `/roadmap` with a briefing-to-roadmap document
lifecycle: an idea dump becomes `00-PRODUCT-REQUIREMENTS.md` (interrogate-until-frozen
PRD), then `01-TECHNICAL-FEASIBILITY.md` (spike plan with agent-run and human-run
steps, verdicts feeding a DECISION-LOG and `docs/adr/` ADRs), then `02-UX-DESIGN.md`
(semantic "markdown design": surfaces, states, affordances, copy; no pixels), then
`03-ARCHITECTURE.md` (system + technical design, state-transition test matrix), then
`/roadmap` synthesizes `development-roadmap.md` from 00-03 risk-first (kill-risks
early, walking-skeleton proof of life, phases ending in PHASE GATE markers). Candidate
skills: PRD, feasibility, UX design, architecture, plus an ADR writer; final names
deferred but should follow the rename plan's verb-scope grammar. Also deferred to this
item: renaming `development-roadmap.md` to a numbered `04-` form, which touches every
command that reads the roadmap path, so it must land as one suite-wide change.

**Status:** Incubating, and dormant. **Checked 2026-09-02:** no incubation work has happened since the doc structure landed on 2026-08-01, so nothing has moved toward stable skill drafts. Left open deliberately; revisit later. The lifecycle is being hand-executed first in
`~/src/facetdigital/timercue` (the TimerCue app, formerly harvest-activity-guard) (doc structure landed 2026-08-01; skill
notes accumulate in that repo's `docs/notes/skill-lab.md`). Draft skills will be
built and tested in that repo's `.claude/` against the real build of Harvest Activity
Guard, then extracted and elevated into Servanda after real-world use. No dotfiles
work yet; do not start here until the incubation run produces stable skill drafts.
Decision context: spec-kit, superpowers, and SDD-style frameworks were evaluated
2026-08-01 and rejected wholesale; steal patterns only (constitution, clarify
discipline, spec-per-feature granularity stays with /gameplan).

### Memory-durability hook: move to Option D (detect the effect, not the command)

**Thread:** Servanda

**Goal:** A hook that fires when a session writes to `~/.claude/projects/*/memory/*` and reminds it that the file is gitignored, unbacked, and invisible to a fresh clone or a fresh-context run, so anything that must survive gets written into the repo instead.

**Status:** Needs a gameplan. **AWAITING SCOTT'S EXPLICIT GO, and do not auto-start.** Relayed to this repo on 2026-09-10 by the Greenthumb session as a decision Scott made in a greenthumb office-hours round that day. Recorded here so the decision is not lost, but a peer's relay is not the same as Scott saying go in this repo, and the implementation edits `settings.json`, which is config.

**The decision:** Option D. Detect the *effect* rather than the command: after any matched tool call, check whether a memory file's mtime changed in the last ~120s.

**Why the current shape fails.** The hook matches `Write|Edit` tool calls. Observation across two live sessions on 2026-09-08 and 09 (Greenthumb's and Donna's) found that almost all memory writes go through Bash instead: `sed -i`, `echo >>`, redirects, `cd` plus a relative path. The hook would have fired zero times across the exact work it exists to protect. Option D was tested informally on 2026-09-09 and caught Bash appends, `sed -i`, new files, and `cd` plus relative writes, while staying silent when nothing changed. It needs no command parser and tolerates no false positives. It is post-hoc rather than preventive, but a fresh session still sees the reminder and can act on the next turn.

**Options already rejected**, so they are not re-proposed: (a) keep matching `Write|Edit`, which the observation above disproves; (b) narrow-match Bash with a command parser, which is the thing Option D exists to avoid; (c) drop the hook entirely and rely on the memory-versus-repo block in `CLAUDE.md`, which auto-loads on fresh sessions and did the real work unaided on 2026-09-08 and 09. Option (c) is the honest fallback if Option D proves noisy, and is worth re-reading before building.

**Correct the handoff's premise before planning.** The relay said the hook already lives in `~/.claude` and is therefore user-global. It does not, as of 2026-09-10. It is in `~/src/scottwb/greenthumb/.claude/settings.json`, greenthumb-scoped, and dotfiles' own `settings.json` has **no** `hooks` key at all. Its message text is also greenthumb-specific, naming "the nightly greenthumb brief". So the work is three things, not one: move it to user-global, generalize the message off greenthumb, and switch the detection to Option D. Scope the gameplan accordingly.

**Source material:** `~/src/scottwb/greenthumb/docs/plans/memory-durability-hook.md` is the historical record and explicitly must not be built from; greenthumb's `docs/open-questions.md` records the decision as answered. Greenthumb offered its 2026-09-08 install test matrix on request; otherwise design fresh.

### Evals as a Servanda verification tier

**Thread:** Servanda

**Goal:** Every feature or epic ships with one or more evals as part of its definition of done, and an eval result sits beside tests and review as a verification tier in the implement commands.

**Status:** Needs a gameplan. **AWAITING SCOTT'S EXPLICIT GO, and do not auto-start.** Relayed on 2026-09-13 by the Donna session as decisions Scott made that day. Recorded so they survive, but a peer's relay is not Scott saying go in this repo, and this one shipped two mis-attributions that were retracted the same day (the lessons are in `.claude/CLAUDE.md`, "Messages between sessions").

**Scott-direct, per the relay:**

- `/gameplan` gains an eval step. A feature plan names a few coarse STAGES plus the final outcome, and per stage: what it covers (skills, prompts, scripts), a rubric fixed before the run, and an acceptance range. Explicitly NOT per item, in his words "don't go down to how did the model do on each photo". Item level is for debugging only.
- Each plan names the models to run. First results are human-reviewed against Fable, the current benchmark. The point of scoring by stage is that a later decision can assign different models to different stages.
- Eval is a verification tier beside tests and review in `/booyah`, `/yolo` and `/beastmode`. It needs a rerun rule like tests, balanced against cost: a dozen frontier-model evals on every check-in is too much.
- **`/implement-phase` wins.** Keep Step 5 of [command-suite-rename.md](command-suite-rename.md) as written; a `/beastmode` scope argument and stop-at-passed-gate flag are dropped, and that plan is not to be edited to make room for them. It stays on hold regardless.
- Cross-repo end-to-end integration testing is Scott's own later effort. Do not build cross-repo orchestration into Servanda now.

**A proposal he has NOT ruled on**, so do not carry it as settled: deterministic checks on every change; a stage eval rerun on one cheap model when a file it declares coverage of changes; the full model matrix at milestone gates, on model releases, or on demand; the Fable baseline recorded once and reused until the feature changes; every run recording cost against a budget cap.

**The eval kit is "gauntlet"**, its own repo, prototyped in greenthumb, and it builds on Patchbay rather than reimplementing harness, model and provider switching. What it will want from here: a scriptable way to launch a run with a given harness, model and provider in a given worktree; per-run tokens, dollars and time; and the audit tier left unmapped on routed sessions so judges and the Fable baseline run on a plain Anthropic session. **That last one already holds** (the D12 block in Patchbay's `claude-run`), verified 2026-09-13. Gauntlet is also the strongest case yet for the `pbay` front door, which stays blocked.

### Split the acceptance checklist into record plus regression suite

**Thread:** Servanda

**Goal:** [command-kit-overhaul.md](command-kit-overhaul.md) is doing two jobs in one file: a one-time acceptance record for the 2026-07-05 batch, and what is really a reusable manual regression suite for the kit. Most of its tier items are worth re-running on every future kit change, not just this one. Split it: the batch record stays as history, the reusable items graduate to `docs/testing/servanda-manual-tests.md`.

**Status:** Deliberately deferred until AFTER the rename, and this is the right time to revisit it. The rename renames every command the checklist names, so splitting first would mean sweeping names through two files instead of one. Doing it after means the tier items get renamed once, then reorganized once.

Tradeoff if you want it sooner: split now and the tier items get renamed in place later; split later and the file gets reorganized once. Either is fine, the ordering above is just the cheaper one.

### Competitive absorption: other governors

**Thread:** Servanda

**Goal:** Investigate same-space projects, catalog their strengths/weaknesses, and absorb anything worth learning into our kit. Explicitly deferred: get ours rock solid FIRST, then do the absorption pass.

Targets found 2026-07-11 while vetting the "Governor" name:

- [0xhimanshu/governor](https://github.com/0xhimanshu/governor) - "Governor for Claude Code": Claude Code plugin for context hygiene, tool-output filtering/compression, memory compression (/governor:compress CLAUDE.md), telemetry, drift guardrails. Angle to study: context economy during long runs (relevant to our subagent-recursion future decision).
- [Fr-e-d/AI-Governor-Framework](https://github.com/Fr-e-d/AI-Governor-Framework) - "The Keystone Framework for AI-Driven Code": turns any AI coding assistant into a disciplined, project-aware partner respecting architecture and coding standards. Concept-neighbor to our whole thesis; study how they encode standards/architecture awareness and what their gaps are.

Add further targets as found (superpowers, spec-kit, and Gas Town were already compared in depth in the July 2026 naming conversation; notes could be reconstructed on demand).

**Status:** Needs planning (do not start until the kit is stable post-rename)

### Literal recursion via subagents

**Thread:** Servanda

**Goal:** /implement-roadmap spawns a fresh subagent per phase; /implement-phase spawns a fresh subagent per feature, so long runs get fresh context per feature (feature #9 starts as clear-headed as feature #1). Per-feature is the natural boundary (already the branch + review boundary).

**Status:** Needs planning (recorded as a future decision in the rename plan; real architectural change, deserves its own plan)

### Deep-vet "Servanda" before any public repo

**Thread:** Servanda

**Goal:** Full conflict vet (npm, PyPI, crates, GitHub orgs, trademark-adjacent products) before the name appears on a public repo or launch material. Quick web vet came back clear 2026-07-13. Not blocking internal use or the talk.

**Status:** Deferred until open-sourcing is on the table

### Write up `claude-ps` (LinkedIn post)

**Thread:** Tools

**Goal:** A short post introducing `claude-ps`, the `ps` for Claude Code sessions: agent name, working directory, branch, harness version (green/yellow/red against latest), provider, model, effort, context used with a red cell past 80%, and with `-l` the permission mode, PID, status (idle / busy / waiting / stale / zombie / stopped, with a coloured margin dot), uptime, memory, CPU. Subagents nest under their parent. Angle: everything it shows comes from what Claude Code already writes to disk (`~/.claude/sessions/<pid>.json`, the transcript) plus the process table; no daemon, no network, one bash script. **Venue: LinkedIn** (Scott's call, 2026-09-02), chosen over a personal blog post or the internal Facet channel.

**The post is about the public fork,** not Patchbay's copy (Scott, 2026-11-03: keep this item up to date as the fork's plan changes). The provider and routed-model columns come from Patchbay's route enricher, which stays out of the public fork, so the post drops them, and the screenshot below needs a reshoot from the fork. Patchbay itself is a Facet tool and has no post planned.

**Asset:** [assets/claude-ps-demo-2026-08-19.png](../assets/claude-ps-demo-2026-08-19.png), a demo screenshot of `claude-ps -l` with lightly redacted names and every status/colour state shown. Taken 2026-08-19 with temporary demo hacks that were removed before commit, so it cannot be regenerated as-is; reshoot from a live session if the columns change.

**Status:** Queued 2026-08-19. **Not yet, as of 2026-09-02:** the overhaul commit has landed and the venue is settled, so the only thing holding this is Scott's appetite for writing it; asked directly and the answer was "not yet". **Related (2026-10-20):** `claude-ps` is queued to be forked as the public `facetdigital/claude-ps`, staying Claude-only, and it stays private for months first. The post waits for that repo, so it has something to link (Scott, 2026-10-31), which now means waiting until it goes public.

### `/write-that-down`: ask whether this repo owns a fact before writing it

**Thread:** Servanda

**Goal:** Give the sweep a step that asks whether the repo it is running in owns a fact, before the fact is written down, and stop a peer agent's claim from landing as settled fact.

**Status:** Needs a gameplan. **Go given 2026-10-31** (Scott, asked directly in `/office-hours`). Relayed 2026-09-17 by the Sri session, with Scott saying this repo owns the fix; filed 2026-10-05 after he asked for it directly. Next: `/gameplan write-that-down-ownership`.

**Two failures in `~/src/scottwb/sri`, both verified in that repo's history.** A knowledge sweep found a first name in a homework-status line with no identity behind it, researched him, and opened a People entry in `synthesis.md`. He is a Facet business contact who belongs to FAW and Donna, not a coaching vault. Reverted in `c7ba3c3`, with the scope rule added in `391254a`. Separately, a peer agent's claim that Donna had restarted mid-thread was written into that repo's CLAUDE.md as settled fact, with no source and no hedge; Donna says it has not happened. **That one is still contested and was never resolved**, so a gameplan should treat it as an open question rather than a fact in either direction.

**This is a change to the global command, not a promotion of a local variant.** Checked 2026-10-05: sri has no `.claude/commands/` at all, and `.claude/commands/write-that-down.md` here is the only copy in existence, global from birth via the `~/.claude` symlink (`26e00ec`, 2026-09-09). What sri patched after the incident was its own `pre-session-prep` skill and its own CLAUDE.md, which is where a vault-specific rule belongs. The global command still has no step that asks the ownership question, which is why the same sweep would do the same thing in any repo.

**Scope context Scott gave on 2026-09-17:** a repo like sri tracks whether he is doing what his advisors discuss, not business or RevOps to-dos. Those belong to FAW and route through Donna. The sweep has no step that asks "does this repo own this fact, or should it go to another agent?"

**Directions, none decided.** An ownership check against the repo's own CLAUDE.md before anything is written; an unidentified name treated as a signal that it does not belong rather than a gap to fill; a peer's claim recorded with its source, or checked, rather than stated flatly. **Note before planning:** Step 4 of the command already says never to record intent or prediction as settled fact, and the command's own guidance says to sharpen an existing rule or add the missing trigger rather than add a second rule. So the second failure is a trigger problem, and only the first is a genuine gap.

### Detect a regenerated `autoMode` profile in the tracked settings.json

**Thread:** Servanda

**Goal:** Fail loudly when `/auto-mode-setup` overwrites the repo-neutral `autoMode` profile in `.claude/settings.json`, before the change is committed to this public repo.

**Status:** Needs a gameplan. `docs/assessments/config-propagation.md` said this check was "queued as a roadmap item" from 2026-10-05, but it was never filed; filed here 2026-10-08. Since 2026-10-07 the neutral profile is meant to be there, so the check must compare against it (or reject any entry naming a repo or path) rather than fail on the key's presence. Where it runs (pre-commit hook, `/booyah` guard, a test) is undecided.

### Status line: clear the workflow mode label when the workflow is over

**Thread:** Servanda

**Goal:** `.claude/statusline.sh` shows Yolo Mode, Booyah Mode or Beastmode only while that workflow is actually running.

**Status:** Needs a gameplan. No fix now. Relayed 2026-10-07 by the FAW session as Scott's direction: put it on this roadmap, and this repo owns it.

**The bug, seen in FAW:** a `/yolo` merged (FAW PR #10) and the session went back to main with a clean tree, but the status line kept saying Yolo Mode for the rest of the session, across unrelated commands. Cause, in segment 4 of the script: the mode comes from the most recent `<command-name>` matching yolo, booyah or beastmode in the transcript's last 4 MB tail. Every other slash command is filtered out before the match, and nothing checks whether the work finished, so the last of those three wins until another one runs, the session restarts, or it scrolls out of the tail. Here the last one was `/yolo done`, the wrap-up itself.

**Directions, none decided, smallest first:**
1. Take the latest slash command of any kind, and show the workflow label only if that command is one of the three. Any other command clears it. Residual: the label still shows right after `/yolo done` until the next command.
2. Also require a `feature/` branch checked out (segment 1 already knows the branch). A wrap-up ends on main, so the label clears when the merge lands. Risk: hides the label for a run on an unusual branch, such as a worktree not named `feature/`.
3. Treat `/yolo done` (and any other wrap-up form) as an explicit clear.

Once the label clears, the permission-mode fallback (Auto Mode and so on) should show, which the script already does when no workflow command matches.

### Extract kit to its own repo (someday)

**Thread:** Servanda (and the thread's exit condition: this item ends Servanda as a dotfiles thread)

**Goal:** Move `.claude/` kit files and `docs/plans/` kit plans out of dotfiles into a standalone `servanda` repo, with install/symlink story, README (lead with the accountability loop; ladder as the teaching diagram; re-invocation grammar as the mechanism; "pacta sunt servanda" epigraph; motto candidate: "ships what it promised, proves what it shipped"), and license decision.

**Status:** Someday; explicitly not now

**Related decision (2026-07-29): no `~/.servanda` dotdir.** Servanda *is* Claude Code commands, so a separate home directory would have to be symlinked back into `~/.claude/commands/` to function, buying indirection and nothing else. The split that actually pays is runtime-vs-dev-artifact: runtime specs in their dotfile locations, dev artifacts in `docs/` (recorded in [land-baseline-commits.md](land-baseline-commits.md) Step 2). Extracting to this repo is the only thing that justifies a new home. Checked 2026-07-29: no `servanda` or `servando` repo exists locally under `~/src/scottwb` or `~/src/facetdigital`, nor in either GitHub org, so the name is unclaimed but also has no code behind it yet.

---

## Completed

### Move Patchbay into its own repo (2026-11-07)

**Thread:** Tools (Patchbay)

Patchbay now lives in the private repo [facetdigital/patchbay](https://github.com/facetdigital/patchbay), cloned at `~/src/facetdigital/patchbay`, with fresh history. `agent`, `claude-run` and `claude-ps` moved byte-identical, with Patchbay's design doc, plans, gate reports and roadmap items; the route selftest became Patchbay's `test/route-selftest`. Patchbay's `install` links its `bin/*` into `~/.local/bin`. All 24 recorded `agent` invocations produced the same `claude` command from Patchbay's copy as from dotfiles', from two directories, and `claude-run`'s dry runs and `claude-ps`'s session list were unchanged. Dotfiles' `claude-end-session-selftest` now checks that Patchbay's `claude-ps` still hides dotfiles' helpers. Removed from dotfiles at HEAD only; history is untouched in both repos.

**Plan:** [patchbay-repo.md](patchbay-repo.md)

### `/end-session`: write it down, then exit (2026-10-31)

**Thread:** Servanda

**Goal:** One command for "I'm done with this session": run `/write-that-down`, then exit. It works in any session, plain `claude` included, and needs nothing from Patchbay. (Scott, 2026-10-20.)

**The chain.** Three commands, each one the previous plus one step:

| Command | Does | Needs |
|---|---|---|
| `/write-that-down` | Records and commits what only the session knows. The session keeps going. | Nothing |
| `/end-session` | `/write-that-down exiting` (the sweep, then the repo's Pre-Exit Steps), then exits. | Nothing |
| `/shift-change` | `/end-session`, then a fresh session comes up at the same post. | The Patchbay runner's relaunch loop |

**The agent cannot type `/exit`,** so exiting needs a signal. As its last step, after the write-down succeeds, the model runs one fixed command, `bin/claude-end-session`, which sends SIGTERM to the nearest `claude` ancestor and refuses if there is none. Why not a `!` line: Claude Code runs a command file's `!` lines when it expands the command, before the model reads it, so a `` !`kill -TERM $PPID` `` line would exit before `/write-that-down` started (found 2026-10-25). SIGTERM gives exit 143, which the `/shift-change` relaunch loop will read as "stop", while SIGHUP (129) will mean "come back".

**Never exit over an unrecorded session.** If `/write-that-down` fails, stops to ask a question, leaves a file it wrote uncommitted, or reports a failed Pre-Exit Step, `/end-session` stops there and the session stays up. Unrelated uncommitted work and unpushed commits do not block; the closing record names them.

**When it runs.** Scott's phrases, and what each one means:

| Scott says | Means |
|---|---|
| "record what we learned", "write that down" | `/write-that-down` |
| "exit the session", "I'm done with this session" | `/end-session` |
| "new context and restart", "get the harness update", "shift change" | `/shift-change` |
| "heading out for a few hours" | Nothing. The session waits. |

An explicit request runs immediately. A phrase that only implies it gets a one-line confirmation first (Scott, 2026-10-20). The trigger lines are in the Proactive Suggestions in `.claude/CLAUDE.md`.

**No Donna briefing.** These commands are meant for everyone, and Donna runs her own daily checks (Scott, 2026-10-20). The peer-handoff idea that would have briefed her is dropped; its lessons about relays live in `.claude/CLAUDE.md` under "Messages between sessions".

**Not a revival of the 2026-08-14 `/end-session`** (commit `48415e6`, never merged). Its three sweeps shipped as `/write-that-down` and its handoff step is dropped, so only the name comes back, with a new job.

**Verified 2026-10-25 on 2.1.310:** SIGTERM gives exit 143, interactive and headless; Claude keeps the transcript through the final answer and writes its shutdown entries; the Remote Control session drops off the phone's list with no dead entry; `$PPID` from the Bash tool is the Claude process.

**Plan:** [end-session.md](end-session.md)

Shipped in four commits plus this one: `bin/claude-end-session` with a selftest that is safe inside a live session (22 assertions, fakes in detached process trees), `.claude/commands/end-session.md`, and the docs. Accepted 2026-10-31 on 2.1.316 in a throwaway repo: nothing to record, something to record under `agent` with the phone, a commit blocked by a pre-commit hook (stayed up), a leftover dirty file (named, then exit), and an implied phrase (asked first). Headless `-p` runs skip the closing record, which never shows there anyway.

### The index's copyable command, and the describe guards (2026-09-23)

**Thread:** AI Staff

**Plan:** [audit-log-index-command-and-guards.md](audit-log-index-command-and-guards.md)

**Gate report:** [phasegate-audit-log-gate-fixes.md](../assessments/phasegate-audit-log-gate-fixes.md)

Merged via PR #7, two commits, both findings of the second phase gate. Suite 428 to 437 tests.

**The index's copy button had never emitted a command that runs.** Every project directory name begins with a dash, argparse reads a dash-led token after `--project` as an option rather than its value, and the line exited 2. It emits `--project=` now, value still quoted. The lesson is in how it survived: the regression test written with the quoting fix asserted the command was byte-identical to what the index had always emitted, which fused "no quoting was added" to "the line still does not parse", so the fix could only pass by keeping the bug. The test now checks the property it was protecting, and a new one feeds the emitted argv to the CLI's own parser. Verified against the real store by copying a `TO DO` row's command out of the HTML and running it.

**A session that could not be described still killed the index.** The earlier guard landed on `render_one`, while `index.scan` and the walking `--project` path called describe unguarded, so `--all --index` finished its sweep and died before writing anything. That was the harm the first gate's finding 2 named, surviving one call site over. Both paths now turn an undescribable transcript into a row, with `?` for participants rather than a guessed attribution on a file nobody could read.

**Both defects were the same shape:** something tested for the form it had rather than the job it does. Gate items 3 to 6 stay open in the report, along with items 7 to 9 carried from the first gate.

### Audit log gate fixes: findings 1 to 5 (2026-09-23)

**Thread:** AI Staff

**Plan:** [audit-log-gate-fixes.md](audit-log-gate-fixes.md)

**Gate report:** [phasegate-audit-log-phase.md](../assessments/phasegate-audit-log-phase.md)

Merged via PR #6, five commits, one per ranked finding from the first gate, each starting with a test that reproduced the defect the gate had demonstrated against real data. Suite 401 to 428 tests.

**The two high findings.** The rate table priced Sonnet 5 at $3 / $15, which is Sonnet 4.6's rates copied across against a published $2 / $10; the whole table was re-read from the published pricing page rather than a cached copy, which is what let the error through, and Claude Opus 5.5 was added along with Mythos 5.1, Opus 4.5 and Sonnet 4.5. Opus 5.5's 0.05x cache read is a second exception after Fable 5.1's 0.025x, so that multiple moved into the data and the hardcoded exception list in the test is gone. Separately, a sweep survived only a failed render: a transcript whose `usage` was a string killed a real six-session sweep after two, and every stage of `render_one` is now covered by the same ERROR row.

**The three mediums.** The index page's copy button interpolated transcript fields raw, so a crafted session id produced a copyable line carrying `; echo PWNED`, which the page invites you to paste into a terminal; ids are now UUID-checked with a quoted file-stem fallback and project names go through `shlex.quote`. Routed OpenRouter slugs were told to add Anthropic list rates that deliberately do not exist, now derived from `provider_for` rather than a second list. And a page written while its model was unpriced said nothing about it; it now marks itself so a later run offers the `--force` repair, while a permanently unpriced page stays quiet.

**Scott widened item 1 on the day:** refresh every row, not the one that was wrong, and add Opus 5.5, released 2026-09-22. That absorbed the first gate's item 6. Items 7 to 10 stay open in the gate report.

### Inter-agent conversation audit log generator (2026-09-23)

**Thread:** AI Staff

**Plans:** [audit-log-generator.md](audit-log-generator.md), then the unattended follow-on batch in [audit-log-followons-batch.md](audit-log-followons-batch.md)

Merged to master via PR #4 with full history, 55 commits. The `audit-agent-conversation` skill and its CLI turn one session transcript into a self-contained HTML page: the opening prompt, the work log, the reply, the derived side effects, and what the traffic would have cost at list rates. Pages land in `~/.ai-staff-audit-log/`, which is deliberately not a repo and not inside one. Four phase gates ran during the build; their reports are in `docs/assessments/`.

**The finding that shaped the design:** Claude Code writes one transcript record per content block and repeats the whole message's `usage` object on every one, so summing per record overcounted the reference session's output tokens by 2.5x. Deduplicating on `message.id` is load-bearing, and the golden test exists to keep it that way.

**Built 2026-08-15, merged 2026-09-23.** The only thing between those dates was manual testing, which is the one part an agent could not do for it. Three commits landed the day of the merge: list rates for `claude-fable-5-1`, whose sessions could not render at all once Greenthumb moved to it; rendering a page with the cost figures suppressed when a model is missing from the rate table, instead of failing the whole page; and stating each model's own cache-read multiple in the cost note rather than asserting 0.1x for everything. Suite: 401 tests.

**v1 is deliberately small.** Single-turn SDK sessions only, which is exactly what every Donna-to-agent brief is. Multi-turn rendering, image blocks, and the 44 MB scale case are deferred: v1 detects them and refuses cleanly with a non-zero exit rather than emitting a half-correct page. What remains is the follow-ons item under Upcoming.

### Fix the install instructions' `rm -rf .git` hazard (2026-08-01)

**Thread:** Machine setup

The install glob links *every* dot-entry into `$HOME`, `.git` included, so `~/.git` ends up pointing at the dotfiles repo and makes the whole home directory look like a checkout. The deletion that follows exists to undo that one bad symlink. Changed `rm -rf .git` to `unlink .git`, with a `ls -ld .git` look-before-you-delete line above it and a note explaining both.

The old instruction was correct as written. What it lacked was any margin for getting it wrong, verified with each case against a fresh target:

| Command | The symlink | The real repo |
|---|---|---|
| `rm -rf .git` | removed | intact |
| **`rm -rf .git/`** | still there | **destroyed** |
| `rm .git` | removed | intact |
| `unlink .git` | removed | intact |

One trailing slash inverts the outcome: macOS resolves through the link, recursively deletes the target's contents, and leaves the dangling symlink behind. Separately, `rm -rf .git` run from inside the repo by mistake destroys it silently, where `unlink .git` refuses with "is a directory". `unlink` cannot recurse and cannot follow a symlink, so both failure modes become harmless errors.

Surfaced while writing a safe recipe for testing the README against a throwaway `$HOME`, not from any plan. The corrected instructions were then run verbatim in that throwaway home and verified end to end.

### Apply the Servanda review fixes (2026-07-30)

**Thread:** Servanda

**Plan:** [servanda-review-fixes.md](servanda-review-fixes.md)

Four commits, `c6e41b2` through `03f33de`. Documented that model pins are tier aliases rather than vendor lock-in, flagged the unmapped audit tier in the parked Ollama profile with a decide-me marker, added provider preflight guards to `/beastmode` and `/phasegate`, and stopped `/booyah` and `/yolo` from assuming a pre-existing dirty tree is their own work.

Two notes worth keeping: the audit tier was deliberately left UNMAPPED rather than pointed at the local 30b, because a silently degraded adversarial audit is the exact failure STOP-not-degrade exists to prevent. And `/yolo` state 3 got a lighter scope check rather than `/booyah`'s hard ask, because its branch-match plus state 1's clean-tree precondition already narrow it.

### Baseline the Servanda suite overhaul (2026-07-30)

**Thread:** Servanda

**Plan:** [servanda-suite-baseline.md](servanda-suite-baseline.md)

Seven commits, `5ceaeca` through `08dbbb2`, on `feature/servanda-suite-baseline`, merged to master with full history. The 2026-07-05 overhaul (~1,400 lines across ten files) had existed only in the working tree for 25 days and is now in git: the /gameplan rename, the /yolo state machine, /phasegate, PHASE GATE awareness in /booyah and /roadmap, the /beastmode hardening, COMMANDS.md with /workflow-help, and the CLAUDE.md workflow table.

Both gates cleared: the five design questions on 2026-07-29, and Scott's read-through of the diffs on 2026-07-30. Every commit staged explicitly by path, never `git add -A`.

### Decide the Claude Code session model pin (2026-07-30)

**Thread:** Servanda (settings, not commands)

**Decided: keep the pin.** `.claude/settings.json` retains `"model": "claude-fable-5[1m]"`. An earlier working-tree state had removed it; that removal was reverted rather than committed, so `23706ca` landed only the three cosmetic preferences (`cleanupPeriodDays: 90`, `theme: dark`, `agentPushNotifEnabled: false`) and changed no behavior.

The parked `x-env` / `x-model` / `x-instructions` Ollama block stays untouched until its replacement is proven in separate work. It reads like cruft and is not.

Note this is the SESSION model only. It is independent of the suite's spawn-site tier pins, which resolve through `ANTHROPIC_DEFAULT_*_MODEL` (see Q2 in the suite plan).

### Land the independent baseline commits (2026-07-29)

**Thread:** Shell + Machine setup (plus two Servanda-adjacent doc commits)

**Plan:** [land-baseline-commits.md](land-baseline-commits.md)

Six commits, `d2b612f` through `7aff8a1`: ignore hygiene, the `docs/plans` relocation and roadmap rescope, the devcontainer theme fix, two aliases, the emdash rule's going-forward scope, and the 1Password secrets convention. The Servanda suite was deliberately excluded and stayed untouched.

Two findings worth remembering, both recorded in [servanda-suite-baseline.md](servanda-suite-baseline.md): `/booyah` cannot run a plan like this (its `git add -A` would sweep held work into a step commit), and `.claude/CLAUDE.md` needed per-hunk staging because it accumulates unrelated changes faster than a plan can reference them by number.

### Kit naming decision (2026-07-29)

**Thread:** Servanda

**Decided: Servanda.** Full candidate history, rejected names, and vet notes live in [command-suite-rename.md](command-suite-rename.md) Step 7's Future Decisions text. Remaining follow-up captured above as "Deep-vet Servanda."

---

## Pointers to Related Work Elsewhere (not roadmap items)

Canonical WORK-PLANs for Facet business work live in `facet-admin-workspace`, not here. Stubs only:

- **Patchbay** lives in [facetdigital/patchbay](https://github.com/facetdigital/patchbay) (private), with its own [roadmap](https://github.com/facetdigital/patchbay/blob/main/docs/plans/development-roadmap.md): `agent`, `claude-run`, `claude-ps`, the `pbay` work, `agent-colors`, the team release and the route launcher follow-ons. Install it with the step in the [README](../../README.md). `/shift-change` and the public `claude-ps` fork stay on this roadmap.
- **Pacta Sunt Servanda brown bag (rescheduled to 2026-07-31, noon Pacific):** the kit's public debut (concepts + the Servanda name; kit itself not shared). Materials and tasks: `facet-revops/demand-gen/talks/20260731-pacta-sunt-servanda/` and `demand-gen/WORK-PLAN.md`. Sponsor call transcripts may reorder/pivot talk concepts; that work happens entirely in the facet workspace, not here.
- **Clay alert sweep (recurring):** `/facet-clay-sweep` command lives in `facet-admin-workspace/.claude/commands/`. Triage state: `facet-revops/prospecting/clay-triage-log.md` (global log). Relevant to this kit only as another example of encoding process as executable policy.
