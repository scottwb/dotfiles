Create a detailed implementation plan for a new feature or task.

Arguments: $ARGUMENTS (optional - feature name)

## Step 1: Understand the Feature

**If no feature name was provided in arguments:**
Ask the user: "What feature or task would you like to plan?"

Once you have the feature name:
1. Restate your understanding of what the feature is
2. Ask if you've understood correctly

## Step 2: Research and Explore

1. Search the codebase to understand:
   - Existing patterns this feature should follow
   - Files that will likely be affected
   - Similar implementations to use as reference

2. Read `docs/plans/development-roadmap.md` to understand the current roadmap

3. Check if a plan already exists in `docs/plans/` for this feature:
   - If it exists, tell the user and ask if they want to refine it or start fresh

## Step 3: Ask Clarifying Questions

Ask questions to clarify:
- Specific requirements and constraints
- Edge cases to consider
- Integration points with existing code
- Any preferences on implementation approach

Don't assume - ask until you understand.

## Step 4: Write the Plan Document

Create a plan at `docs/plans/<feature-name>.md` with this structure:

```markdown
# Plan: <Feature Name>

## Execution Instructions

When executing this plan:

1. **Work step-by-step** - Complete each step fully before moving to the next
2. **Test after each step** - Run the test commands listed to verify the change works
3. **Commit after each step** - Use the provided commit message for each step
4. **Update documentation continuously** - After ANY change that affects them, update:
   - `README.md` - User-facing documentation
   - `CLAUDE.md` - Developer/AI guidelines
   - `run` script usage comments
   - `docs/plans/<feature-name>.md` - Mark progress, update status
   - `docs/plans/development-roadmap.md` - Mark progress, update status
5. **Mark completion** - When all steps are done, move this item from "Next Immediate Step" to "Completed" in the roadmap

---

## Summary

<Brief description of what this feature does>

## Requirements

- <Bullet list of requirements>

## Implementation Steps

### Step 1: <Step Title>

- [ ] <Specific change 1>
- [ ] <Specific change 2>

**File(s):** `path/to/file.rb`

**Test:**
```bash
<commands to test this step>
```

**Commit message:** `<descriptive commit message>`

---

### Step 2: <Next Step Title>
...

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `file1.rb` | 1, 3 |
| `file2.rb` | 2 |
```

**Key principles for steps:**
- Each step is the **smallest change that is still working, testable, and functional**
- Each step can be **committed independently**
- Each step includes **test commands** to verify it works
- Each step includes a **commit message**
- **Sub-items use checkboxes** (`- [ ]`) so `/booyah` can track progress

## Step 5: Update the Roadmap

Add the new plan to `docs/plans/development-roadmap.md`:
1. Move current "Next Immediate Step" to "Upcoming" section
2. Add this plan as the new "Next Immediate Step" with link to plan file
3. Set status to "Planning"

## Step 6: Iterate with User

Show the user the plan and ask:
> Does this plan look good? Let me know if you'd like to refine any steps or add more detail.

Keep iterating until the user says the plan is good.

## Step 7: Commit the Plan

When the user approves:
1. Update the roadmap status to "Ready to implement"
2. Commit both files with message: `Add plan: <feature-name>`
3. Tell the user: "Plan committed! To start implementing, run `/booyah <feature-name>` in a new session."
