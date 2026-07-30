Unleash beast mode: chew through the entire roadmap autonomously, one feature at a time, with an independent Opus review loop, CI-green merges, and automatic Fable phase gates at PHASE GATE markers.

Arguments: $ARGUMENTS (optional - search term to start from a specific plan; otherwise start from "Next Immediate Step")

## What Beast Mode Does

Beast mode is `/yolo` + self-review + fix + merge, on repeat, until the roadmap is empty:

For each "yolo-able" roadmap item:
1. Run a YOLO-style implementation pass on a feature branch
2. Push and open a PR (or stay local if no remote) with a nice description, assigned to the user
3. Spawn a code-review subagent to critique the branch
4. Write the review to the PR (or capture it locally)
5. Loop back into implementation to fix every actionable finding
6. Re-review. Repeat until clean.
7. Approve and merge the PR, delete local + remote feature branch, return to main
8. Pick the next yolo-able roadmap item and start the cycle over
9. Stop when the roadmap has nothing left that can run unattended

**Use this when:** You trust the roadmap, you trust the plans, and you want to come back to a finished project (or as close as autonomous execution can get).

---

## CRITICAL SAFETY RULES

**NEVER violate these rules:**

1. **NO UNCOMMITTED CHANGES** - Beast mode must start from a clean working tree. If there are uncommitted changes, STOP and tell the user.

2. **NEVER WORK ON MAIN/MASTER** - All implementation happens on feature branches. Main/master is only checked out to branch from or to merge into.

3. **NEVER FORCE PUSH MAIN/MASTER** - Ever. Even if it seems convenient. Stop instead.

4. **ONE FEATURE = ONE BRANCH = ONE PR** - Don't reuse branches across features. Don't bundle multiple roadmap items into a single PR.

5. **READ-ONLY HARVEST (and any other prod-affecting integrations)** - During automated testing, only use read-only API calls. Never create, update, or delete real data.

6. **REVIEW MUST BE INDEPENDENT** - The review subagent runs as a fresh subagent with no prior conversation context. Do not "pre-bias" it by telling it the answer.

7. **NO EMPTY APPROVALS** - Do not approve and merge a PR until the review loop has produced a genuinely clean review (no actionable findings of medium severity or higher).

8. **STOP ON UNRESOLVABLE ERRORS** - If something fails that you cannot fix in 3 attempts, stop the entire beast mode loop and report state. Don't paper over failures to "keep moving."

9. **NOT DONE UNTIL CI IS GREEN** (PR mode) - A PR is not "done" when the review loop converges. It is done when CI is green AND review is clean AND it has been merged. If CI is red, treat it as part of the work that beast mode owns and must fix before moving on.

10. **PHASE GATES RUN AT FABLE TIER OR NOT AT ALL** - The phase-gate audit is spawned with `model: "fable"`. If that model is unavailable in this environment, STOP at the gate and hand off to the user. Never run the gate on a lesser model, and never skip past an unrun gate.

---

## Progress Announcements

Beast mode runs unattended for a long time. Emit short, scannable status lines at each meaningful milestone so the user can glance at the terminal and know what's happening.

**Use a green check (`✅`) as the prefix for every successful milestone announcement.** This is the beast mode "brand mark" for forward progress. Examples:

- `✅ Preflight clean — PR mode, starting from: <plan-name>`
- `✅ Branch created: feature/<plan-name>`
- `✅ Step committed: <short summary>`
- `✅ All plan steps complete (<N> commits)`
- `✅ PR opened: #<num> — <url>`
- `✅ Review pass <N>: CLEAN`
- `✅ CI green (<N> checks passed)`
- `✅ PR merged: #<num>`
- `✅ Branch deleted: feature/<plan-name>`
- `✅ Roadmap updated — next up: <name>`
- `✅ Beast mode complete — <N> features shipped`

For non-success states use plain prefixes (no green check), e.g.:
- `⏳ Waiting on CI — <N>/<M> checks running`
- `⚠️  Review pass <N>: NEEDS_CHANGES (<count> findings)`
- `❌ CI failed: <check name> — fetching logs`
- `🛑 Stopping beast mode: <reason>`

The green check is reserved for genuine forward progress. Don't put it on failures or "still working" updates — that defeats the branding.

---

## Step 0: Preflight

Before starting the outer loop, validate the environment ONCE:

