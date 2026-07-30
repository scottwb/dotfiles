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

### Review and baseline the Servanda suite overhaul

**Thread:** Servanda

**Goal:** Review the 2026-07-05 command-kit overhaul (~1,400 lines across ten files, still uncommitted), then land it as seven commits. Scott explicitly wants to review the current state, and likely work on these files further, before they get baselined.

**Plan:** [servanda-suite-baseline.md](servanda-suite-baseline.md)

**Status:** STILL HELD on Scott's read-through of the files. **Do not commit.**

Two gates, do not confuse them:

- **Design questions: CLEARED 2026-07-29.** All five settled with reasoning, rejected alternatives, and consequences recorded in the plan's "Review first" section. Q1 keep the 4-state /yolo, Q2 keep the model pins (they are already provider-agnostic tier aliases) with STOP-not-degrade, Q3 keep all four safety caps, Q4 fix booyah to ask on first invocation only, Q5 baseline separately rather than folding into the rename.
- **Scott's read-through of the ten files: STILL OPEN.** Answering the design questions did not clear this. The decisions say what shape the suite should have; they do not certify the working tree implements that shape.

**Sequence decided in Q5:** baseline the suite, then [the review fixes](servanda-review-fixes.md), then acceptance testing, then the rename. Rationale: 1,400 lines currently exist only in the working tree, so getting them into git beats a cleaner history. Accepted cost: four files get touched in three passes.

This is the pre-step [command-suite-rename.md](command-suite-rename.md) requires.

---

## Upcoming

Ordered by priority. The Tools and Terminal & editors threads have nothing queued;
new items for them go here with a **Thread:** tag like everything else.

### Apply the Servanda review fixes

**Thread:** Servanda

**Goal:** The concrete work that fell out of the 2026-07-29 review: document that model pins are tier aliases rather than vendor lock-in, map (or deliberately refuse) the audit tier in the parked Ollama profile, add a provider preflight guard, and stop `/booyah` and `/yolo` from assuming a pre-existing dirty tree is their own work.

**Plan:** [servanda-review-fixes.md](servanda-review-fixes.md)

**Status:** Blocked on the suite baseline landing first. Four steps, four commits, all small.

Deliberately sequenced BEFORE acceptance testing so testing does not exercise code already known to be wrong. Step 4 is the fix for a real failure hit on 2026-07-29, not an inspection finding: `/booyah` could not be used to land the baseline commits because it would have swept the held suite into one commit.

### Decide the Claude Code session model pin

**Thread:** Servanda (settings, not commands)

**Goal:** Settle whether `.claude/settings.json` should keep its pinned `"model": "claude-fable-5[1m]"` or run unpinned. The working tree currently has the pin REMOVED along with three cosmetic prefs (`cleanupPeriodDays: 90`, `theme: dark`, `agentPushNotifEnabled: false`), all uncommitted and held on purpose.

**Status:** Held, no plan needed. This is a one-file decision, not a feature.

Context for the decision: the kit does not depend on the session model, since it spawns subagents with explicit `model: "fable"` and `model: "opus"` overrides, so unpinning does not weaken the Fable-tier gate rules. The question is purely what you want driving interactive sessions by default. Worth deciding alongside the suite review, since the model pins are one of that review's open questions.

If the answer is "unpin," this can land as one commit (`Settings: unpin the model, extend cleanup retention to 90 days, record UI prefs`), or two if you want the behavior change findable separately from the cosmetics.

### Acceptance-test the Servanda kit

**Thread:** Servanda

**Goal:** Walk Tiers 0 through 4 of the kit's manual test plan against the now-committed batch. The 2026-07-05 overhaul (gameplan rename, /yolo state machine, Opus-pinned review, Fable phase gates, /phasegate) is code-complete with **zero** acceptance testing so far.

**Plan:** [command-kit-overhaul.md](command-kit-overhaul.md)

**Status:** Blocked on the suite baseline AND [the review fixes](servanda-review-fixes.md) landing first (nothing to test against until the suite is committed, and no point exercising code the review already flagged as wrong). Then deliberately opportunistic. Tier 0 is ~5 minutes and needs no project; run it as soon as the fixes land. Tiers 1 through 3 need one real small feature in a low-stakes repo; Tier 4 needs a genuine phase boundary with a `PHASE GATE:` marker. Per the plan's own philosophy: no throwaway sandbox, test each behavior the next time real hobby-grade work offers the opportunity.

**Ordering decision (2026-07-29):** test BEFORE the rename below, even though the rename touches every command the checklist names. The rename is a mechanical layer on top; verifying behavior first and then renaming is cheaper than verifying a spec that is about to be renamed. Accept that a name sweep of the checklist follows the rename.

### Command Suite Rename (verb-scope grammar + /implement-phase)

**Thread:** Servanda

**Goal:** Rename /gameplan, /booyah, /yolo, /beastmode to /plan-feature, /implement-step, /implement-feature, /implement-roadmap; add net-new /implement-phase; record the hierarchy, delegation-decision rule, and trust-substitution ladder in COMMANDS.md.

**Plan:** [command-suite-rename.md](command-suite-rename.md)

**Status:** Ready to implement. AWAITING SCOTT'S EXPLICIT GO. Do not auto-start. Blocked on the batch landing above (the plan header's pre-step); acceptance testing should also come first per the ordering decision above.

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

### Extract kit to its own repo (someday)

**Thread:** Servanda (and the thread's exit condition: this item ends Servanda as a dotfiles thread)

**Goal:** Move `.claude/` kit files and `docs/plans/` kit plans out of dotfiles into a standalone `servanda` repo, with install/symlink story, README (lead with the accountability loop; ladder as the teaching diagram; re-invocation grammar as the mechanism; "pacta sunt servanda" epigraph; motto candidate: "ships what it promised, proves what it shipped"), and license decision.

**Status:** Someday; explicitly not now

**Related decision (2026-07-29): no `~/.servanda` dotdir.** Servanda *is* Claude Code commands, so a separate home directory would have to be symlinked back into `~/.claude/commands/` to function, buying indirection and nothing else. The split that actually pays is runtime-vs-dev-artifact: runtime specs in their dotfile locations, dev artifacts in `docs/` (recorded in [land-baseline-commits.md](land-baseline-commits.md) Step 2). Extracting to this repo is the only thing that justifies a new home. Checked 2026-07-29: no `servanda` or `servando` repo exists locally under `~/src/scottwb` or `~/src/facetdigital`, nor in either GitHub org, so the name is unclaimed but also has no code behind it yet.

---

## Completed

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
