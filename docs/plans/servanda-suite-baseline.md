# Plan: Review and Baseline the Servanda Suite Overhaul

**Status:** STILL HELD. **Do not commit anything in this plan until Scott has read
through the files themselves and says go** (reaffirmed 2026-07-29).

Two separate gates, do not confuse them:

| Gate | State |
|---|---|
| The five design questions below | CLEARED 2026-07-29, all five decided with reasoning recorded |
| Scott's read-through of the ten files | **STILL OPEN.** Nothing commits until this clears. |

Answering the design questions did not clear the review. Scott explicitly wants to
read the current state, and may work on these files further, before they are
baselined. The design decisions tell you *what shape* the suite should have; they do
not certify that what is in the working tree actually implements that shape.

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

Before any commit below, review the current state. Questions worth deciding during
the review, all cheaper to change before baselining than after. Answers recorded
as they are settled (review session 2026-07-29).

### Q1: Is the `/yolo` 4-state machine the right shape? DECIDED: yes, keep as-is

States keyed off observable git and plan state, with re-invocation as the approval
signal, same grammar `/booyah` uses per step:

| Detected state | Condition | Action |
|---|---|---|
| 1 fresh run | on main/master | branch, implement all steps, stop with checklist |
| 2 resume | on plan branch, unchecked steps remain | continue from first unchecked |
| 3 fix round | on plan branch, all checked, dirty tree | commit fixes, re-list what to retest |
| 4 wrap-up | on plan branch, all checked, clean tree | MERGE, delete branch, roadmap, gate |
| STOP | branch matches no plan | refuse the mismatch |

`/yolo done` forces state 4. The command announces the detected state in one line
before acting.