1. **Git state:**
   ```bash
   git status --porcelain
   git branch --show-current
   ```
   - If working tree is dirty: STOP. Tell user to commit/stash first.
   - If not on main/master: ask the user if they want to continue from the current branch as-is or switch to main first. Default to switching to main.

2. **Remote / PR mode detection:**
   ```bash
   git remote -v
   gh auth status 2>&1 || true
   ```
   - If there is a remote AND `gh` is authenticated: **PR mode**. We push, open PRs, write reviews as PR comments, approve, merge.
   - If there is no remote OR `gh` is not available/authenticated: **Local mode**. We do all review work in-repo (review written to a tmp file or inline), and merge locally without pushing.
   - Announce which mode is active: "Beast mode engaged: PR mode" or "Beast mode engaged: Local mode".

3. **Roadmap presence:**
   - Confirm `docs/plans/development-roadmap.md` exists. If not, STOP and tell user to run `/roadmap` first.

4. **GitHub user (PR mode only):**
   ```bash
   gh api user --jq .login
   ```
   - Capture for PR assignment.

5. **Model tier availability:**
   ```bash
   echo "base=${ANTHROPIC_BASE_URL:-<anthropic default>}"
   echo "opus=${ANTHROPIC_DEFAULT_OPUS_MODEL:-<unset>}"
   echo "fable=${ANTHROPIC_DEFAULT_FABLE_MODEL:-<unset>}"
   ```
   The `model:` values this command spawns with are tier aliases, not vendor names (see COMMANDS.md). They resolve through those env vars, so a custom provider needs them mapped.

   - If `ANTHROPIC_BASE_URL` is unset or points at Anthropic: the aliases resolve natively. Proceed.
   - If `ANTHROPIC_BASE_URL` points at a non-Anthropic host AND either alias above is unset: **STOP before the confirmation prompt.** Do not spawn and hope.
     ```
     🛑 Provider is <host> but the <opus|fable> tier is unmapped.
        This run needs Opus-tier review and Fable-tier gates.
        Map ANTHROPIC_DEFAULT_OPUS_MODEL / ANTHROPIC_DEFAULT_FABLE_MODEL
        in settings.json env, then re-run /beastmode.
     ```
   - Never guess a model name, and never substitute a lower tier. Unconfigured means stop and ask, the same rule as safety rule 10.

6. **Final confirmation:**
   - Show the user: mode (PR / Local), starting roadmap item, and how many "Upcoming" items follow.
   - Ask: "Engage beast mode? This will run autonomously through these items until done or blocked."
   - Wait for confirmation. **This is the only user prompt in the entire run.**

---

## Step 1: Pick the Next Roadmap Item

At the top of each outer-loop iteration:

1. Read `docs/plans/development-roadmap.md`.
2. Identify the current "Next Immediate Step".
3. **If the item is a PHASE GATE marker** (an item titled `PHASE GATE: <phase name>`): run the phase gate per Step 1b, then loop back to Step 1.
4. Find its linked plan in `docs/plans/`.
5. Determine if the item is **yolo-able**:
   - Has a concrete plan file with checkbox steps
   - No "needs human input" / "decision required" / "do not auto-implement" markers
   - No `(don't plan this part)` or "manual" tags
6. **If not yolo-able:** Skip to Step 7 (Wrap Up). Beast mode ends cleanly with a report of what got done and what got skipped and why.
7. **If yolo-able:** Proceed to Step 2.

If `$ARGUMENTS` was provided on the initial invocation, use it ONLY to pick the first item; subsequent iterations always read fresh from the roadmap.

---

## Step 1b: Run the Phase Gate (PHASE GATE markers only)

The phase-gate audit verifies that the just-completed phase delivered its plans' promises before beast mode rolls into the next phase. It runs at Fable tier, independently, against merged main.

1. Announce: `⏳ PHASE GATE reached: <phase name> - spawning Fable audit`
2. Spawn a fresh-context subagent via the Agent tool with `model: "fable"`, instructing it to follow `~/.claude/commands/phasegate.md` for the named phase (audit only; it must not fix code). If the fable model override is unavailable or the spawn fails on model grounds: STOP the entire run (safety rule 10) and report `🛑 Phase gate requires a Fable-tier audit - run /phasegate in a Fable session, then re-run /beastmode.`
3. Commit the gate report the audit produces (under `docs/assessments/`) on main; push in PR mode.
4. **Verdict PASS (or PASS_WITH_FINDINGS with nothing above low severity):** mark the PHASE GATE item complete in the roadmap, commit (`Phase gate passed: <phase name>`), announce `✅ Phase gate PASSED: <phase name>`, and loop back to Step 1 to start the next phase.
5. **Verdict with medium+ findings or FAIL:** announce `🛑 Phase gate found issues: <phase name> (<count> findings)`, STOP the entire beast mode run, and present the fix list. Architectural findings are planned in a `/gameplan` session (Fable), never auto-fixed by the implementation model.

