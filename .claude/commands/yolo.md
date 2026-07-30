Execute an entire plan autonomously on a feature branch; re-running /yolo = resume, commit the fix round, or (plan complete + clean tree) approve, merge, wrap up, and phase-gate.

Arguments: $ARGUMENTS (optional - search term to find a plan file, or `done` to force wrap-up)

## What YOLO Does

YOLO = "You Only Live Once" mode. It is a small state machine keyed off observable git and plan state, so re-invoking `/yolo` always does the right next thing:

1. **Fresh run** (on main, plan identified): create a feature branch, implement ALL steps without stopping, commit per step, output a consolidated manual-testing checklist, stop.
2. **Resume** (on the plan's feature branch, unchecked steps remain): continue implementing where it left off.
3. **Fix round** (on the plan's branch, all steps checked, dirty tree): the user tested and reported issues that were just fixed in conversation; commit the fixes, re-present what to re-test, stop.
4. **Wrap-up** (on the plan's branch, all steps checked, clean tree): the user re-running `/yolo` here IS the approval signal, exactly like /booyah's. Merge the feature, delete the branch, return to main, update the roadmap, and run the phase gate if one is due.

`/yolo done` forces the wrap-up interpretation when detection is ambiguous (for example, one checkbox deliberately skipped).

The complaint path needs no special mode: after testing, the user describes problems in plain words, fixes happen in conversation on the same branch, and the next bare `/yolo` is either a fix-round commit (state 3) or the wrap-up (state 4).

**Use this when:** You trust the plan and want the whole thing implemented quickly, with you as the acceptance gate at the end.

---

## CRITICAL SAFETY RULES

**NEVER violate these rules:**

1. **NO UNCOMMITTED CHANGES ON FRESH RUN** - A fresh run (state 1) must start from a clean working tree. If there are uncommitted changes, STOP and tell the user. (States 3 and 4 legitimately encounter and handle uncommitted work.)

2. **NEVER WORK ON MAIN/MASTER** - Implementation happens on feature branches only. If you somehow end up on main/master during implementation, STOP immediately.

3. **CORRECT BRANCH ONLY** - If already on a feature branch, it must match the plan being executed. Never run one plan on another plan's branch.

4. **READ-ONLY AGAINST PROD-AFFECTING INTEGRATIONS** - During automated testing, only use read-only calls against any integration that touches real data (external APIs, SaaS systems, production databases). Never create, update, or delete real data.

5. **STOP ON UNRESOLVABLE FAILURES** - If a step's tests still fail after systematic debugging (see Step 4b), STOP the run and report state. Do NOT note the failure and continue; building later steps on a broken foundation compounds the damage.

6. **PHASE GATES RUN AT FABLE TIER OR NOT AT ALL** - The wrap-up phase gate is spawned with `model: "fable"`. If that is unavailable, skip the gate with an explicit handoff; never run it on a lesser model silently.

---

## Step 0: Detect State

Run:

```bash
git status --porcelain
git branch --show-current
```

Decide the state:

- **On main/master** (or a branch unrelated to any plan): **State 1 (fresh run)**. Go to Step 1.
- **On a feature branch matching a plan** (branch name contains the plan filename stem):
  - Plan has unchecked `- [ ]` steps: **State 2 (resume)**. Go to Step 4 and continue from the first unchecked step.
  - All steps checked, dirty tree: **State 3 (fix round)**. Go to Step 5.
  - All steps checked, clean tree (or `$ARGUMENTS` is `done`): **State 4 (wrap-up)**. Go to Step 6.
- **On a feature branch that does NOT match any plan**: STOP and report the mismatch. Never run one plan's work on another plan's branch.

Announce the detected state in one line, e.g. `State: wrap-up (plan complete, tree clean) - merging.`

---

## Step 1: Identify the Plan (fresh run)

**If a plan argument is provided ($ARGUMENTS):**

1. Search `docs/plans/` for matching plan files
2. If exactly one match, confirm with user: "Found plan: <name>. Execute in YOLO mode?"
3. If multiple matches, list them and ask which one
4. If no matches, tell user and stop

**If no argument provided:**

1. Check `docs/plans/development-roadmap.md` for "Next Immediate Step"
2. Find its linked plan file
3. Confirm with user: "Found plan: <name>. Execute in YOLO mode?"

**Wait for user confirmation before proceeding.** This is the ONLY user interaction in a fresh run.

If the roadmap's Next Immediate Step is a `PHASE GATE: <name>` marker rather than a plan, tell the user the phase is awaiting its gate and suggest `/phasegate` (or wrap-up state 4 if the gate follows a feature just finished here).

---

## Step 2: Validate Git State (fresh run)

**Check: uncommitted changes**

```bash
git status --porcelain
```

If there is ANY output:

```
STOP! Cannot start a fresh YOLO run with uncommitted changes.
Please commit or stash first, then run /yolo again.
```

**DO NOT PROCEED. STOP HERE.**

---

## Step 3: Create Feature Branch (fresh run)

1. Extract feature name from plan filename
2. Create and checkout:
```bash
git checkout -b feature/<plan-name>
```

Announce: "Created branch: feature/<plan-name>"

---

## Step 4: Execute Plan Steps (states 1 and 2)

**Initialize test collection:** an empty list of manual test steps (state 2: rebuild it from already-completed steps' test sections so the final checklist is complete).

**For each uncompleted step in the plan (`- [ ]` items):**

### 4a: Implement the Step
- Read the step requirements
- If the plan is TDD-shaped (a "write the failing test first" sub-item), honor the order: write the test, see it fail, then implement, then see it pass
- Follow the plan's instructions exactly

### 4b: Run Automated Tests
- Execute any test commands in the plan that are READ-ONLY (per safety rule 4)
- SKIP tests that would modify real data in prod-affecting integrations or require interactive input; add them to the manual checklist instead
- **If a test fails, debug it systematically. Do not shotgun retries:**
  1. Reproduce it and read the actual failure output
  2. Form a hypothesis about the root cause
  3. Gather evidence (read the code, logs, and data involved) to confirm or kill the hypothesis
  4. Fix the root cause, not the symptom
  5. If the investigation reveals a distinct new bug, follow the CLAUDE.md TDD policy: write the failing test first, then fix
- **Cap: 3 root-cause attempts per step.** Still failing: STOP the entire run (safety rule 5) and report what was completed, what failed, the evidence gathered, and the current hypothesis.

### 4c: Update Documentation
After each step, update as needed:
- `README.md` - if user-facing behavior changed
- `CLAUDE.md` - if developer patterns/conventions changed
- `run` script - if command usage changed
- Plan file - mark step complete (`- [ ]` to `- [x]`)

### 4d: Commit the Step
1. Stage all changes: `git add -A`
2. Write a descriptive commit message (use plan's suggested message if provided; no Claude attribution)
3. Commit immediately
4. Announce briefly: "Committed: <summary>"

### 4e: Collect Test Steps
- Add this step's manual test instructions to the collected list

### 4f: Proceed to Next Step
- Immediately continue; no waiting, no confirmation

**When all steps are complete:** proceed to Step 7 (testing checklist) and STOP. Do not merge; that is the user's call via the next `/yolo`.

---

## Step 5: Fix Round Commit (state 3)

The dirty tree is the just-finished fix work from the user's testing feedback.

1. `git status` and `git diff` to see what changed
2. Ensure any bug fixed here has its failing-test-first coverage per CLAUDE.md TDD policy
3. `git add -A` and commit with a message describing the fixes (e.g. `Fix from manual testing: <summary>`)
4. Re-present a DELTA testing checklist: only what the fixes affected
5. Announce: "Fixes committed. Run `/yolo` again when testing passes to merge and wrap up."
6. STOP.

---

## Step 6: Wrap-Up (state 4)

The user re-running `/yolo` on a completed, clean branch IS the approval. Announce each action as it happens; do not ask for pre-confirmation.

### 6a: Detect Mode

```bash
git remote -v
gh auth status 2>&1 || true
```

- Remote exists AND `gh` authenticated: **PR mode**
- Otherwise: **Local mode**

### 6b: Merge

**Local mode:**
```bash
git checkout main
git merge --no-ff feature/<plan-name> -m "Merge feature/<plan-name>"
git branch -d feature/<plan-name>
```
Preserve full history: `--no-ff`, never squash, never rebase (honor an explicit repo override in CLAUDE.md/CONTRIBUTING.md if one exists).

**PR mode:**
1. Push: `git push -u origin feature/<plan-name>`
2. Create the PR: title under 70 chars; body includes a summary, the plan link, and an "Operator verified" section recording that the user manually tested (list what the checklist covered)
3. Wait for CI green: poll `gh pr checks` every 30 seconds, 45-minute cap. CI failure: diagnose and fix using the same systematic method as Step 4b, push, re-wait (3 fix rounds max, then STOP)
4. Merge preserving history: `gh pr merge <PR#> --merge --delete-branch`
5. `git checkout main && git pull --ff-only`

Announce: "Merged: feature/<plan-name>" and "Branch deleted".

### 6c: Update Roadmap

1. Move the completed item from "Next Immediate Step" to "Completed"; promote the next "Upcoming" item
2. Commit on main: `Complete: <feature-name>` (push in PR mode)

### 6d: Phase Gate (if due)

If the roadmap's next item is a `PHASE GATE: <phase name>` marker:

1. Spawn the phase-gate audit as a fresh-context subagent via the Agent tool with `model: "fable"`, instructing it to follow `~/.claude/commands/phasegate.md` for the named phase. (The work is merged and the user's invocation is explicit consent; auto-run is correct here.)
2. Commit the gate report it produces (push in PR mode), and mark the PHASE GATE item complete in the roadmap on a PASS.
3. **PASS / PASS_WITH_FINDINGS (minor only):** announce the verdict and finish.
4. **Findings (medium+):** present the fix list and recommend a `/gameplan` session to plan the fixes before starting the next phase. Do not attempt architectural fixes here.
5. **Fable unavailable:** announce "Phase gate pending: run /phasegate in a Fable session." Never run the gate on a lesser model.

### 6e: Final Announcement

```
Wrapped up: <feature-name>
  Merged to main (<local|PR #N>), branch deleted
  Roadmap updated - next up: <name or "(none)">
  Phase gate: <not due | PASS | findings: see report | pending Fable session>
```

---

## Step 7: Consolidated Testing Checklist (end of states 1 and 2)

**IMPORTANT: Consolidate by command/action, not by step.**

1. Group all collected test steps by the command or action required
2. If multiple steps need the same command run, combine them into ONE test item with all verifications listed under it

**Example consolidation:**

If Step 1 says "Run `./run shell` and verify TimeEntry class exists"
and Step 3 says "Run `./run shell` and verify billable_amount works"

**WRONG (don't do this):**

```
#### From Step 1:
- [ ] Run `./run shell` and verify TimeEntry class exists

#### From Step 3:
- [ ] Run `./run shell` and verify billable_amount works
```

**CORRECT (do this):**

```
- [ ] **Run `./run shell`** and verify:
  - TimeEntry class exists and can be instantiated
  - `entry.billable_amount` computes correctly
```

Present it:

```
## YOLO Complete! Manual Testing Required

Branch: feature/<plan-name>
Commits: <number>

### Manual Testing Checklist

- [ ] **<Command or action 1>**
  - <Thing to verify>
  - <Thing to verify>

- [ ] **Review CLAUDE.md / README.md** for accuracy (if changed)

### Next Steps

- Test the items above.
- All good? Run `/yolo` again (or `/yolo done`) and I will merge, clean up, update the roadmap, and run the phase gate if one is due.
- Problems? Just tell me what's wrong; I'll fix on this branch, commit, and you re-test.
```

Then STOP.

---

## Error Handling

**If any step fails and cannot be resolved (after the systematic-debugging cap):**

1. Stop execution
2. Report what failed, the evidence gathered, and the current root-cause hypothesis
3. Show what was completed successfully
4. Leave the branch in a consistent state (last successful commit)
5. Tell user how to resume (`/yolo` resumes from the first unchecked step) or roll back

**If a critical safety rule would be violated:**

- STOP immediately
- Explain the violation
- Do NOT attempt to work around it
