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

### Patchbay team release

**Thread:** Tools

**Goal:** Ship Patchbay to the Facet dev team as an OpenRouter fallback for Claude outages, in its own repository. De-personalize the launchers so they work for someone who is not Scott, and give the team a documented install and setup path.

**Plan:** [patchbay-team-release.md](patchbay-team-release.md)

**Status:** Ready to implement. Eight steps. Repo owner settled 2026-08-08: **`facetdigital/patchbay`**, so licensing and any future public release are a company decision.

**Why this jumped the queue (2026-08-08):** the extraction triggers written down on 2026-08-03 were "the ccr question resolves in favour of Patchbay standing alone, **or** someone other than you wants it." The second one fired. Scott's devs at Facet want a simple, low-dependency way to keep working through Claude outages, needing nothing beyond a credential in an environment variable.

**What is already true, and reduces the work considerably:** the env-var credential path already functions with no `op` on `PATH`, runtime dependencies are already just `bash`, `curl`, `sed`, `grep`, `ps` and `claude`, and the `ollama` binary is not a runtime dependency at all. What blocks sharing is narrower than it looked: the 1Password vault path is hardcoded, the selftest enforces that hardcoding, and the missing-credential error tells the user to install 1Password, which is the wrong guidance for their most likely mistake.

**This also settles the ccr question for this audience, in Patchbay's favour.** [patchbay.md](../patchbay.md) currently advises non-Servanda users to prefer ccr. That is wrong here: ccr is a proxy daemon, and telling a dev to install Node and run a background service *during an outage* is backwards. The no-daemon property is the actual advantage for outage fallback. Step 8 corrects the doc.

---

## Upcoming

Ordered by priority. The Terminal & editors thread has nothing queued;
new items for it go here with a **Thread:** tag like everything else.

### Inter-agent conversation audit log generator

**Thread:** AI Staff

**Goal:** From any Claude Code session, run a skill and get a self-contained HTML audit log page for a given session transcript, written to `~/.ai-staff-audit-log/`. Renders the opening prompt, the work log, the reply, derived side effects, and a real cost breakdown, with the work log hidden by default and a raw/preview toggle on markdown-bearing tool results.

**Plan:** [audit-log-generator.md](audit-log-generator.md)

**Status:** Built on `feature/audit-log` (worktree `../dotfiles-audit-log`), 2026-08-15. **Awaiting Scott's testing and review; deliberately not merged.** Fifteen steps, four phase gates, 249 tests. Grew out of a one-off HTML log built by hand for a single Donna to Greenthumb exchange, which worked well enough to deserve being a real tool.

**The skill is `audit-agent-conversation`, not `audit-log`** (decision A10). The `audit-` prefix reserves a namespace for the other kinds of audit skill that will follow; nothing in the name binds to Claude, to `claude -p`, to SendMessage, or to any single harness, model, or transport.

**Why it is not a Tools item:** it is the first thing in this repo that is *about* the agent fleet rather than part of it, which is what opened the AI Staff thread. It is also a skill plus a Python CLI, so it straddles `.claude/` and `bin/` and would sit awkwardly in either existing thread.

**The finding that shaped the whole design:** Claude Code writes one transcript record per content block, and every record repeats the entire message's `usage` object. Summing per record overcounted the reference session's output tokens by 2.5x. Deduplicating on `message.id` is load-bearing, and the golden test exists to keep it that way.

**v1 is deliberately small.** Single-turn SDK sessions only, which is exactly what every Donna-to-agent brief is; 15 of the 28 surveyed sessions qualify. Multi-turn rendering, image blocks, and the 44 MB scale case are all deferred; v1 detects them and refuses cleanly with a non-zero exit rather than emitting a half-correct page.

### Audit log generator follow-ons

**Thread:** AI Staff

**Goal:** Everything v1 deliberately refuses or leaves out.

**Status:** Queued behind the item above; v1 is useful without any of them.

Ordered for value, not for size: cheap changes that improve **inspecting
agent-to-agent conversations** come first, then work that makes more sessions
renderable at all, then anything needing a decision before it can be built, then
research. Each tier is meant to be finishable without leaving half-built work
behind.

#### Do first: cheap, low risk, immediate inspection value

1. **Provider and model in the stats strip.** Show what actually served the
   conversation, not just the model: `OpenRouter / gpt-5.6-sol`,
   `Ollama / glm-4.7-flash`, `Anthropic / claude-fable-5`. Today the page names
   the model and leaves you to infer the rest.

   **Measured 2026-08-16: transcripts record no provider, base URL, or
   endpoint at all.** Checked every top-level record field on real routed
   sessions; there is nothing to read. Provider has to be inferred from the
   model id, which the pricing table already does to decide what is unpriced,
   so this is mostly wiring plus a stats tile. Consequence worth accepting up
   front: **which Ollama host is not recoverable.** localhost versus an IP
   versus a hosted endpoint is not in the file, so it would need either a
   config map or a change to what Claude Code records. Show the provider now
   and leave the host for later rather than guessing it.