---

## Step 2: Implementation Pass (YOLO-style)

This is essentially `/yolo` executed inline. Do not actually invoke `/yolo` as a subcommand. Run its logic directly.

1. **Create feature branch from main:**
   ```bash
   git checkout main   # or master, whichever is the main branch
   git pull --ff-only  # PR mode only; skip in local mode if no remote
   git checkout -b feature/<plan-name>
   ```
   Announce: `✅ Branch created: feature/<plan-name>`

2. **Execute every uncompleted step** (`- [ ]`) in the plan:
   - Implement the step (write code, edit files)
   - Run any READ-ONLY tests included in the plan
   - Update docs as needed (`README.md`, `CLAUDE.md`, `run`, the plan file itself)
   - Mark the step `- [x]` in the plan
   - `git add -A` and commit with a descriptive message (no Claude attribution)
   - Announce per step: `✅ Step committed: <short summary>`
   - Move to the next step immediately

3. **On test failures:** Retry up to 3 times. If still failing, STOP the entire beast mode run and report.

4. **When all steps are done:** Announce `✅ All plan steps complete (<N> commits)` and proceed to Step 3.

---

## Step 3: Open the PR (PR mode) or Snapshot the Diff (Local mode)

### PR mode

1. **Push the branch:**
   ```bash
   git push -u origin feature/<plan-name>
   ```

2. **Build the PR description.** Include:
   - **Summary:** 1-3 bullets of what shipped
   - **Plan:** link to `docs/plans/<plan-name>.md`
   - **Roadmap item:** which roadmap entry this completes
   - **Commits:** brief list (or "see commit history")
   - **Test plan:** checklist of how to manually verify
   - **Notes / known gaps:** anything autonomous execution couldn't resolve

3. **Create the PR:**
   ```bash
   gh pr create \
     --title "<concise title under 70 chars>" \
     --assignee "<github-user-from-preflight>" \
     --body "$(cat <<'EOF'
   <description from step 2>
   EOF
   )"
   ```

4. **Capture the PR URL and number** for later steps.

5. Announce: `✅ PR opened: #<num> — <url>`

### Local mode

1. Generate a diff snapshot for the review:
   ```bash
   git log main..HEAD --oneline
   git diff main..HEAD
   ```
2. No push, no PR. Hold these in memory (or write to a tmp file under `/tmp/`) for the review subagent.

---

## Step 4: Review Loop

This is the heart of beast mode. Iterate until the review is clean.

### 4a: Spawn the Review Subagent

Launch a fresh subagent via the Agent tool with `subagent_type: "general-purpose"` (or a dedicated reviewer if one exists) and `model: "opus"`. Pin the reviewer model explicitly: review quality must not float with whatever model happens to be driving the session. The subagent has NO conversation history. Brief it completely.

**Prompt template for the review subagent:**

