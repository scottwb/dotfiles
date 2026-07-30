# Servanda Command Kit Overhaul: Manual Test Plan

Companion to `.claude/COMMANDS.md`. This is the acceptance checklist for the 2026-07-05 command-kit overhaul (gameplan rename, /yolo state machine, beastmode Opus pin + Fable phase gates, /phasegate, docs layer). Check items off as real usage covers them.

## Status

- Batch applied to `~/src/scottwb/dotfiles/.claude`: 2026-07-05
- Relocated here from `.claude/COMMANDS-TESTING.md`: 2026-07-29
- Batch committed: **YES, 2026-07-30**, via [servanda-suite-baseline.md](servanda-suite-baseline.md). Seven commits, `5ceaeca` through `08dbbb2`, on `feature/servanda-suite-baseline` and merged to master.
- Testing: **LIVE, nothing checked off yet.** Tier 0 first; it needs no project and takes about five minutes.

**This file is no longer a commit gate.** It originally held the batch hostage ("commit when everything is checked"), reversed deliberately on 2026-07-29: the batch gets committed first so the only copy is not the working tree, and testing runs against committed code where findings become fix commits on a known baseline. Rationale in [servanda-suite-baseline.md](servanda-suite-baseline.md) under "Decision: commit before acceptance testing."

Scott's content review of the suite cleared on 2026-07-30 ("I have read the diffs and approve of them all"), which is what unblocked the baseline.

**Run [servanda-review-fixes.md](servanda-review-fixes.md) before working through the tiers below.** Those four fixes address problems the review already found, so testing ahead of them would exercise code known to be wrong.

Philosophy: no throwaway sandbox. Test each behavior the next time real (hobby-grade) work gives you the opportunity. Low-stakes repos are the proving ground; smyk v1 implementation is the graduation exercise, not the test bed.

Note for whoever runs this after the [command suite rename](command-suite-rename.md): every command name below is the pre-rename name (/gameplan, /booyah, /yolo, /beastmode). The agreed ordering is to test BEFORE renaming, so if you are reading this post-rename, the checklist needs a name sweep first, and the reusable tier items should graduate to `docs/testing/servanda-manual-tests.md` while this file becomes the historical record.

---

## Tier 0: Anytime checks (no project needed, ~5 minutes)

- [ ] Type `/` in any session and read the autocomplete: `gameplan`, `plan` (says "Deprecated alias"), `booyah`, `yolo`, `beastmode`, `phasegate`, `workflow-help` all show their new contract-carrying descriptions
- [ ] `/workflow-help` bare: prints the autonomy ladder table and one-line contracts
- [ ] `/workflow-help does yolo merge?`: answers "only at wrap-up, on your re-invocation," from COMMANDS.md, not from vibes
- [ ] `/workflow-help what does booyah do with branches?`: answers "nothing; works on the branch you are on"

## Tier 1: Next time you plan any small feature (hobby project)

Use `/gameplan` (and once, deliberately, `/plan` to test the alias):

- [ ] `/plan <feature>` once: emits the one-time "(FYI: /plan is now /gameplan)" note, then behaves identically to /gameplan
- [ ] `/gameplan <feature>`: asks clarifying questions before writing
- [ ] Produced plan: every behavior-changing step starts with a "write the failing test first" sub-item
- [ ] Produced plan: every step has a **Satisfies:** line (or the step got questioned); docs/scaffolding steps say "test-first: n/a" explicitly
- [ ] Plan committed with `Add plan: <feature>` and roadmap updated to "Ready to implement"

## Tier 2: Next time you implement that small feature step-by-step

Use `/booyah`:

- [ ] Works on whatever branch you are on without branch ceremony (deliberately try it on main once for a docs-ish feature)
- [ ] Stops after each step with what-changed + how-to-test; does NOT commit before you re-run it
- [ ] Re-running `/booyah` commits the tested step without asking and advances to the next
- [ ] TDD order honored: test sub-item implemented before the code it tests
- [ ] At plan completion: roadmap updated, `Complete: <feature>` committed
- [ ] If the next roadmap item is a `PHASE GATE:` marker: it ASKS "run the gate now?" (does not auto-fire); on yes, spawns the gate via Agent tool with model fable and relays verdict + report path

