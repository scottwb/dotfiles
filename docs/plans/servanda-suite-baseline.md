# Plan: Review and Baseline the Servanda Suite Overhaul

**Status:** HELD. Do not start committing until Scott has reviewed the suite's
current state. He explicitly wants to review these files, and likely work on them
further, before they get baselined (2026-07-29).

This is the pre-step [command-suite-rename.md](command-suite-rename.md) requires,
and it gates [command-kit-overhaul.md](command-kit-overhaul.md) acceptance
testing.

## What is held

The 2026-07-05 command-kit overhaul, code-complete and never committed. All of it
is sitting uncommitted in the working tree; the only copy is the tree itself.

| File | State | Change |
|---|---|---|
| `.claude/commands/gameplan.md` | untracked, 132 lines | New: the planning flow, TDD-shaped with **Satisfies:** citations |
| `.claude/commands/plan.md` | modified, -124 | Reduced to a 7-line deprecated alias stub |
| `.claude/commands/yolo.md` | modified, +277/-162 | Rewritten as a 4-state re-invocation machine |
| `.claude/commands/phasegate.md` | untracked, 100 lines | New: Fable-tier phase audit |
| `.claude/commands/booyah.md` | modified, +3 | Phase-gate awareness at plan completion |
| `.claude/commands/roadmap.md` | modified, +5 | `[Phase Gate]` display, `/gameplan` routing |
| `.claude/commands/beastmode.md` | modified, +51 | Opus-pinned review, Fable gates, security pass, root-cause CI fixes |
| `.claude/COMMANDS.md` | untracked, 62 lines | New: autonomy ladder, contracts, conventions |
| `.claude/commands/workflow-help.md` | untracked, 9 lines | New: answers from COMMANDS.md on demand |
| `.claude/CLAUDE.md` | modified, workflow-table change only | Workflow table gains the new commands |

Roughly 1,400 lines across ten files. Zero acceptance testing so far.

## Review first (the actual gate)

Before any commit below, review the current state. Open questions worth deciding
during the review, all of which are cheaper to change before baselining than
after:

- **Is the `/yolo` 4-state machine the right shape?** It is the largest behavior
  change in the batch. States are keyed off observable git and plan state (fresh
  run, resume, fix round, wrap-up), with re-invocation as the approval signal.
- **Are the model pins right?** Review subagents pinned to Opus, phase gates and
  security passes pinned to Fable with STOP-rather-than-degrade. These interact
  with the held `settings.json` model-unpin decision.
- **Are the safety caps right?** 5 review passes, 5 CI fix attempts, 8 combined,
  4-hour wall clock per PR.
- **`/booyah` Step 4's `git add -A` is a footgun** (found 2026-07-29 while trying
  to use `/booyah` to land the baseline commits). Step 2 treats any dirty tree as
  "my previous step's work needs committing," then Step 4 stages with `git add -A`.
  Any pre-existing unrelated dirty work therefore gets swept into a step commit
  with a message describing something else. This is not hypothetical: it is why
  [land-baseline-commits.md](land-baseline-commits.md) has to be run manually.
  Candidate fix: stage only the paths in the step's declared **File(s)** line, and
  refuse to proceed (or ask) when the tree contains modifications outside them.
  Note `/yolo` shares the shape of this assumption in its state 3 (fix round),
  which also commits a dirty tree it did not necessarily create; check whether the
  same fix applies there.
- **Does the rename land on top cleanly,** or should some of this be folded into
  the rename rather than committed twice? The rename plan renames every command
  here. If a file needs substantive rework anyway, doing it as part of the rename
  may be cheaper than baseline-then-rename.

That last question is the one that could restructure this whole plan. Settle it
during the review.

## Execution Instructions (after the review clears)

1. **Work step-by-step** - one commit per step, in order
2. **Test-first within each step** - n/a (these are command spec files, pure
   docs); each Test block is a manual smoke check
3. **Commit after each step** - use the provided commit message verbatim
4. **Mark completion** - check off steps as they land

Prerequisite: [land-baseline-commits.md](land-baseline-commits.md) is done, so the
tree contains only held items and each commit below is clean.

## Decision: commit before acceptance testing (2026-07-29)

[command-kit-overhaul.md](command-kit-overhaul.md) originally held itself as a
gate: "batch committed: NOT YET (intentionally; this file is the gate)." That is
reversed deliberately. Reasons:

