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

**Servanda** is Scott's workflow command kit for Claude Code (from "pacta sunt servanda": agreements must be kept; the kit is the enforcement half). Code lives in this repo at `.claude/` (commands in `.claude/commands/`, contracts in `.claude/COMMANDS.md`), symlinked from `~/.claude`. Plans live here in `docs/plans/`. The kit is internal (not shared, not a product); it may get its own repo someday. It is the dominant thread at the moment, so most items below are tagged Servanda; that is a snapshot of current attention, not the repo's permanent shape.

---

## Next Immediate Step

### Fix the install instructions' `rm -rf .git` hazard

**Thread:** Machine setup

**Goal:** Change the README's install step from `rm -rf .git` to `unlink .git`, and add a `ls -ld .git` look-before-you-delete line above it.

**Status:** Ready, about five minutes. Promoted 2026-08-01 on completing the route launchers. It sits ahead of the larger Servanda work not because it outranks it but because it is a latent data-loss hazard in the one document a new machine follows, and the fix is trivial.

**Why it matters.** The install symlinks every dot-entry from the repo into `$HOME`, `.git` included, so `~/.git` ends up pointing at the dotfiles repo and makes the whole home directory look like a checkout. The `rm -rf .git` that follows exists to undo exactly that one bad symlink. Verified empirically on 2026-08-01, each case against a fresh target:

| Command | The symlink | The real repo |
|---|---|---|
| `rm -rf .git` | removed | intact |
| **`rm -rf .git/`** | still there | **destroyed** |
| `rm .git` | removed | intact |
| `unlink .git` | removed | intact |

One trailing slash inverts the outcome: macOS resolves through the link, recursively deletes the target's contents, and leaves the dangling link behind. Separately, `rm -rf .git` run in the repo by mistake destroys it silently, while `unlink .git` and `rm .git` both refuse with "is a directory". `unlink` cannot recurse, cannot follow a symlink, and fails safe in both directions.

The instruction as written is correct. This is about removing the ways to get it wrong.

---

## Upcoming

Ordered by priority. The Terminal & editors thread has nothing queued;
new items for it go here with a **Thread:** tag like everything else.

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

**Status:** Queued 2026-08-01, none urgent. The launchers work; these make them easier to set up and keep current.

- **`bin/claude-route-doctor`**, a preflight checker for the setup the README currently describes in prose: `op` installed with shell integration on, the `op://` item resolving, a **per-key** OpenRouter credit limit set, Ollama up, the model installed, and the loaded window matching the route. Prints what is missing plus the fix. This is the answer to a real gap: nothing short of fresh hardware exercises the Homebrew and 1Password-toggle steps, so setup correctness is currently documentation you have to trust. The per-key check earns its place on its own, since an account-level limit leaves the key endpoint reporting `limit: null` and that mistake was made live during Gate B.
- **More OpenRouter models** (`kimi`, `deepseek`, `qwen`), plus a decision on the `glm` alias collision, since GLM exists on both backends and the alias currently resolves to Ollama. **Verify ZDR availability for each first:** Zero Data Retention is on for the account and filters the reachable catalog, so a model in OpenRouter's public list is not necessarily in this one's. Lower value than it looks: Gate B Check 5 showed gateway discovery already reaches the whole filtered catalog in-session, making these a convenience rather than the way to access a model.
- **A periodic model-slug refresh.** OpenRouter's catalog churns and several 2025-era slugs already carry expiration dates.
- **Bake `num_ctx` into `Modelfile.glm-4.7-flash`.** Fixes both the `num_ctz` typo and the `FROM` line (raw blob path to `glm-4.7-flash:latest`, since blob builds fail in `llama-quantize` on Ollama 0.30.7). Today the 198K window comes from `OLLAMA_CONTEXT_LENGTH` in the server's environment, which is silent when absent; a baked-in parameter survives any start method. Demoted from a Gate A blocker on 2026-07-30 once `/api/ps` showed the effective window was already correct.

### Extend the launcher pattern to the other harnesses

**Thread:** Tools

**Goal:** Launchers for aider, codex, opencode, and pi following the `claude-run` shape, with `aider-run` migrating out of `ollama-tools` into `bin/`. Includes the `ollama-tools` scope reduction: delete `claude-install` and demote its README's harness support to a mention.

**Status:** Queued. This is the payoff D8 was aiming at, and the reason the transport logic lives in one workhorse rather than being copy-pasted per model. Worth doing only when a second harness is actually in regular use; building it speculatively would be inventing requirements.

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
