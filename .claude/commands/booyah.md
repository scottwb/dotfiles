Execute a plan step-by-step on the current branch; re-running /booyah = approve the previous step, commit it, and implement the next (stops for your testing between steps).

Arguments: $ARGUMENTS (optional - search term to find a plan file)

## Permission Model

**Running `/booyah` IS the permission signal.** When the user runs this command, they are saying:
- "I have tested the previous work (if any) and it's good"
- "You have permission to commit without asking"
- "Proceed to the next step autonomously"

Do NOT ask for confirmation before committing. Do NOT ask "are you ready?" - just do it.

## Step 1: Identify the Active Plan

**If a plan is already active in this conversation:**
- Continue with that plan (skip to Step 3)

**If no plan is active yet:**

1. Search for plan files in `docs/plans/` and `.claude/plans/`
   - Look for files ending in `.md` that contain implementation steps
   - Exclude `development-roadmap.md` (that's the roadmap, not a plan)

2. If `$ARGUMENTS` is provided:
   - Find plan files whose name or content matches the search term
   - If exactly one match, show it and ask to confirm
   - If multiple matches, list them and ask which one

3. If no arguments provided:
   - Check `docs/plans/development-roadmap.md` for "Next Immediate Step" and find its linked plan
   - If no linked plan, list available plans and ask which one

4. Once confirmed, this becomes the active plan for the session

## Step 2: Check for Uncommitted Work

Run `git status` to check if there are uncommitted changes.

**If there are NO uncommitted changes (clean working tree):**
- Skip directly to Step 5 (Identify Next Step)
- The plan's checkboxes already reflect completed work

**If there ARE uncommitted changes, first ask: is this work mine?**

The default assumption is that uncommitted work is the previous `/booyah` step
finishing, because that is what it usually is. That assumption is only safe once
this command has actually been running.

- **Second and later invocation in this session** (you already implemented a step
  in this conversation): the work IS yours. Proceed to Step 3 and Step 4 without
  asking. This is the common path and it stays frictionless.

- **First invocation in this session** (no active plan yet, fresh conversation, or
  you have not implemented anything here): do NOT assume. The tree may hold work
  that has nothing to do with this plan. Show it and ask:

  ```
  The working tree was already dirty before I started:

    <git status --short output>

  Is this the step to commit, or unrelated work I should leave alone?
  ```

  Wait for the answer. If the user says it is unrelated: do not commit it, do not
  stage it, and skip to Step 5 to implement the next step. Leave those files
  untouched for the rest of the run.

**Why this exists:** committing under a message that describes something else is
hard to notice and annoying to unpick. This actually happened on 2026-07-29, when
a tree holding six unrelated concerns plus a deliberately held feature branch's
worth of work would have been swept into one commit. Running `/booyah` is
permission to commit YOUR work, not everything present.

## Step 3: Update the Plan (only if uncommitted changes exist)

Mark the just-completed step as done:
- Change `- [ ]` to `- [x]` for completed items
- If there are sub-items, mark those complete too

## Step 4: Commit Changes (only if uncommitted changes exist)

Commit the step's work WITHOUT asking permission:
1. Run `git status` and `git diff` to see what changed
2. Stage it:
   - **Default:** `git add -A`. Correct when everything dirty is this step's work,
     which is the normal case once you have been running.
   - **If Step 2 established that some of the tree is unrelated:** stage the step's
     files explicitly by path instead, and leave the rest alone. Confirm before
     committing:
     ```bash
     git diff --cached --name-only     # must list ONLY this step's files
     ```
3. Write a clear, descriptive commit message that:
   - Summarizes what was done (not just "completed step X")
   - Follows the repo's commit conventions if any
   - Does NOT include any Claude attribution or co-author tags
4. Commit the changes immediately
5. Briefly announce: "Committed: <summary of what was committed>"

## Step 5: Identify Next Step

Read the plan and find the next uncompleted step (first `- [ ]` item).

If no uncompleted steps remain:
1. Update `docs/plans/development-roadmap.md`:
   - Move the completed item from "Next Immediate Step" to a "Completed" section (create if needed)
   - Promote the next "Upcoming" item to "Next Immediate Step"
2. Commit the roadmap update with message: `Complete: <feature-name>`
3. Announce: "🎉 **Booyah!** All steps complete! Roadmap updated."
4. **Phase gate check:** if the newly promoted "Next Immediate Step" is a `PHASE GATE: <phase name>` marker, ask the user: "Phase complete. Run the phase gate now?" On yes, spawn the audit as a fresh-context subagent via the Agent tool with `model: "fable"`, instructing it to follow `~/.claude/commands/phasegate.md` for that phase; relay its verdict, report path, and fix list. If the fable model override is unavailable, tell the user to run `/phasegate` in a Fable session instead; never run the gate on a lesser model. (The human is present in booyah, so ask rather than auto-fire.)

## Step 6: Execute Next Step

Implement the next step from the plan. Do the work - write code, make edits, etc.

## Step 6b: Update Documentation

After implementing each step, check if any of these need updating and update them:
- `README.md` - If user-facing behavior or commands changed
- `CLAUDE.md` - If developer guidelines, patterns, or conventions changed
- `run` script - If command usage or help text needs updating
- `docs/plans/development-roadmap.md` - Update progress/status if appropriate

This is not optional - documentation must stay in sync with code changes.

## Step 7: STOP - Wait for User Testing

**CRITICAL: Do NOT commit yet.** The work is done but needs user verification.

Provide a clear testing summary:

1. **What changed:** Brief list of files/functionality modified
2. **How to test:** Specific commands to run and expected results
3. **Ready signal:** "Run `/booyah` when testing passes."

Then STOP. Do not proceed until the user runs `/booyah` again.

When they do, the cycle repeats: commit → next step → implement → stop for testing.