```
You are a senior staff engineer doing an independent code review of a feature branch. You did not write this code and have no context from prior conversation. Be rigorous, specific, and fair.

## What to review
- Branch: feature/<plan-name>
- Base: main
- Plan being implemented: docs/plans/<plan-name>.md
- Roadmap item: <roadmap entry>

## Review focus (in priority order)
1. **Correctness & security**: bugs, race conditions, injection risks, auth/authz gaps, secret handling, data exposure
2. **Scale & performance**: N+1 queries, unbounded loops, memory issues, blocking I/O, missing indexes
3. **Plan & architecture adherence**: does this implement what the plan said? Does it fit the existing architecture? Does it duplicate work or reinvent existing utilities?
4. **Code quality & best practices**: naming, separation of concerns, error handling, dead code, premature abstraction
5. **Test coverage**: new behavior has tests; bug fixes have a failing-then-passing test per the project's TDD policy in CLAUDE.md. The bar: new modules/packages carry unit tests; every user-visible or lifecycle behavior touched has an end-to-end/conformance test where the project has such a suite; overall coverage must not decrease. Cite specific untested paths, not "add more tests"
6. **Docs & artifacts**: README, CLAUDE.md, run script, plan file, roadmap all reflect the change

## How to investigate
- Read CLAUDE.md (project + user) for conventions and policies
- Read the plan file end-to-end
- `git log main..HEAD` and `git diff main..HEAD`
- Read the actual files changed, not just the diff hunks
- Grep for duplicated functionality before flagging "should use existing util" (cite the util)

## Output format (strict)

### Verdict
One of: CLEAN | MINOR_ONLY | NEEDS_CHANGES | BLOCKED

### Findings
For each finding:
- **Severity**: critical | high | medium | low | nit
- **Location**: file:line (or file if structural)
- **Issue**: what's wrong, concretely
- **Suggested fix**: what to change

### Things done well
Brief, specific positives (helps calibrate). Optional.

## Rules
- Be specific. "Add more tests" is useless; "TimeEntry#billable_amount has no test for the zero-rate case at line 42" is useful.
- Cite evidence. If you claim duplication, name the existing function.
- Don't invent problems. If it looks fine, say CLEAN.
- Don't fix anything. Just review.
```

### 4b: Post the Review

**PR mode:**
- Format the review as a PR comment using `gh pr comment <PR#> --body-file <tmpfile>` or `gh pr review <PR#> --comment --body-file <tmpfile>` depending on what's appropriate.
- Use `gh pr review --request-changes` if verdict is NEEDS_CHANGES or BLOCKED; `--comment` if MINOR_ONLY or CLEAN.

**Local mode:**
- Append the review to a session log (e.g., `/tmp/beastmode-<plan-name>-reviews.md`) with a timestamp and pass number.
- Echo the review to the user's terminal output.

### 4c: Decide

