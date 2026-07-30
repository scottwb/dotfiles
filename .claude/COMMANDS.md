# Workflow Command Suite

Canonical reference for the development workflow commands in `~/.claude/commands/`. This file is NOT auto-loaded into agent context; it is read on demand (by humans directly, or by agents via `/workflow-help`). Each command's own file is the executable spec; this document is the contract summary: what each does, what it deliberately does NOT do, and how they compose.

## The Autonomy Ladder

Approval granularity coarsens as autonomy increases. One consistent grammar throughout: re-invocation (or a roadmap marker) is the approval signal.

| Command | Granularity | Approval signal | Branch behavior | Gate behavior |
|---|---|---|---|---|
| /roadmap | none (viewer) | n/a | none | shows PHASE GATE items as [Phase Gate] |
| /gameplan | none (planning) | user iterates until "good" | none | plans are TDD-shaped and citation-tagged |
| /booyah | step | re-run = approve last step + commit + do next | none: works on whatever branch you are on (you chose it) | offers the gate when a completed plan ends a phase |
| /yolo | feature | re-run on completed clean branch = approve + merge + wrap up | own `feature/<plan>` branch; never main | auto-runs the gate at wrap-up when a PHASE GATE is next |
| /beastmode | phase | one preflight confirmation, then continuous | branch per feature (one feature = one branch = one PR) | auto-runs the gate at PHASE GATE markers; findings = STOP |
| /phasegate | phase audit | invoked by you or spawned by the above | none (audits merged main) | is the gate |

## Shared Conventions

- **Roadmap file:** `docs/plans/development-roadmap.md` per repo; sections: Next Immediate Step, Upcoming, Completed. Plans live beside it in `docs/plans/`.
- **PHASE GATE markers:** a roadmap item titled `PHASE GATE: <phase name>` marks a phase boundary. It is not a feature; it is processed by /phasegate.
- **Merge policy:** preserve full history (`--no-ff` / `--merge`); never squash, never rebase, unless the repo explicitly overrides.
- **Commits:** descriptive messages, no Claude attribution or co-author trailers.
- **TDD:** plans are test-first (failing conformance/e2e scenario or unit test before implementation); bug fixes always get a failing-then-passing test that is never modified afterward.
- **Debugging:** systematic, never shotgun: reproduce, hypothesize, gather evidence, fix the root cause. Capped attempts, then STOP; autonomous modes never build on a broken foundation.
- **Verification tiers:** Tier 1 deterministic (tests, conformance, CI) decides everything decidable; Tier 2 per-PR review runs on Opus (pinned); Tier 3 phase gates run on Fable, or not at all (never silently degraded).
- **Model pins are TIER ALIASES, not vendors.** The `model:` values at spawn sites (`"opus"`, `"fable"`) are Claude Code tier aliases. Each resolves through the corresponding `ANTHROPIC_DEFAULT_<TIER>_MODEL` environment variable, so the vendor mapping lives in `env` in `settings.json` and nowhere else. Switching to OpenRouter, Ollama, or any other provider therefore requires changing only that `env` block: point `ANTHROPIC_DEFAULT_FABLE_MODEL` and `ANTHROPIC_DEFAULT_OPUS_MODEL` at whatever serves those roles, and every command file keeps working untouched. **Do not add per-provider fallback logic to the command files.** The indirection already exists one layer down; duplicating it there would be a regression, not a feature. What the pins do assert is a capability floor: an audit spawned at the Fable tier must actually be the strongest model available, whoever makes it.

## Command Contracts

### /roadmap
- **Does:** finds or creates the repo roadmap, displays status with [Plan Ready]/[Needs Planning]/[Phase Gate] indicators, routes you to /gameplan or /booyah.
- **Does not:** implement anything, commit anything (except initial roadmap creation), touch branches.

### /gameplan (formerly /plan)
- **Does:** researches the codebase and specs, asks clarifying questions, writes a step-by-step plan to `docs/plans/<feature>.md` where every step is the smallest committable change, starts with a failing test, and carries a **Satisfies:** citation (PRD section, decision number, scenario ID). Iterates with you, then commits the plan.
- **Does not:** implement anything. `/plan` still works as a deprecated alias.

### /booyah
- **Does:** step-at-a-time execution with you as the tester between steps. Re-running it commits the previous (now tested) step without asking, implements the next step, updates docs, and stops with testing instructions. At plan completion: updates the roadmap and, if a PHASE GATE is next, asks whether to run the gate (spawned at Fable tier).
- **Does not:** touch branches (it commits on the branch you are on, main included: you chose the branch before starting), run multiple steps unattended, or auto-fire the gate.

### /yolo
- **Does:** implements an entire plan unattended on its own feature branch with per-step commits, then stops with a consolidated manual-testing checklist. Re-invocation is a state machine: resume (unchecked steps remain), fix-round commit (complete + dirty tree: commits your requested fixes, re-lists what to re-test), or wrap-up (complete + clean tree: merges with full history, local or PR-mode with CI wait, deletes the branch, updates the roadmap, and auto-runs the phase gate if one is next). `/yolo done` forces the wrap-up reading.
- **Does not:** merge without your re-invocation, work on main, continue past unresolvable failures (it STOPs), touch prod data in prod-affecting integrations, or run the gate below Fable tier.

### /beastmode
- **Does:** the full outer loop, unattended after one confirmation: per roadmap item, a yolo-style implementation pass on its own branch, PR (or local mode), an independent fresh-context review subagent pinned to Opus with structured verdicts, fix-and-re-review until clean (5-pass cap), a Fable security pass when the change touches the security surface, CI-green-before-merge with flake handling and time caps, full-history merge, roadmap update, next item. At PHASE GATE markers it spawns the Fable gate audit: PASS = continue into the next phase; findings = STOP with the fix list. Cap breaches recommend escalation to a Fable session.
- **Does not:** ask per-item permission, bundle features into one PR, force-push, merge red CI, approve its own dirty reviews, run gates or security passes below Fable tier, or auto-fix architectural gate findings.

### /phasegate
- **Does:** the Tier 3 audit after a phase's features are merged: verifies the test suite tells the truth, walks every plan step's Satisfies citation against the actual code, hunts drift against the specs and architecture, runs the security-surface triage (full adversarial review when it hits), writes a verdict report to `docs/assessments/phasegate-<phase>.md`, commits it, and produces the fix list that seeds the next planning session.
- **Does not:** fix anything (audit only), run below Fable tier without warning you, or pass a red suite.

### /workflow-help
- **Does:** reads this file and answers "what does X do?" questions on demand, so the contracts never need to live in standing context.

## Typical Flows

- Interactive: `/roadmap` -> `/gameplan <feature>` -> `/booyah` (repeat per step) -> gate offer at phase end.
- Semi-autonomous: `/gameplan` -> `/yolo <feature>` -> test -> complain/fix rounds -> `/yolo` (wrap-up, merge, gate).
- Autonomous: plans ready for a whole phase -> `/beastmode` -> come back to merged features and either a passed gate or a fix list.
- The fix list from any gate goes back into `/gameplan` for the next phase's first plan.