- The batch is ~1,400 lines whose only copy is the working tree. A reboot or a
  stray `git checkout` loses it.
- Acceptance testing is opportunistic by its own design ("test each behavior the
  next time real work gives you the opportunity"), so the gate could stay closed
  for weeks.
- Testing against committed code is strictly better: findings become fix commits
  on top of a known baseline, and anything that goes wrong is revertable.

Note this does NOT conflict with the review gate above. Scott's review is a human
gate on *content*; the old gate was on *acceptance testing*. Review, then commit,
then test.

---

## Step 1: Rename /plan to /gameplan, keep /plan as a deprecated alias

- [ ] Test-first: n/a (command specs)
- [ ] `commands/gameplan.md` (new) carries the planning flow, now TDD-shaped with
      **Satisfies:** citations
- [ ] `commands/plan.md` reduced to a 7-line alias stub that emits a one-time FYI
      then defers

Motivation: `/plan` collided with Claude Code's built-in plan mode.

**File(s):** `.claude/commands/gameplan.md`, `.claude/commands/plan.md`

**Test:**
```bash
head -2 .claude/commands/gameplan.md .claude/commands/plan.md
# New session: /gameplan and /plan both appear, /plan says "Deprecated alias"
```

**Commit message:** `Rename /plan to /gameplan; keep /plan as a deprecated alias`

---

## Step 2: Rewrite /yolo as a re-invocation state machine

- [ ] Test-first: n/a (command specs)
- [ ] Four states keyed off observable git and plan state (fresh run, resume, fix
      round, wrap-up), `/yolo done` to force wrap-up, merge and roadmap update
      and phase gate at wrap-up
- [ ] Safety rules generalized: prod-affecting integrations rather than Harvest
      specifically; STOP on unresolvable failures instead of noting and
      continuing

The largest single behavior change in the batch (+277/-162). The key idea: the
user re-invoking `/yolo` on a complete clean branch IS the approval signal, the
same grammar `/booyah` already used per step.

**File(s):** `.claude/commands/yolo.md`

**Test:**
```bash
grep -n "Step 0: Detect State" .claude/commands/yolo.md
grep -c "State [1-4]" .claude/commands/yolo.md
```

**Commit message:** `Rewrite /yolo as a re-invocation state machine with wrap-up and merge`

---

## Step 3: Add /phasegate

- [ ] Test-first: n/a (command specs)
- [ ] `commands/phasegate.md` (new): Fable-tier audit of a completed phase, walks
      every plan step's **Satisfies:** citation against real code,
      security-surface triage, verdict plus fix list to
      `docs/assessments/phasegate-<slug>.md`, audit only, never fixes code

**File(s):** `.claude/commands/phasegate.md`

**Test:**
```bash
head -2 .claude/commands/phasegate.md
grep -n "docs/assessments" .claude/commands/phasegate.md
```

**Commit message:** `Add /phasegate: Fable-tier phase audit with verdict and fix list`

---

## Step 4: Teach /booyah and /roadmap about PHASE GATE markers

- [ ] Test-first: n/a (command specs)
- [ ] `/booyah` step 5 asks (never auto-fires) when a completed plan promotes a
      `PHASE GATE:` marker, spawning the gate at Fable tier
- [ ] `/roadmap` shows gate items as `[Phase Gate]` with no planning indicator,
      and routes to `/gameplan`

**File(s):** `.claude/commands/booyah.md`, `.claude/commands/roadmap.md`

**Test:**
```bash
grep -n "PHASE GATE" .claude/commands/booyah.md .claude/commands/roadmap.md
```

**Commit message:** `Teach /booyah and /roadmap about PHASE GATE markers`

---

## Step 5: Harden /beastmode

- [ ] Test-first: n/a (command specs)
- [ ] Review subagents pinned to `model: "opus"` so review quality does not float
      with the session model
- [ ] Automatic Fable phase gates at `PHASE GATE:` markers (step 1b), with safety
      rule 10: Fable tier or STOP, never a lesser model, never skip an unrun gate
- [ ] Step 4c-2 Fable security pass when the branch touches the security surface
- [ ] Root-cause-before-fixing rule for CI failures (no shotgun "see if CI likes
      this one"), coverage-bar language in the review prompt, cap breaches
      recommend escalating to a Fable session, wrap-up report accounts for gates
      and security passes

**File(s):** `.claude/commands/beastmode.md`

**Test:**
```bash
grep -n 'model: "opus"\|model: "fable"' .claude/commands/beastmode.md
grep -n "Step 1b\|4c-2" .claude/commands/beastmode.md
```

**Commit message:** `Harden /beastmode: Opus-pinned review, Fable gates and security pass, root-cause CI fixes`

---

## Step 6: Add COMMANDS.md contract reference and /workflow-help

- [ ] Test-first: n/a (docs)
- [ ] `.claude/COMMANDS.md` (new): the autonomy ladder table, shared conventions,
      per-command "does / does not" contracts, typical flows
- [ ] `commands/workflow-help.md` answers questions from it on demand, so
      contracts never sit in standing context

**File(s):** `.claude/COMMANDS.md`, `.claude/commands/workflow-help.md`

**Test:**
```bash
grep -n "Autonomy Ladder" .claude/COMMANDS.md
# New session: /workflow-help "does yolo merge?" answers from the contract
```

**Commit message:** `Add COMMANDS.md contract reference and /workflow-help`

---

## Step 7: Update global CLAUDE.md for the expanded suite

- [ ] Test-first: n/a (docs)
- [ ] Workflow table gains `/yolo`, `/beastmode`, `/phasegate`; `/plan` becomes
      `/gameplan`; pointer to `COMMANDS.md` with an explicit "do not load
      preemptively"; proactive-suggestion trigger for the `/yolo` wrap-up
- [ ] **Stage the workflow-table change only.** By the time this step runs,
      [land-baseline-commits.md](land-baseline-commits.md) steps 5 and 6 have
      already committed the other two changes to this file (the Writing Style
      enforce-forward clause and the `## Secrets` section), so a plain `git add`
      should be safe. Verify that with `git diff .claude/CLAUDE.md` before
      relying on it: that file is edited often, and a new unrelated change may
      have appeared since. If one has, use `git add -p` and select by content.

**File(s):** `.claude/CLAUDE.md`

**Test:**
```bash
git diff .claude/CLAUDE.md          # confirm ONLY the workflow-table change remains
git diff --cached .claude/CLAUDE.md | grep -c "gameplan"     # nonzero
git diff --cached .claude/CLAUDE.md | grep -c "1Password"    # 0 (already committed)
grep -nE "gameplan|phasegate|beastmode" .claude/CLAUDE.md
```

**Commit message:** `Update CLAUDE.md workflow tables for the expanded command suite`

---

## Step 8: Flip the acceptance test plan to live

- [ ] Test-first: n/a (docs)
- [ ] Update [command-kit-overhaul.md](command-kit-overhaul.md): batch committed,
      testing IN PROGRESS
- [ ] Keep every unchecked tier item as-is: they are the live test plan

**File(s):** `docs/plans/command-kit-overhaul.md`

**Test:** `grep -n "Batch committed" docs/plans/command-kit-overhaul.md`

**Commit message:** `Servanda suite is baselined; acceptance testing now live`

---

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `.claude/commands/gameplan.md` (new), `commands/plan.md` | 1 |
| `.claude/commands/yolo.md` | 2 |
| `.claude/commands/phasegate.md` (new) | 3 |
| `.claude/commands/booyah.md`, `commands/roadmap.md` | 4 |
| `.claude/commands/beastmode.md` | 5 |
| `.claude/COMMANDS.md` (new), `commands/workflow-help.md` | 6 |
| `.claude/CLAUDE.md` (workflow-table change) | 7 |
| `docs/plans/command-kit-overhaul.md` | 8 |

## Loose ends deliberately deferred

Not blocking this plan; each has a home:

- `.claude/commands/booyah.md:21` still searches a legacy `.claude/plans/`
  fallback alongside `docs/plans/`. Fold into the rename plan's Step 6
  cross-reference sweep rather than churning the file twice.
- [command-kit-overhaul.md](command-kit-overhaul.md) mixes two jobs: a one-time
  acceptance record for the 2026-07-05 batch, and what is really a reusable manual
  regression suite for the kit. Most tier items are worth re-running on every
  future kit change. Split after the rename (which renames every command the
  checklist names) into a historical record plus
  `docs/testing/servanda-manual-tests.md`.