- **CLEAN**: Announce `✅ Review pass <N>: CLEAN`. Exit the review loop. Proceed to Step 4.5 (CI wait) in PR mode, or Step 5 in Local mode.
- **MINOR_ONLY**: Announce `✅ Review pass <N>: MINOR_ONLY`. Exit the review loop. Proceed to Step 4.5 / Step 5. (Optionally address nits if trivial, but don't loop on them.)
- **NEEDS_CHANGES**: Announce `⚠️  Review pass <N>: NEEDS_CHANGES (<count> findings)`. Proceed to Step 4d.
- **BLOCKED**: Announce `🛑 Review pass <N>: BLOCKED`. STOP the entire beast mode run. Report the blocker.

### 4c-2: Fable Security Pass (security-sensitive changes only)

When the review loop exits CLEAN or MINOR_ONLY, check whether the branch touches the security surface: authn/authz, permission or privilege modes, trust boundaries or prompt/contract composition, tenant or data isolation, secret handling, subprocess/argv construction, file permissions, or parsing of untrusted content.

- **Not touched:** proceed as normal.
- **Touched:** run ONE additional review pass by spawning a fresh subagent per 4a but with `model: "fable"` and a prompt focused solely on security (adversarial mindset: injection, privilege escalation, path traversal, TOCTOU, data leakage; same strict output format). Findings feed 4d like any review pass. If the fable model override is unavailable: do NOT merge this feature; STOP the run and report that a Fable security review is pending (safety-rule-10 spirit: security review never silently degrades).

### 4d: Fix the Findings

For each actionable finding (critical / high / medium):
1. Implement the fix
2. Update tests if needed (write failing test first for any new bug discovered, per CLAUDE.md TDD policy)
3. Update docs if needed
4. Commit with a message referencing the review: `Address review: <short summary>`

Push the new commits (PR mode):
```bash
git push
```

### 4e: Re-review

Go back to 4a with a fresh subagent. Repeat until CLEAN or MINOR_ONLY.

**Safety cap:** If the review loop runs more than 5 passes on a single feature without converging, STOP and report, and recommend escalating to a Fable session: a non-converging review loop usually signals an architectural misunderstanding in the plan or the code, not a bug the implementation model can patch its way out of.

---

## Step 4.5: Wait for CI Green (PR mode only)

**Skip this entire step in Local mode** — no CI, no waiting. Go straight to Step 5.

**The job is not done until CI is green.** Beast mode owns this. If CI fails, beast mode reads the logs, fixes the cause, pushes, and waits again — same loop discipline as the review loop.

### 4.5a: Detect whether there are any checks

```bash
gh pr checks <PR#> --json name,state,conclusion
```

- If the PR has **zero required checks configured** (output is empty or trivially complete): announce `✅ No CI checks configured — skipping CI wait` and proceed to Step 5.
- Otherwise, enter the polling loop in 4.5b.

### 4.5b: Poll Until Done or Timeout

- Announce: `⏳ Waiting on CI — <N> checks running`
- Poll every **30 seconds** using `gh pr checks <PR#>`.
- **Timeout cap: 45 minutes** (90 polls) per CI attempt. This accounts for slow project pipelines.
- States to recognize:
  - All checks `pass` / `success`: announce `✅ CI green (<N> checks passed)` and proceed to Step 5.
  - Any check `fail` / `failure` / `cancelled` / `timed_out` / `action_required`: proceed to 4.5c (fix loop).
  - All checks still `pending` / `in_progress` / `queued` / `waiting`: keep polling.
- During polling, every ~5 minutes emit a heartbeat: `⏳ CI still running — elapsed: <Xm>, <N> pending`.

**On the 45-minute timeout with checks still pending:**
- Announce: `🛑 CI exceeded 45-min budget while still running.`
- Do NOT cancel the CI run; the user may want it to finish.
- STOP beast mode. Report state. Do not merge.

### 4.5c: Fetch Logs and Diagnose

When a check fails:

1. Announce: `❌ CI failed: <check name> — fetching logs`
2. Identify the failing run and its logs:
   ```bash
   gh pr checks <PR#> --json name,state,conclusion,link
   gh run view <run-id> --log-failed
   ```
   (For non-GitHub-Actions checks where logs aren't available via `gh`, capture whatever URL or summary `gh pr checks` provides and read what you can.)
3. Read the failure output. Identify the actual cause:
   - Test failures: which test, what assertion, what value
   - Build/compile errors: file and line
   - Lint/style: file and rule
   - Flaky/infra: timeout, network, runner crash (see 4.5e)

### 4.5d: Fix, Push, Re-wait

1. Diagnose to the root cause before fixing: reproduce the failure, form a hypothesis, and confirm it with evidence from the logs and code. Do not shotgun speculative fixes to "see if CI likes this one." Then implement the fix on the same feature branch.
2. If a new bug was uncovered, follow CLAUDE.md TDD policy: write the failing test first, then fix.
3. Commit:
   ```bash
   git add -A
   git commit -m "Fix CI: <short cause>"
   git push
   ```
4. Announce: `✅ CI fix pushed: <short cause> — re-waiting on CI`
5. Loop back to 4.5b with a fresh 45-minute budget.

### 4.5e: Flaky / Infrastructure Failures

If the failure looks like infrastructure or flake (network timeout to package mirror, runner died, transient external service error, etc.) and the code itself is fine:

1. Re-run the failing checks:
   ```bash
   gh run rerun <run-id> --failed
   ```
2. Announce: `⚠️  Suspected flake — re-running failed checks`
3. Loop back to 4.5b.
4. **Flake retry cap: 2 reruns.** If the "flake" reproduces a third time, treat it as a real failure and either fix it or STOP.

### 4.5f: Safety Caps

- **CI fix attempts per PR: 5** (matches the review-loop cap). If beast mode pushes 5 rounds of CI fixes and still can't get green, STOP and report.
- **Combined cap (review + CI):** if the combined number of "fix and retry" rounds (review fixes + CI fixes) on a single PR exceeds **8**, STOP, and recommend escalating to a Fable session; repeated non-convergence usually means the plan or architecture needs rework, not more patches.
- **Hard wall-clock cap per PR: 4 hours** from PR open to merge. If the PR can't be merged within 4 hours, STOP and report. (Most PRs will finish in under 60 minutes; this is a guardrail against silent infinite loops.)

### 4.5g: Re-trigger Review if Code Changed Significantly

If fixing CI required non-trivial code changes (more than a small typo / config tweak), the previously-clean review is now stale. After CI goes green, **run one more pass of Step 4 (Review Loop)** on the new commits before proceeding to merge. This catches the case where a CI fix introduces its own quality regression.

"Non-trivial" rule of thumb: more than 20 lines changed, OR new logic added, OR new public API touched. A typo fix or config bump doesn't require re-review.

---

## Step 5: Merge

### PR mode

1. **Approve the PR** (self-approve is fine for solo workflows):
   ```bash
   gh pr review <PR#> --approve --body "Beast mode review loop converged clean."
   ```
   Note: GitHub may block self-approval depending on repo settings. If so, skip approval and proceed to merge if the user has admin/maintainer rights, or stop and report.

2. **Merge:**
   ```bash
   gh pr merge <PR#> --merge --delete-branch
   ```
   **Default policy: preserve full history.** Always use a true merge commit (`--merge`, i.e. `--no-ff`). Never squash. Never rebase. Never fast-forward. The per-step commits made during implementation and the review-fix commits are valuable history and must survive into main.

   **Override only if the repo explicitly says so.** If the repo's `CLAUDE.md`, `CONTRIBUTING.md`, or branch protection settings require a different style (squash-only, rebase-only, etc.), honor that. Otherwise, full merge commit always.

   Announce: `✅ PR merged: #<num>`

3. **Sync local main:**
   ```bash
   git checkout main
   git pull --ff-only
   git branch -d feature/<plan-name>  # local cleanup (should already be gone if --delete-branch worked)
   ```
   Announce: `✅ Branch deleted: feature/<plan-name>`

### Local mode

1. **Merge locally:**
   ```bash
   git checkout main
   git merge --no-ff feature/<plan-name> -m "Merge feature/<plan-name>"
   git branch -d feature/<plan-name>
   ```
   **Default policy: preserve full history.** Always use `--no-ff` to create a real merge commit. Never squash. Never rebase. Never fast-forward.

   **Override only if the repo explicitly says so.** If the repo's `CLAUDE.md` or `CONTRIBUTING.md` mandates a different style, honor that. Otherwise, full merge commit always.

2. No push.

   Announce: `✅ Merged locally: feature/<plan-name>` and `✅ Branch deleted: feature/<plan-name>`

---

## Step 6: Update Roadmap & Loop

1. **Update `docs/plans/development-roadmap.md`:**
   - Move the just-finished item from "Next Immediate Step" to "Completed"
   - Promote the next "Upcoming" item to "Next Immediate Step"

2. **Commit the roadmap update on main:**
   ```bash
   git add docs/plans/development-roadmap.md
   git commit -m "Complete: <feature-name>"
   git push   # PR mode only
   ```
   Announce: `✅ Roadmap updated — next up: <name or "(none)">`

3. **Loop back to Step 1.** Pick the next item and start a new feature branch.

---

## Step 7: Wrap Up

Reached when:
- The next roadmap item is not yolo-able, OR
- The roadmap has no more "Upcoming" items, OR
- A safety rule fired and stopped the loop, OR
- The review loop hit the 5-pass cap on some feature, OR
- A phase gate returned findings (the fix list is in the gate report), OR
- A phase gate could not run at Fable tier.

Output a final report:

```
## Beast Mode Complete

Mode: <PR | Local>
Features shipped: <N>
  - <feature-1> (PR #123, merged)
  - <feature-2> (PR #124, merged)
  - ...

Stopped because: <reason>

Roadmap state:
  Next Immediate Step: <name> (<reason it wasn't auto-handled>)
  Upcoming: <count> items

Review activity:
  Total review passes: <N>
  Features that needed >1 review pass: <list>
  Fable security passes run: <N or 0>

Phase gates:
  Gates processed: <N> (<phase name>: <verdict>, ...)
  Pending gate: <none | "<phase name>" - run /phasegate in a Fable session>

Anything skipped or deferred:
  - <item> (<why>)

Next move suggestion:
  <e.g., "Run /plan on <item> to make it yolo-able" or "Manual review needed on <item>">
```

---

## Error Handling

**On any unrecoverable failure during the outer loop:**
1. Stop immediately
2. Leave the current branch in a consistent state (last good commit)
3. Do NOT attempt cleanup that could lose work (no `git reset --hard`, no force pushes, no branch deletes)
4. Print: what feature was in progress, what step failed, what was completed before the failure, and what the user should check
5. Suggest how to resume (usually: fix the issue, then re-run `/beastmode`; beast mode will pick up from the roadmap's current state)

**If the review subagent returns malformed output:**
- Retry once with a clarification appended to the prompt
- If still malformed, treat as NEEDS_CHANGES with a single finding ("review subagent output unparseable, manual review required") and STOP

**If the user interrupts mid-run:**
- The last commit is the safe resume point
- Beast mode is idempotent at the roadmap level: re-running it will pick up wherever the roadmap says we are