2. **Work log as an aligned table, with per-step duration.** Make the log read
   as columns rather than a stack: the `+` becomes a rotating arrow, then
   timestamp, then a badge, then the label and its sub-label, with duration
   right-aligned at the end. Narration rows (the italic blockquote ones) get a
   badge of their own so every row has one and the columns actually line up.

   **Durations are free.** A tool call's wall clock is the gap between the
   record emitting the `tool_use` and the record carrying its `tool_result`;
   measured on a real brief, that yields 0.00s to 0.66s per call. No new
   parsing, no ambiguity. Pure presentation plus arithmetic, so it is cheap to
   build and cheap to verify.

3. **An index page across `~/.ai-staff-audit-log/`.** One page listing what has
   been generated, newest first, with participants, date, duration, and cost.
   Worth having as soon as there are more than a handful, and it needs nothing
   the renderer does not already produce.

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

#### Needs a decision before it can be built

8. **Cost as a share of the subscription, alongside list price.** These
   sessions run on a Claude subscription, so the current figure is what the
   traffic *would* cost through the public API. The more useful number is what
   share of the month it actually consumed: if a plan costs $200 and covers N
   tokens, a conversation using 10% of N cost $20 of the bill. Show both: the
   subscription share and the pay-as-you-go price side by side. In API mode
   there is no share to show, so the page stays as it is today.

   **The open question is N.** Anthropic publishes no monthly token allotment
   for a subscription; usage is rate-limited by rolling windows, not a monthly
   quota. So the divisor has to come from somewhere: a figure Scott sets in
   config, a measured personal average, or a modelled cap. Until that is
   settled the arithmetic is fiction. Worth doing, worth not guessing.

9. **Real pricing for OpenRouter and other providers.** Extend the rate table
   past Anthropic so routed sessions cost out properly instead of rendering
   with the figures suppressed. OpenRouter publishes per-model pricing and
   returns generation cost, though the transcript captures only token counts,
   so this likely means a second rate table rather than live data. Ollama and
   other local runtimes stay genuinely unpriced, which the page already handles.

10. **A retention policy** for the output directory, which nothing currently
    prunes. Cheap to build; the decision is what to keep and for how long.

11. **The `--annotate` pass.** Optional model-assisted enrichment: tool-call
    one-liners for tools the regex table does not know, side-effect prose, and
    participant names where nothing records them. Quarantined to a sidecar JSON
    file so rebuilds stay instant, free, and byte-reproducible. Deliberately
    never in the render path.

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

**Status:** Unblocked as of 2026-07-30. Both prerequisites landed: the suite baseline and the review fixes.

Deliberately opportunistic. Tier 0 is about five minutes and needs no project; run it first. Tiers 1 through 3 need one real small feature in a low-stakes repo. Tier 4 needs a genuine phase boundary with a `PHASE GATE:` marker. Per the plan's own philosophy: no throwaway sandbox, test each behavior the next time real hobby-grade work offers the opportunity.

**The route-launcher plan above IS that opportunity.** It is a real, low-stakes, ten-step feature in this repo with a normal plan file, which is exactly what Tiers 1 through 3 need. Running it through `/booyah` or `/yolo` acceptance-tests the kit and ships the feature in one pass, which is why it now sits ahead of this item rather than behind it. Tier 4 still needs a genuine phase boundary and is unaffected.

**Ordering decision (2026-07-29):** test BEFORE the rename, even though the rename touches every command the checklist names. The rename is a mechanical layer on top; verifying behavior first is cheaper than verifying a spec that is about to be renamed. Accept that a name sweep of the checklist follows the rename.

**Worth doing early, while testing:** confirm `ANTHROPIC_DEFAULT_FABLE_MODEL` is actually honored, not merely present in the CLI binary. `strings` proved the name exists; nothing has proved the behavior. Gates are the wrong place to discover that assumption was wrong. Note the route-launcher plan's Gate A now covers this directly.

### Command Suite Rename (verb-scope grammar + /implement-phase)

**Thread:** Servanda

**Goal:** Rename /gameplan, /booyah, /yolo, /beastmode to /plan-feature, /implement-step, /implement-feature, /implement-roadmap; add net-new /implement-phase; record the hierarchy, delegation-decision rule, and trust-substitution ladder in COMMANDS.md.