## Tier 3: Next time you have a self-contained feature you trust (the /yolo lifecycle)

This is the biggest behavioral change; walk the whole state machine on one real feature:

- [ ] Fresh run: `/yolo <plan>` asks for confirmation ONCE, creates `feature/<plan>`, implements everything with per-step commits, ends with a checklist consolidated by command (not by step), and does NOT merge
- [ ] Resume: interrupt a run (Esc mid-implementation), re-run `/yolo`: announces resume state and continues from the first unchecked step
- [ ] Fix round: after your manual testing, report a real complaint in plain words; after the fix, `/yolo` commits it with a testing-feedback message and presents a DELTA checklist only
- [ ] Wrap-up: `/yolo` on the completed clean branch announces the wrap-up state, merges with full history (`--no-ff` local, or PR mode with CI wait if the repo has a remote + gh), deletes the branch, lands on main, updates and commits the roadmap
- [ ] Wrap-up + gate: if a `PHASE GATE:` marker is next, the gate runs automatically (watch for the Agent spawn with model fable), the report lands in `docs/assessments/` and is committed
- [ ] Post-wrap-up: one more `/yolo` treats it as a fresh run on the NEXT item, with the confirmation guard (accidental double-tap protection)
- [ ] `/yolo done` forces wrap-up interpretation (test once when convenient)

Safety rails (contrive these cheaply on the same repo, ~5 minutes):

- [ ] Dirty tree + `/yolo` fresh run: refuses and stops
- [ ] On plan-A's branch, `/yolo plan-B`: refuses the mismatch
- [ ] A step whose test genuinely fails: does systematic debugging (states a hypothesis, gathers evidence; no shotgun retry spam) and after the cap STOPs the run rather than continuing to later steps

## Tier 4: Next time a phase of work completes (gate + beastmode)

Prerequisite: put a `PHASE GATE: <name>` item in the hobby repo's roadmap at a genuine phase boundary.

/phasegate direct:

- [ ] In a Fable session: `/phasegate <name>` audits without fixing anything, writes `docs/assessments/phasegate-<slug>.md` with verdict + citation walk + security triage, commits it, marks the roadmap gate item complete on PASS
- [ ] Model check: run `/phasegate` in an OPUS session: it warns it is not Fable-tier and asks proceed-or-defer (the never-silently-degrade behavior)

/beastmode (local mode is sufficient to prove the new wiring; PR mode is already battle-tested from v0):

- [ ] Preflight: one confirmation, correct mode announcement
- [ ] Review subagent spawns with model: opus (watch the Agent call), regardless of session model
- [ ] Review prompt includes the coverage bar language
- [ ] A feature touching the security surface (or contrive one: touch anything auth/subprocess/file-permission flavored) triggers the 4c-2 Fable security pass after a clean Opus review
- [ ] At the PHASE GATE marker: auto-spawns the Fable gate; PASS = marks gate item complete and continues; findings = STOPs with the fix list
- [ ] Wrap-up report includes the new "Phase gates" and "Fable security passes" accounting

## Invariants to watch on every test above

- [ ] No Claude attribution or co-author trailers in any commit
- [ ] No emdashes in generated plans, reports, or PR bodies
- [ ] Merges preserve full history (no squash, no rebase) unless the repo overrides
- [ ] Announcements match the documented formats (green check only on genuine progress)

## Sign-off

The batch commits themselves are no longer part of sign-off; they happen up front
via [servanda-suite-baseline.md](servanda-suite-baseline.md). When all tiers are
checked:

1. Commit this file with the tiers checked off, message like: `Servanda acceptance testing complete: tiers 0-4 verified`
2. Any findings become their own fix commits on top of the batch, each with a failing-then-passing check where the TDD policy applies
3. Update the smykowski project memory (`command-kit-patch-plan.md`) to note the batch is committed and acceptance-tested
4. Mark "Acceptance-test the Servanda kit" complete in [development-roadmap.md](development-roadmap.md)
5. The suite is then cleared to drive smyk v1 implementation (`docs/05-DEV-ROADMAP.md` gets written with PHASE GATE markers)
