Execute the "booyah" workflow for step-by-step plan execution.

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

**If there ARE uncommitted changes:**
- This means the previous `/booyah` session completed work that needs committing
- Proceed to Step 3 (Update Plan) and Step 4 (Commit)

**If there are NO uncommitted changes (clean working tree):**
- Skip directly to Step 5 (Identify Next Step)
- The plan's checkboxes already reflect completed work

## Step 3: Update the Plan (only if uncommitted changes exist)

Mark the just-completed step as done:
- Change `- [ ]` to `- [x]` for completed items
- If there are sub-items, mark those complete too

## Step 4: Commit Changes (only if uncommitted changes exist)

Commit all staged and unstaged changes WITHOUT asking permission:
1. Run `git status` and `git diff` to see what changed
2. Stage all changes with `git add -A`
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