**Plan:** [command-suite-rename.md](command-suite-rename.md)

**Status:** Ready to implement. AWAITING SCOTT'S EXPLICIT GO. Do not auto-start. Blocked on the batch landing above (the plan header's pre-step); acceptance testing should also come first per the ordering decision above.

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

**Status:** Incubating. The lifecycle is being hand-executed first in
`~/src/facetdigital/timercue` (the TimerCue app, formerly harvest-activity-guard) (doc structure landed 2026-08-01; skill
notes accumulate in that repo's `docs/notes/skill-lab.md`). Draft skills will be
built and tested in that repo's `.claude/` against the real build of Harvest Activity
Guard, then extracted and elevated into Servanda after real-world use. No dotfiles
work yet; do not start here until the incubation run produces stable skill drafts.
Decision context: spec-kit, superpowers, and SDD-style frameworks were evaluated
2026-08-01 and rejected wholesale; steal patterns only (constitution, clarify
discipline, spec-per-feature granularity stays with /gameplan).

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

### Route launcher follow-ons

**Thread:** Shell + Tools

**Goal:** The deferred pieces of [claude-route-launchers.md](claude-route-launchers.md), none of which blocked shipping it.

**Status:** Queued 2026-08-01, none urgent. The launchers work; these make them easier to set up and keep current. **The doctor script moved out of this item on 2026-08-08** and into [patchbay-team-release.md](patchbay-team-release.md) Step 6, where per-dev keys make it load-bearing rather than a nicety.

- **More OpenRouter models** (`kimi`, `deepseek`, `qwen`), plus a decision on the `glm` alias collision, since GLM exists on both backends and the alias currently resolves to Ollama. **Verify ZDR availability for each first:** Zero Data Retention is on for the account and filters the reachable catalog, so a model in OpenRouter's public list is not necessarily in this one's. Lower value than it looks: Gate B Check 5 showed gateway discovery already reaches the whole filtered catalog in-session, making these a convenience rather than the way to access a model.
- **A periodic model-slug refresh.** OpenRouter's catalog churns and several 2025-era slugs already carry expiration dates.
- **Bake `num_ctx` into `Modelfile.glm-4.7-flash`.** Fixes both the `num_ctz` typo and the `FROM` line (raw blob path to `glm-4.7-flash:latest`, since blob builds fail in `llama-quantize` on Ollama 0.30.7). Today the 198K window comes from `OLLAMA_CONTEXT_LENGTH` in the server's environment, which is silent when absent; a baked-in parameter survives any start method. Demoted from a Gate A blocker on 2026-07-30 once `/api/ps` showed the effective window was already correct.

### Patchbay v2: the `pbay` front door

**Thread:** Tools

**Goal:** Replace the wrapper-per-combination shape with a single subcommand CLI over the harness x model x provider matrix: `pbay run claude glm`, `pbay ps`, `pbay doctor`, `pbay models --refresh`, `pbay config`, `pbay providers`. State in `~/.pbay/`, cache kept separable from config. Absorbs three items that would otherwise be built separately: the doctor script, the model-slug refresh, and the harness expansion. Includes the `ollama-tools` scope reduction (delete `claude-install`, demote its README's harness support to a mention) and `aider-run` migrating into `bin/`.

**Status:** BLOCKED, deliberately. Design captured in [patchbay.md](../patchbay.md); do not build yet.

**The trigger:** the first time you want aider or codex against a routed backend for real work. That is when the matrix becomes real. Today there is one harness, two backends, four launchers, and nothing chafing, so building the general form would be inventing requirements.

**An honest complication found on 2026-08-02**, which supersedes the earlier framing of this item as "extend the launcher pattern to other harnesses": **claude-code-router already supports Claude Code, Codex, Grok CLI, Kimi CLI, Kilo Code, OpenCode, Pi, and ZCode.** The multi-harness capability this item was going to build is not a gap in the market; it is a gap only in this repo. So the trigger event for v2 is also the moment ccr becomes the obvious answer instead.

That makes the real question upstream of the build: **is the durable idea worth a competing tool at all?** ccr's ordered-fallback feature ("tries each backup model in order, returns on first success") is structurally the anti-pattern Servanda's capability floor exists to prevent, and no routing tool surveyed has any concept of refusing to substitute downward. A per-route `no_fallback: true` flag contributed upstream would be a small feature in ccr's existing config shape and would make the differentiator disappear in the best way. Not attempted, no issue filed, and the idea has been checked only against ccr's documentation rather than its code. See patchbay.md for the four options and their rough effort.

### Local model evaluation pass

**Thread:** Tools

**Goal:** Work out which local models are genuinely usable for agentic coding, rather than assuming.

**Status:** Queued. Live candidates are `glm-4.7-flash`, `qwen3.5-27b`, and a possible `qwen3.6:27b` pull. `gemma4` has an open tool-parser issue and `qwen3-coder` has the worst Claude-Code-specific bug reports, so both start behind.

One measurement already exists and should shape the rest: Gate A found `glm-4.7-flash` cold-starts in minutes, dominated by fixed cost rather than prompt size, against OpenRouter's roughly four seconds. Any evaluation that only scores output quality will miss the property that actually decides whether a local model gets used.

### Extract kit to its own repo (someday)

**Thread:** Servanda (and the thread's exit condition: this item ends Servanda as a dotfiles thread)

**Goal:** Move `.claude/` kit files and `docs/plans/` kit plans out of dotfiles into a standalone `servanda` repo, with install/symlink story, README (lead with the accountability loop; ladder as the teaching diagram; re-invocation grammar as the mechanism; "pacta sunt servanda" epigraph; motto candidate: "ships what it promised, proves what it shipped"), and license decision.

**Status:** Someday; explicitly not now

**Related decision (2026-07-29): no `~/.servanda` dotdir.** Servanda *is* Claude Code commands, so a separate home directory would have to be symlinked back into `~/.claude/commands/` to function, buying indirection and nothing else. The split that actually pays is runtime-vs-dev-artifact: runtime specs in their dotfile locations, dev artifacts in `docs/` (recorded in [land-baseline-commits.md](land-baseline-commits.md) Step 2). Extracting to this repo is the only thing that justifies a new home. Checked 2026-07-29: no `servanda` or `servando` repo exists locally under `~/src/scottwb` or `~/src/facetdigital`, nor in either GitHub org, so the name is unclaimed but also has no code behind it yet.

---

## Completed

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

### Claude Code route launchers (OpenRouter + Ollama) (2026-08-01)

**Thread:** Shell + Tools

**Plan:** [claude-route-launchers.md](claude-route-launchers.md)

Ten steps, three of them gates, all passed. `bin/claude-run` owns the provider and model tables; `claude-glm`, `claude-ollama`, `claude-gpt`, and `claude-openrouter` are thin wrappers over it. Routing is per process, so a routed session and a plain Max session run side by side and `settings.json` never needs editing to switch. `bin/what-claude` reports each session's backend in a ROUTE column read from process ancestry, and `bin/claude-route-selftest` holds the family to 105 assertions without launching a session or spending a token.

**The gates cost $0.48** and were worth more than that. What they settled:

- **Per-process routing leaves the Max login untouched**, which is what kept the design per-process instead of a global mode flip.
- **D12 is confirmed by observed behavior, not assumed.** An unmapped audit tier resolves to the literal `claude-fable-5`, which routed backends reject with exit 1 rather than falling through to the Opus or Sonnet mapping. That was the dangerous case: a phase gate quietly auditing on a local 30b while reporting success.
- **MCP tool calling works on both backends**, measured with the same probe against the same independently verifiable value rather than trusting either model's prose.
- **Ollama needs MCP trimming, OpenRouter does not**, which made the allowlist Ollama-specific and the workhorse simpler than Gate 0 feared.
- **The backends differ sharply**: ~220s vs ~4s to first token, 202752 vs 1M context, free vs ~$0.06-0.10/turn. Neither dominates, which is why both exist.

It also closed two things the Servanda thread was carrying: the `x-ANTHROPIC_DEFAULT_FABLE_MODEL-DECIDE-ME` marker from [servanda-review-fixes.md](servanda-review-fixes.md) step 2 is answered (routed profiles leave the audit tier unmapped on purpose, and gates therefore halt under routing), and `ANTHROPIC_DEFAULT_FABLE_MODEL` is proven honored rather than merely present in the binary.

Full records in [mcp-schema-budget.md](../assessments/mcp-schema-budget.md) and [route-gates.md](../assessments/route-gates.md). Follow-ons are queued in Upcoming under "Route launcher follow-ons".

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

- **Pacta Sunt Servanda brown bag (rescheduled to 2026-07-31, noon Pacific):** the kit's public debut (concepts + the Servanda name; kit itself not shared). Materials and tasks: `facet-revops/demand-gen/talks/20260731-pacta-sunt-servanda/` and `demand-gen/WORK-PLAN.md`. Sponsor call transcripts may reorder/pivot talk concepts; that work happens entirely in the facet workspace, not here.
- **Clay alert sweep (recurring):** `/facet-clay-sweep` command lives in `facet-admin-workspace/.claude/commands/`. Triage state: `facet-revops/prospecting/clay-triage-log.md` (global log). Relevant to this kit only as another example of encoding process as executable policy.
