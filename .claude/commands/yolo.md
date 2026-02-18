Execute an entire plan autonomously on a feature branch without user intervention.

Arguments: $ARGUMENTS (optional - search term to find a plan file)

## What YOLO Does

YOLO = "You Only Live Once" mode. It executes an entire plan from start to finish:

1. Creates a feature branch (never works on main/master)
2. Implements ALL steps without stopping for user input
3. Commits after each step with good commit messages
4. Collects all test steps for manual verification at the end
5. Outputs a consolidated testing checklist when done

**Use this when:** You trust the plan and want to see the whole thing implemented quickly.

---

## CRITICAL SAFETY RULES

**NEVER violate these rules:**

1. **NO UNCOMMITTED CHANGES** - YOLO must start from a clean working tree. If there are uncommitted changes, STOP and tell the user.

2. **NEVER WORK ON MAIN/MASTER** - YOLO creates and works on feature branches only. If you somehow end up on main/master during execution, STOP immediately.

3. **CORRECT BRANCH ONLY** - If already on a feature branch, it must match the plan being executed. Never run one plan on another plan's branch.

4. **READ-ONLY HARVEST** - During automated testing, only use read-only Harvest API calls. Never create, update, or delete any Harvest data.

5. **COMPLETE THE PLAN** - Once started, execute ALL steps. Don't stop partway through unless there's an error you cannot resolve.

---

## Step 1: Identify the Plan

**If a plan argument is provided ($ARGUMENTS):**

1. Search `docs/plans/` for matching plan files
2. If exactly one match, confirm with user: "Found plan: <name>. Execute in YOLO mode?"
3. If multiple matches, list them and ask which one
4. If no matches, tell user and stop

**If no argument provided:**

1. Check `docs/plans/development-roadmap.md` for "Next Immediate Step"
2. Find its linked plan file
3. Confirm with user: "Found plan: <name>. Execute in YOLO mode?"

**Wait for user confirmation before proceeding.** This is the ONLY user interaction in YOLO mode.

---

## Step 2: Validate Git State

Run `git status` and check the current state:

**Check 1: Uncommitted changes**
```bash
git status --porcelain
```

If there is ANY output (uncommitted changes exist):

```
STOP! Cannot run YOLO with uncommitted changes.

You have uncommitted changes:
<list changes>

Please commit or stash your changes first, then run /yolo again.
```
**DO NOT PROCEED. STOP HERE.**

**Check 2: Current branch**

```bash
git branch --show-current
```

- If on `main` or `master`: Proceed to Step 3 (create feature branch)
- If on a feature branch: Proceed to Step 2b (validate branch matches plan)

---

## Step 2b: Validate Feature Branch Matches Plan

If already on a feature branch, verify it matches the plan:

1. Extract feature name from plan filename (e.g., `add-time-entry-domain-model.md` → `add-time-entry-domain-model`)
2. Check if current branch contains this name or a reasonable variation

**If branch matches plan:** Proceed to Step 4

**If branch does NOT match:**

```
STOP! Branch mismatch.

Current branch: feature/other-feature
Plan: add-time-entry-domain-model

Cannot run YOLO for one plan on another plan's branch.
Either:

1. Switch to main and run /yolo again (will create correct branch)
2. Switch to the correct feature branch
```

**DO NOT PROCEED. STOP HERE.**

---

## Step 3: Create Feature Branch

Only reached if on main/master with clean working tree.

1. Extract feature name from plan filename
2. Create and checkout feature branch:
```bash
git checkout -b feature/<plan-name>
```

Example: Plan `add-time-entry-domain-model.md` → branch `feature/add-time-entry-domain-model`

Announce: "Created branch: feature/<plan-name>"

---

## Step 4: Execute All Plan Steps (Autonomous Loop)

**Initialize test collection:**

- Create an empty list to collect all manual test steps

**For each uncompleted step in the plan (`- [ ]` items):**

### 4a: Implement the Step
- Read the step requirements
- Implement the changes (write code, edit files, etc.)
- Follow the plan's instructions exactly

### 4b: Run Automated Tests
- Execute any test commands in the plan that are READ-ONLY
- **SKIP any tests that would:**
  - Create/update/delete Harvest data
  - Make API calls that modify state
  - Require interactive user input
- If a test fails, attempt to fix and retry (up to 3 attempts)
- If still failing after 3 attempts, note the failure and continue

### 4c: Update Documentation
After each step, update as needed:

- `README.md` - If user-facing behavior changed
- `CLAUDE.md` - If developer patterns/conventions changed
- `run` script - If command usage changed
- Plan file - Mark step complete (`- [ ]` → `- [x]`)

### 4d: Commit the Step
1. Stage all changes: `git add -A`
2. Write descriptive commit message (use plan's suggested message if provided)
3. Commit immediately
4. Announce briefly: "Committed: {summary}"

### 4e: Collect Test Steps
- Add this step's manual test instructions to the collected list
- Include: what to test, commands to run, expected results

### 4f: Proceed to Next Step
- Immediately continue to the next uncompleted step
- NO waiting for user input
- NO asking for confirmation

**Repeat 4a-4f until all steps are complete.**

---

## Step 5: Finalize Plan Completion

Once all steps are done:

1. **Update the roadmap:**
   - Move completed item from current section to "Completed" section
   - If it was "Next Immediate Step", promote next "Upcoming" item
   - Commit: `Complete: <feature-name>`

2. **Verify all checkboxes are checked** in the plan file

---

## Step 6: Output Consolidated Testing Checklist

**IMPORTANT: Consolidate by command/action, not by step.**

When building the final checklist:
1. Group all test steps by the command or action required
2. If multiple steps need the same command run, combine them into ONE test item
3. List all the things to verify under that single command

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
  - `entry.hours` returns rounded_hours value
  - `entry.billable_amount` computes correctly
```

Present the consolidated checklist:

```
## YOLO Complete! Manual Testing Required

Branch: feature/<plan-name>
Commits: <number> commits made

### Manual Testing Checklist

Before merging, please verify:

- [ ] **<Command or action 1>**
  - <Thing to verify>
  - <Thing to verify>
  - <Thing to verify>

- [ ] **<Command or action 2>**
  - <Thing to verify>
  - <Thing to verify>

- [ ] **Review CLAUDE.md** for accuracy

- [ ] **Review README.md** for accuracy (if changed)

### Next Steps

1. Run the manual tests above
2. Review the changes: `git log main..HEAD --oneline`
3. Push the branch: `git push -u origin feature/<plan-name>`
4. Create a PR for review
5. After merge, delete the feature branch

If issues found, make fixes on this branch and I'll help commit them.
```

---

## Error Handling

**If any step fails and cannot be auto-fixed:**

1. Stop execution
2. Report what failed and why
3. Show what was completed successfully
4. Leave the branch in a consistent state (last successful commit)
5. Tell user how to resume or rollback

**If a critical safety rule would be violated:**

- STOP immediately
- Explain the violation
- Do NOT attempt to work around it