Considered and rejected: adding a confirmation before the wrap-up merge (breaks the
"re-invocation IS approval" promise at exactly the rung where unattended behavior
is the point), and splitting wrap-up into a separate command (loses the "keep
running /yolo until done" rhythm). Accepted risk: state is inferred rather than
declared, and the riskiest inference is fix-round vs wrap-up, which turns only on
whether the tree is dirty. The one-line state announcement is the mitigation, so
keep it.

### Q2: Are the model pins right? DECIDED: yes, and no new abstraction needed

The pins are already provider-agnostic capability tiers. `model: "fable"` does not
mean "Anthropic Fable 5"; it means "whatever `ANTHROPIC_DEFAULT_FABLE_MODEL`
resolves to." All four aliases (haiku, sonnet, opus, fable) have
`ANTHROPIC_DEFAULT_*_MODEL` remap vars, confirmed present in the CLI binary
(`strings` on `~/.local/share/claude/versions/2.1.220`, build 2.1.220). The parked
Ollama profile in `settings.json` already exploits this for haiku/sonnet/opus.

So switching to OpenRouter with GPT-5.6 or Kimi K3 needs only the `env` block
changed: set `ANTHROPIC_DEFAULT_FABLE_MODEL=openai/gpt-5.6`,
`ANTHROPIC_DEFAULT_OPUS_MODEL=moonshot/kimi-k3`, and all five spawn sites work
unchanged. The vendor mapping lives in exactly one place already.

Considered and rejected: a semantic tier layer ("super smart" / "smart") mapped per
provider, and threading tier params through every spawn site. Both would stack a
second indirection on one that already ships. The alias names read as vendor names,
which is what made them look Anthropic-locked, but semantically they are tiers.

**Unavailability: STOP, never degrade** (Scott's call, 2026-07-29: "networks fail,
Anthropic has a whopping 89% uptime"). Confirmed as written in safety rule 10.

Three follow-ups this decision creates. All three touch `beastmode.md` and
`phasegate.md`, which is a third argument for folding into the rename (see Q5):

1. **Document that the pins are tiers, not vendors** (one paragraph in
   `COMMANDS.md` beside the existing verification-tiers line). Without it, a future
   reader sees `model: "fable"` and concludes the suite is Anthropic-locked, then
   adds fallback logic that is not needed.
2. **Fix the parked Ollama profile:** `x-env` remaps haiku, sonnet, and opus but
   NOT fable. Flipping to Ollama today would leave the audit tier unmapped, which
   under STOP-not-degrade means a hard halt at every gate. One line, in the held
   `settings.json`.
3. **Add a preflight guard** to `/beastmode` preflight and `/phasegate`'s opening
   check: if `ANTHROPIC_BASE_URL` points at a non-Anthropic host AND the tier alias
   this step needs is unmapped, STOP and say so rather than guessing. Default when
   unconfigured is stop-and-ask, consistent with the unavailability rule.

**Still to verify behaviorally:** `strings` proves the env var name is present in
the binary, not that it is honored as described. The inference is strong (its three
siblings demonstrably work through the Ollama profile, and the
`_NAME`/`_DESCRIPTION`/`_SUPPORTED_CAPABILITIES` companions match the supported
pattern), but set it to something identifiable once and confirm a spawned subagent
lands on that model before relying on it for gates.

### Q3: Are the safety caps right? DECIDED: keep all four as written

| Cap | Value |
|---|---|
| Review passes per feature | 5 |
| CI fix attempts per PR | 5 |
| Combined fix rounds per PR | 8 |
| Wall clock per PR | 4 hours |

Breach behavior stays: STOP and recommend escalating to a Fable session, on the
theory that a non-converging loop signals a wrong plan or architecture rather than
code needing another patch. That framing is the actual safety mechanism; the exact
thresholds matter less than the fact that something stops.

Considered and rejected: logging every breach to build empirical thresholds (real
value, but it only pays off after several runs and adds an artifact to maintain),
and dropping the 4-hour wall clock (it is the one cap that can fire on healthy work
when CI queues are slow, but it is also the only backstop against a stuck loop that
never trips the count caps).

Acknowledged: these numbers are untested guesses. Accepted deliberately rather than
deferred. If acceptance testing shows 5 review passes is routinely too few, that is
a cheap one-line change later.

### Q4: `/booyah` Step 4's `git add -A` is a footgun. DECIDED: ask on first invocation only

Found 2026-07-29 while trying to use `/booyah` to land the baseline commits. Step 2
treats any dirty tree as "my previous step's work needs committing," then Step 4
stages with `git add -A`. Any pre-existing unrelated dirty work therefore gets swept
into a step commit with a message describing something else. This is not
hypothetical: it is why [land-baseline-commits.md](land-baseline-commits.md) had to
be run manually.

**Key insight that shapes the fix:** the assumption is CORRECT in the normal case.
If `/booyah` has been running in this session, a dirty tree genuinely is its own
work. The bug bites only on the FIRST invocation against a tree that was already
dirty. So the fix is narrow.

The fix:

- **First invocation of a session, dirty tree:** do NOT assume the work is yours.
  Show what is dirty and ask whether it is the step to commit or unrelated work to
  leave alone.
- **Second and subsequent invocations:** unchanged. `git add -A`, commit, proceed.
  By then the tree really is booyah's own work, and the no-prompt permission model
  ("running `/booyah` IS the permission signal") is preserved for the common case.

Considered and rejected: staging only the step's declared **File(s)** paths (real
regression risk, since plans routinely touch files the File(s) line did not
anticipate, and those edits would be silently left uncommitted, which is worse than
a commit with a slightly-off message), and tracking the files booyah itself edited
(most accurate, but the record does not survive a session restart and booyah is
designed to resume from cold git state, so it would need the ask-fallback anyway).

**Also apply to `/yolo` state 3 (fix round),** which shares the shape: it commits a
dirty tree it did not necessarily create. Same narrow fix, same reasoning. Verify
during implementation whether state 3's branch-match check already narrows it enough
that the ask is redundant.

### Q5: Fold into the rename, or baseline separately? DECIDED: keep separate, baseline first

Sequence:

1. **Baseline the suite as-is** (this plan, steps 1 through 8)
2. **Apply the Q2 and Q4 fixes** ([servanda-review-fixes.md](servanda-review-fixes.md))
3. **Acceptance testing** ([command-kit-overhaul.md](command-kit-overhaul.md))
4. **Rename** ([command-suite-rename.md](command-suite-rename.md))

The deciding factor: 1,400 lines currently exist only in the working tree. Getting
them into git today beats a cleaner history later. Secondary: git history then shows
what the 2026-07-05 overhaul actually was, separately from the mechanical rename,
and acceptance testing gets a real baseline to sit on.

Accepted cost: `beastmode.md`, `phasegate.md`, `booyah.md`, and `yolo.md` get
touched in three passes (baseline, fixes, rename), so some diffs are churn. Judged
worth it. History is verbose but honest.

Considered and rejected: folding the fixes into the rename (known bugs would sit in
the baseline for however long the rename takes, and acceptance testing would
exercise code already known to be wrong), and one big pass doing rename plus fixes
plus first commit together (each file touched once, but nothing is committed until
all of it is, which is the largest possible risk window for work that has no other
copy).

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
